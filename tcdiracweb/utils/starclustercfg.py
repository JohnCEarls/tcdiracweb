import starcluster
import boto
import boto.ec2
import os, os.path
from datetime import datetime
import ConfigParser
from pynamodb.models import Model
from pynamodb.attributes import (UnicodeAttribute, UTCDateTimeAttribute, 
        NumberAttribute, UnicodeSetAttribute, JSONAttribute)

class AdversaryMaster(Model):
    table_name = 'adversary-master'
    master_name = UnicodeAttribute( hash_key=True )
    date_created = UTCDateTimeAttribute( range_key=True, default=datetime.utcnow() )
    region = UnicodeAttribute()
    data_clusters = UnicodeSetAttribute(default=[])
    gpu_clusters = UnicodeSetAttribute(default=[])
    key_pairs = JSONAttribute(default={})
    key_location = UnicodeAttribute()

class StarclusterConfig(Model):
    table_name='sc-config'
    master_name = UnicodeAttribute( hash_key=True )
    cluster_name = UnicodeAttribute( range_key=True )
    cluster_master_instance = UnicodeAttribute()
    region = UnicodeAttribute()
    key_name = UnicodeAttribute()
    num_nodes = NumberAttribute(default=0)
    nodes = UnicodeSetAttribute()
    active = NumberAttribute(default=0)


class AdversaryMasterServer:
    def __init__(self, key_location='/home/sgeadmin'):
        md = boto.utils.get_instance_metadata()
        name = md['instance-id']
 
        region = md['placement']['availability-zone'][:-1]
        if not AdversaryMaster.exists():
            AdversaryMaster.create_table( read_capacity_units=2, write_capacity_units=1, wait=True)
        items = [item for item in AdversaryMaster.scan( master_name__eq=name) if item.region == region]
        if items:
            self._model = max( items, key=lambda x: x.date_created)
        else:
            #creating new ams
            self._model = AdversaryMaster( name )
            self._model.region = md['placement']['availability-zone'][:-1]
            self._model.key_location = key_location
            self._model.save()

    @property
    def region( self ):
        return self._model.region

    def get_key( self, region):
        self._model.refresh()
        if region not in self._model.key_pairs:
            key_location ,new_key = self._gen_key( region )
            kp = self._model.key_pairs
            kp[region] = new_key 
            self._model.key_pairs = kp
            self._model.key_location = key_location
            self._model.save()
        return self._model.key_pairs[region]

    def _gen_key(self, region='us-east-1', key_location= '/home/sgeadmin' ):
        ec2 = boto.ec2.connect_to_region( region )
        key_name = 'sc-key-%s-%s' % (self._model.master_name, region )
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

    def _aws_info_config( self,config):
        md = boto.utils.get_instance_metadata()
        config.add_section('aws info')
        sc = md['iam']['security-credentials']['gpu-data-instance']
        
        #aws info
        config.set('aws info', 'aws_access_key_id',sc['AccessKeyId'])
        config.set('aws info', 'aws_secret_access_key', sc['SecretAccessKey'])
        config.set('aws info', 'AWS_CONFIG_TABLE', 'sc_config')
        config.set('aws info', 'AWS_META_BUCKET','ndprice-aws-meta')
        config.set('aws info', 'AWS_SPOT_TABLE', 'spot_history')
        return config

    def _key_config( self, config, region):
        key = self.get_key(region)
        key_location = self._model.key_location
        config.add_section( 'key %s' % key )
        config.set('key %s' % key, 'key_location', os.path.join( key_location, '%s.pem' % key) )
        return config

    def _data_cluster_config( self, config, 
            cluster_prefix='gpu-data', 
            region='us-east-1', 
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
        while cluster_name in self._model.data_clusters:
            ctr += 1
            cluster_name = '%s-%i' % ( cluster_prefix, ctr)
        s = 'cluster %s' % cluster_name
        config.add_section(s)
        config.set(s, 'key_name', self.get_key(region) )
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
        return config

    def make_data_cluster( self, data_cluster_prefix='gpu-data', region=None):
        if region is None:
            region = self.region
        config = ConfigParser.RawConfigParser()
        config = self._aws_info_config( config ) 
        config = self._key_config( config , region)
        config = self. _data_cluster_config( config )


        #key info

        with open('tmp.txt','w+') as tmp:
            config.write(tmp)
            tmp.seek(0)
            for line in tmp:
                print line

        os.remove('tmp.txt')





if __name__ == "__main__":
    ams = AdversaryMasterServer()
    print ams.get_key('us-east-1')
    print ams.make_data_cluster()

