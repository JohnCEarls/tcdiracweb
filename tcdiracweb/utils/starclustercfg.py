import starcluster
import boto
import boto.ec2
from boto.s3.key import Key
import os, os.path
from datetime import datetime
import ConfigParser
from pynamodb.models import Model
from pynamodb.attributes import (UnicodeAttribute, UTCDateTimeAttribute,
        NumberAttribute, UnicodeSetAttribute, JSONAttribute)
from pynamodb.exceptions import DoesNotExist
import StringIO
from flask import render_template
from tcdiracweb import app
import sys
import select
import boto.sqs
from boto.sqs.message import Message
import json
import multiprocessing
import subprocess 
from collections import defaultdict
class SCConfigError(Exception):
    pass

class ANMaster(Model):
    table_name = 'aurea-nebula-master'
    master_name = UnicodeAttribute( hash_key=True )
    date_created = UTCDateTimeAttribute( range_key=True, default=datetime.utcnow() )
    aws_region = UnicodeAttribute()
    key_pairs = JSONAttribute(default={})
    key_location = UnicodeAttribute()

class ANWorkerConfig(Model):
    table_name='aurea-nebula-worker'
    master_name = UnicodeAttribute( hash_key=True )
    cluster_name = UnicodeAttribute( range_key=True )
    cluster_type = UnicodeAttribute(default='data')
    node_type = UnicodeAttribute(default='m1.xlarge')
    aws_region = UnicodeAttribute(default='')
    num_nodes = NumberAttribute(default=0)
    nodes = UnicodeSetAttribute(default=[])
    state = NumberAttribute(default=0)
    config = UnicodeAttribute(default='')
    startup_log = UnicodeAttribute(default='')
    startup_pid = UnicodeAttribute(default='')


class ANMasterServer:
    def __init__(self, key_location='/home/sgeadmin'):
        md = boto.utils.get_instance_metadata()
        name = md['instance-id']

        aws_region = md['placement']['availability-zone'][:-1]
        if not ANMaster.exists():
            ANMaster.create_table( read_capacity_units=2, write_capacity_units=1, wait=True)
        items = [item for item in ANMaster.scan( master_name__eq=name) if item.aws_region == aws_region]
        if items:
            self._model = max( items, key=lambda x: x.date_created)
        else:
            #creating new ams
            self._model = ANMaster( name )
            self._model.aws_region = md['placement']['availability-zone'][:-1]
            self._model.key_location = key_location
            self._model.save()

    @property
    def aws_region( self ):
        return self._model.aws_region

    @property
    def master_name(self):
        return self._model.master_name

    @property
    def unstarted_data_clusters(self):
        clusters = ANWorkerConfig.scan(master_name__eq=self.master_name)
        return [ANDataServer( self.master_name, cluster.cluster_name )
                for cluster in clusters if cluster.active == 0 and
                cluster.cluster_type=='data']

    @property
    def unstarted_gpu_clusters(self):
        clusters = ANWorkerConfig.scan(master_name__eq=self.master_name)
        return [ANGPUServer( self.master_name, cluster.cluster_name )
                for cluster in clusters if cluster.active == 0 and
                cluster.cluster_type=='gpu']

    def get_key( self, aws_region):
        self._model.refresh()
        if aws_region not in self._model.key_pairs:
            key_location ,new_key = self._gen_key( aws_region )
            kp = self._model.key_pairs
            kp[aws_region] = new_key
            self._model.key_pairs = kp
            self._model.key_location = key_location
            self._model.save()
        return self._model.key_pairs[aws_region]

    def _gen_key(self, aws_region='us-east-1', key_location= '/home/sgeadmin' ):
        ec2 = boto.ec2.connect_to_region( aws_region )
        key_name = 'sc-key-%s-%s' % (self._model.master_name, aws_region )
        k_file = '.'.join( [ key_name, 'pem' ])

        if os.path.isfile(os.path.join(key_location,k_file )) and \
                ec2.get_key_pair( key_name ):
            #we have a key and key_pair
            return key_name
        elif os.path.isfile(os.path.join(key_location, k_file )):
            #we have a key and no key pair
            os.remove( os.path.join(key_location, k_file) )
        elif ec2.get_key_pair( key_name ):
            #we have a key_pair, but no key
            ec2.delete_key_pair( key_name )
        key = ec2.create_key_pair( key_name )
        key.save( key_location )
        os.chmod( os.path.join( key_location, k_file ), 0600 )
        return (key_location , key_name)

    def _aws_info_config( self,config, aws_region):
        md = boto.utils.get_instance_metadata()
        config.add_section('aws info')
        sc = md['iam']['security-credentials']['gpu-data-instance']
        #aws info
        config.set('aws info', 'aws_access_key_id','IGNORE')
        config.set('aws info', 'aws_secret_access_key', 'IGNORE')

        config.set('aws info', 'AWS_CONFIG_TABLE', 'sc_config')
        config.set('aws info', 'AWS_META_BUCKET','ndprice-aws-meta')
        config.set('aws info', 'AWS_SPOT_TABLE', 'spot_history')
        config.set('aws info', 'AWS_REGION_NAME', aws_region)
        return config

    def _key_config( self, config, aws_region):
        key = self.get_key(region)
        key_location = self._model.key_location
        config.add_section( 'key %s' % key )
        config.set('key %s' % key, 'key_location', os.path.join( key_location, '%s.pem' % key) )
        return config


    def _data_cluster_config( self, config,
            cluster_prefix='gpu-data',
            aws_region='us-east-1',
            cluster_size=10,
            cluster_shell='bash',
            node_image_id='ami-0773776e',
            node_instance_type='m1.xlarge',
            iam_profile='gpu-data-instance',
            dns_prefix=True,
            disable_queue=True,
            spot_bid='.50',
            permissions = [],
            availability_zone=None,
            plugins= ['base-tgr', 'gpu-data-tgr', 'user-bootstrap', 'data-bootstrap'],
            cluster_user='sgeadmin',
            force_spot_master=True):
        return self._cluster_config( config,cluster_prefix,region, cluster_size,
                cluster_shell, node_image_id, node_instance_type, iam_profile,
                dns_prefix, disable_queue, spot_bid, permissions,
                availability_zone, plugins, cluster_user, force_spot_master)

    def _gpu_cluster_config( self,  config,
            cluster_prefix='gpu-server',
            aws_region='us-east-1',
            cluster_size=1,
            cluster_shell='bash',
            node_image_id='ami-4f5c6126',
            node_instance_type='cg1.4xlarge',
            iam_profile='gpu-data-instance',
            dns_prefix=True,
            disable_queue=True,
            spot_bid='2.00',
            permissions = [],
            availability_zone=None,
            plugins= ['base-tgr', 'gpu-server-tgr', 'user-bootstrap', 'gpu-bootstrap'],
            cluster_user='sgeadmin',
            force_spot_master=True):
        return self._cluster_config( config,cluster_prefix,region, cluster_size,
                cluster_shell, node_image_id, node_instance_type, iam_profile,
                dns_prefix, disable_queue, spot_bid, permissions,
                availability_zone, plugins, cluster_user, force_spot_master)

    def _cluster_config( self, config,
            cluster_prefix='gpu-data',
            aws_region='us-east-1',
            cluster_size=10,
            cluster_shell='bash',
            node_image_id='ami-9b0924f2',
            node_instance_type='m1.xlarge',
            iam_profile='gpu-data-instance',
            dns_prefix=True,
            disable_queue=True,
            spot_bid='.50',
            permissions = [],
            availability_zone=None,
            plugins= ['base-tgr', 'gpu-data-tgr', 'user-bootstrap', 'data-bootstrap'],
            cluster_user='sgeadmin',
            force_spot_master=True
            ):
        self._model.refresh()
        ctr = 0
        cluster_name = '%s-%i' % ( cluster_prefix, ctr)
        existing_clusters =[item.cluster_name for item in
                ANWorkerConfig.query( self._model.master_name,
                    cluster_name__begins_with=cluster_prefix)]

        while cluster_name in existing_clusters:
            ctr += 1
            cluster_name = '%s-%i' % ( cluster_prefix, ctr)
        s = 'cluster %s' % cluster_name
        config.add_section(s)
        config.set(s, 'keyname', self.get_key(region) )
        config.set(s, 'cluster_size', cluster_size)
        config.set(s, 'cluster_user', cluster_user)
        config.set(s, 'cluster_shell', cluster_shell)
        config.set(s, 'spot_bid', spot_bid)
        config.set(s, 'iam_profile', iam_profile)
        config.set(s, 'node_instance_type', node_instance_type)
        config.set(s, 'node_image_id', node_image_id)
        if plugins:
            config.set(s, 'plugins', ', '.join( plugins ))
        if availability_zone:
            config.set(s, 'availability_zone', availability_zone)
        if disable_queue:
            config.set(s, 'disable_queue', 'True')
        if dns_prefix:
            config.set(s, 'dns_prefix', 'True')
        if permissions:
            config.set(s, 'permissions', ', '.permissions )
        if force_spot_master:
            config.set(s, 'force_spot_master', 'True')
        return (cluster_name, config)

    def configure_data_cluster( self, **kwargs):
        if kwargs is None:
            kwargs = {}
        if 'region' not in kwargs:
            aws_region = self.aws_region
        else:
            aws_region = kwargs['region']
        if 'cluster_prefix' not in kwargs:
            cluster_prefix = 'gpu-data'
        else:
            cluster_prefix = kwargs['cluster_prefix']
        config = ConfigParser.RawConfigParser()
        config = self._aws_info_config( config, aws_region )
        config = self._key_config( config , aws_region)
        kwargs['config'] = config
        kwargs['cluster_prefix'] = cluster_prefix
        kwargs['region'] = aws_region
        cluster_name, config = self._data_cluster_config( **kwargs )
        stringIO = StringIO.StringIO()
        config.write( stringIO )
        config_str = stringIO.getvalue()
        ads = ANDataServer( self._model.master_name, cluster_name, aws_region )
        ads.set_config( config_str )
        ads.set_num_nodes( config.getint( 'cluster %s' % cluster_name, 'cluster_size') )
        return cluster_name

    def configure_gpu_cluster( self, **kwargs):
        if kwargs is None:
            kwargs = {}
        if 'region' not in kwargs:
            aws_region = self.aws_region
        else:
            aws_region = kwargs['region']
        if 'cluster_prefix' not in kwargs:
            cluster_prefix = 'gpu-server'
        else:
            cluster_prefix = kwargs['cluster_prefix']
        config = ConfigParser.RawConfigParser()
        config = self._aws_info_config( config, aws_region )
        config = self._key_config( config , aws_region)
        kwargs['config'] = config
        kwargs['cluster_prefix'] = cluster_prefix
        kwargs['region'] = aws_region
        cluster_name, config = self. _gpu_cluster_config( **kwargs )
        stringIO = StringIO.StringIO()
        config.write( stringIO )
        
        config_str = stringIO.getvalue()
        ads = ANGPUServer( self._model.master_name, cluster_name, aws_region )
        ads.set_config( config_str )
        ads.set_num_nodes( config.getint( 'cluster %s' % cluster_name, 'cluster_size') )
        return cluster_name

class ANServer:
    def __init__(self, master_name, cluster_name, aws_region=None, no_create=False):
        if not ANWorkerConfig.exists():
            ANWorkerConfig.create_table( read_capacity_units=2, write_capacity_units=1, wait=True)
        try:
            sc_config = ANWorkerConfig.get( master_name, cluster_name )
        except:
            sc_config = None
        if sc_config:
            self._model = sc_config
        elif no_create:
            raise SCConfigError("%s, %s does not exist" % (master_name, cluster_name))
        else:
            self._model = self._create_model( master_name, cluster_name, aws_region )
        self.log_bucket = 'ndp-adversary'

    def _create_model(self, master_name, cluster_name, aws_region):
        sc_model = ANWorkerConfig( master_name, cluster_name )
        sc_model.aws_region = aws_region
        sc_model.cluster_type='data'
        sc_model.save()
        return sc_model

    def set_config( self, config):
        self._model.refresh()
        self._model.config = config
        self._model.save()

    def set_active(self):
        self._model.refresh()
        self._model.active = 1
        self._model.save()

    @property
    def active(self):
        self._model.refresh()
        return self._model.active == 1

    @property
    def config(self):
        self._model.refresh()
        return str(self._model.config)

    def start_cluster(self):
        self._model.refresh()

    @property
    def startup_log(self):
        self._model.refresh()
        s3 = boto.connect_s3()
        b = s3.get_bucket(self.log_bucket)
        k =  b.get_key(self._model.startup_log)
        if k:
            return k.get_contents_as_string()
        else:
            return ''

    def set_startup_log(self, log):
        s3_name = 'logs/sc_startup/%s/%s.log' %(self._model.master_name, 
                self._model.cluster_name )
        self._model.startup_log = s3_name
        #note:race conditions possible
        s3 = boto.connect_s3()
        b = s3.get_bucket(self.log_bucket)
        k = Key(b)
        k.key = s3_name
        k.set_contents_from_string( log )
        self._model.save()


    @property
    def startup_pid(self):
        self._model.refresh()
        return self._model.startup_pid

    def set_startup_pid(self, startup_pid):
        self._model.refresh()
        self._model.startup_pid = str(startup_pid)
        self._model.save()

    @property
    def ready(self):
        self._model.refresh()
        return self._model.ready

    def set_ready(self):
        self._model.refresh()
        self._model.ready = 1
        self._model.save()

    @property
    def num_nodes(self):
        self._model.refresh()
        return self._model.num_nodes

    def set_num_nodes(self, num_nodes):
        self._model.refresh()
        self._model.num_nodes = num_nodes
        self._model.save()



class ANDataServer(ANServer):
    def _create_model(self, master_name, cluster_name, aws_region):
        sc_model = ANWorkerConfig( master_name, cluster_name )
        sc_model.aws_region = aws_region
        sc_model.cluster_type='data'
        sc_model.node_type='m1.xlarge'
        sc_model.save()
        return sc_model

class ANGPUServer(ANServer):
    def _create_model(self, master_name, cluster_name, aws_region):
        sc_model = ANWorkerConfig( master_name, cluster_name )
        sc_model.aws_region = aws_region
        sc_model.cluster_type='gpu'
        sc_model.node_type='cg1.4xlarge'
        sc_model.save()
        return sc_model


def run_sc( starcluster_bin, url, master_name,cluster_name ):
    adv_ser = ANServer(master_name, cluster_name, no_create=True)
    pid = multiprocessing.current_process()
    base_message = {'cluster_name': cluster_name, 'master_name': master_name, 'pid':str(pid) }
        
    sqs =boto.sqs.connect_to_region("us-east-1")
    q = sqs.create_queue('starcluster-results')
    if adv_ser.active:
        base_message['type'] = 'system'
        base_message['msg'] = 'Error: already active'
        q.write( Message(body=json.dumps(message)) )
        return

    sc_command = "%s -c %s/%s/%s start -c %s %s" %( os.path.expanduser(starcluster_bin), url,master_name, cluster_name, cluster_name, cluster_name)
    base_message['command'] = sc_command
    sc_p = subprocess.Popen( sc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
    adv_ser.set_active()
    adv_ser.set_startup_pid(str(sc_p.pid))
    log_subprocess_messages( sc_p, q, base_message)
    adv_ser.set_ready()
    """
    stdout = []
    stderr = []
    errors = False
    ctr = 0
    while True:
        ctr += 1
        reads = [sc_p.stdout.fileno(), sc_p.stderr.fileno()]
        ret = select.select(reads, [], [])
        for fd in ret[0]:
            base_message['time'] = datetime.now().isoformat()
            base_message['count'] = ctr
            if fd == sc_p.stdout.fileno():
                read = sc_p.stdout.readline()
                base_message['type'] ='stdout'
                base_message['time'] = datetime.now().isoformat()
                base_message['msg'] = read.strip()
                q.write(Message(body=json.dumps(base_message)))
            if fd == sc_p.stderr.fileno():
                read = sc_p.stderr.readline()
                base_message['type'] ='stderr'
                base_message['msg'] = read.strip()
                q.write(Message(body=json.dumps(base_message)))
        if sc_p.poll() != None:
            base_message['type'] = 'system'
            base_message['msg'] = 'Complete'
            if errors:
                base_message['msg'] += ':Errors exist'

            q.write(Message(body=json.dumps(base_message)))
            break"""

def gpu_logserver_daemon(starcluster_bin, url, master_name, cluster_name, action='start'):
    valid_actions = ['start', 'stop', 'status']
    assert action in valid_actions, "%s is not a valid action for gpu" % action
    base_message = {'cluster_name': cluster_name, 'master_name': master_name, 
            'action': action, 'component': 'gpu-logserver-daemon' }
    sqs =boto.sqs.connect_to_region("us-east-1")
    q = sqs.create_queue('starcluster-results')
    sc_command = "%s -c %s/%s/%s sshmaster -u sgeadmin %s " %( os.path.expanduser(starcluster_bin), url,master_name, cluster_name, cluster_name)
    if action == 'start':
        sc_command += "'bash /home/sgeadmin/GPUDirac/scripts/logserver.sh start'"
    if action == 'status':
        sc_command += "'bash /home/sgeadmin/GPUDirac/scripts/logserver.sh status'" 
    if action == 'stop':
        sc_command += "'bash /home/sgeadmin/GPUDirac/scripts/logserver.sh stop'"
    base_message['command'] = sc_command
    sc_p = subprocess.Popen( sc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
    log_subprocess_messages( sc_p, q, base_message)

def gpu_daemon( starcluster_bin, url, master_name, cluster_name, gpu_id=0, action='start'):
    valid_actions = ['start', 'stop', 'status']
    assert action in valid_actions, "%s is not a valid action for gpu" % action

    base_message = {'cluster_name': cluster_name, 'master_name': master_name, 
            'gpu_id':str(gpu_id), 'action':action, 'component':'gpuserver-daemon' }
        
    sqs =boto.sqs.connect_to_region("us-east-1")
    q = sqs.create_queue('starcluster-results')
    sc_command = "%s -c %s/%s/%s sshmaster -u sgeadmin %s " %( os.path.expanduser(starcluster_bin), url,master_name, cluster_name, cluster_name)
    if action == 'start':
        sc_command += "'bash /home/sgeadmin/GPUDirac/scripts/gpuserver%i.sh start'" % gpu_id
    if action == 'status':
        sc_command += "'bash /home/sgeadmin/GPUDirac/scripts/gpuserver%i.sh status'" % gpu_id
    if action == 'stop':
        sc_command += "'bash /home/sgeadmin/GPUDirac/scripts/gpuserver%i.sh stop'" % gpu_id
    base_message['command'] = sc_command
    sc_p = subprocess.Popen( sc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
    log_subprocess_messages( sc_p, q, base_message)

def cluster_restart( starcluster_bin, url, master_name, cluster_name):
    base_message = {'cluster_name': cluster_name, 'master_name': master_name, 
            'component':'restart'} 
    sqs =boto.sqs.connect_to_region("us-east-1")
    q = sqs.create_queue('starcluster-results')
    sc_command = "%s -c %s/%s/%s restart %s " %( os.path.expanduser(starcluster_bin), url,master_name, cluster_name, cluster_name)
    base_message['command'] = sc_command
    sc_p = subprocess.Popen( sc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
    log_subprocess_messages( sc_p, q, base_message)

def cluster_terminate( starcluster_bin, url, master_name, cluster_name):
    base_message = {'cluster_name': cluster_name, 'master_name': master_name, 
            'component':'restart'} 
    sqs =boto.sqs.connect_to_region("us-east-1")
    q = sqs.create_queue('starcluster-results')
    sc_command = "%s -c %s/%s/%s terminate -f -c %s " %( os.path.expanduser(starcluster_bin), url,master_name, cluster_name, cluster_name)
    base_message['command'] = sc_command
    sc_p = subprocess.Popen( sc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
    log_subprocess_messages( sc_p, q, base_message)


def log_subprocess_messages( sc_p, q, base_message):
    stdout = []
    stderr = []
    errors = False
    ctr = 0
    while True:
        ctr += 1
        reads = [sc_p.stdout.fileno(), sc_p.stderr.fileno()]
        ret = select.select(reads, [], [])
        for fd in ret[0]:
            base_message['time'] = datetime.now().isoformat()
            base_message['count'] = ctr
            if fd == sc_p.stdout.fileno():
                read = sc_p.stdout.readline()
                base_message['type'] ='stdout'
                base_message['time'] = datetime.now().isoformat()
                base_message['msg'] = read.strip()
                q.write(Message(body=json.dumps(base_message)))
            if fd == sc_p.stderr.fileno():
                read = sc_p.stderr.readline()
                base_message['type'] ='stderr'
                base_message['msg'] = read.strip()
                q.write(Message(body=json.dumps(base_message)))
        if sc_p.poll() != None:
            #process exitted
            ctr += 1
            base_message['time'] = datetime.now().isoformat()
            base_message['count'] = ctr
            base_message['type'] = 'system'
            base_message['msg'] = 'Complete'
            if errors:
                base_message['msg'] += ':Errors exist'
            q.write(Message(body=json.dumps(base_message)))
            break

def log_sc_startup( ):
    sqs =boto.sqs.connect_to_region("us-east-1")
    q = sqs.create_queue('starcluster-results')
    msg = q.read(120)
    msg_comb = defaultdict(list)
    err = ''
    clusters = set()
    while msg:
        mymsg = json.loads(msg.get_body())
        q.delete_message( msg )
        mymsg_key = mymsg['cluster_name'] + '-' + mymsg['master_name']
        msg_comb[mymsg_key].append(mymsg)
        msg = q.read(120)
    for key, msg_list in msg_comb.iteritems():
        first = msg_list[0]
        msg_list.sort(key=lambda x: x['count'])
        clusters.add( first['cluster_name'] )
        adv_ser = ANServer(first['master_name'], first['cluster_name'], no_create=True)
        log = adv_ser.startup_log 
        for msg in msg_list:
            if 'time' not in msg:
                msg['time'] = datetime.now().isoformat()
            if msg['type'] == 'stdout':
                log += '[%s] %s\n' % (msg['time'], msg['msg'])
            if False and msg['type'] == 'stderr':
                if msg['msg'][:3] == '>>>':
                    log += msg['msg'] + '\n'
            if msg['type'] == 'system':
                if msg['msg'][:8] == 'Complete':
                    log += '=' * 60 + '\n'
                    log += '[%s] %s\n' % (msg['time'], msg['msg'])
                    adv_ser.set_ready()
        adv_ser.set_startup_log( log )

    return list(clusters) 

if __name__ == "__main__":
    if not ANMaster.exists():
        ANMaster.create_table( read_capacity_units=2, write_capacity_units=1, wait=True)
    if not ANWorkerConfig.exists():
        ANWorkerConfig.create_table( read_capacity_units=2, write_capacity_units=1, wait=True)
    print log_sc_startup()
    exit()
    ams = ANMasterServer()
    #print ams.get_key('us-east-1')
    print ams.configure_data_cluster()
    print ams.configure_gpu_cluster()
    ds = ams.unstarted_data_clusters
    for ads in ds:
        print ads.config


    ds = ams.unstarted_gpu_clusters
    for ads in ds:
        print ads.config

