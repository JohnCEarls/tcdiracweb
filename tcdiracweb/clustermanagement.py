from flask import Blueprint, Response, make_response 
from flask import jsonify, abort, current_app
from flask import render_template, flash, request


from tcdiracweb.utils.app_init import crossdomain, secure_page, check_id

import json
import boto

cm = Blueprint('cm', __name__, template_folder = 'templates', static_folder = 'static')

@cm.route('/clustermain')
@secure_page
def clustermain():
    instance_id =  boto.utils.get_instance_identity()['document']['instanceId']
    return render_template('clustermain.html', instance_id=instance_id, app=current_app)

@cm.route('/createclusterconfig', methods=['POST','GET'])
@secure_page
def scgenerate_config():
    current_app.logger.debug(repr(request))
    try:
        if request.method == 'POST':
            allowed = ['cluster_size', 'cluster_prefix', 'region', 'availability_zone','spot_bid']
            args = {}
            for k, v in request.form.iteritems():
                if k in allowed and v != 'na' and k != 'cluster_type':
                    args[k] = str(v.strip())
            if 'force_spot_master' in request.form and request.form['force_spot_master'] == 'true':
                args['force_spot_master'] = True
            else:
                args['force_spot_master'] = False
            ms = AdversaryMasterServer()
            current_app.logger.debug( str(args) )
            current_app.logger.debug( str(request.form))
            if request.form['cluster_type'] == 'data':
                cluster_name = ms.configure_data_cluster(**args)
            elif request.form['cluster_type'] == 'gpu':
                cluster_name = ms.configure_gpu_cluster(**args)
            message = {'status': 'success',
                    'cluster_name': cluster_name}
            return jsonify(message);
        else:
            message = {'status' : 'error',
                    'error': 'No POST Request found'}
            return jsonify( message )
    except Exception as e:
        current_app.logger.error("%r" % e)
        message = {'status' : 'error',
            'error': 'Server Error'}
        return jsonify( message )

@cm.route('/cluster')
@cm.route('/cluster/<cluster_name>')
@secure_page
def cluster_get( cluster_name = None ):
    #TODO - this needs to be reconciled with the new setup
    """
    from tcdiracweb.utils.starclustercfg import StarclusterConfig
    try:
        instance_id = boto.utils.get_instance_identity()['document']['instanceId']
        if cluster_name:
            res = StarclusterConfig.get( instance_id, cluster_name )
            if res:
                return jsonify( res.attribute_values )
            else:
                abort(400)
        else:
            #return all clusters
            import json
            res = StarclusterConfig.scan(master_name__eq = instance_id )
            if res:
                return Response( json.dumps([r.attribute_values for r in res]), 
                        mimetype='application/json')
            else:
                abort(400)
    except Exception as e:
        current_app.logger.error("%r" % e)
        abort(400)"""


@cm.route('/createcluster', methods=['POST'])
@secure_page
def create_cluster():
    if request.method == 'POST':
        cluster_name = request.form['cluster_name']
        instance_id =  boto.utils.get_instance_identity()['document']['instanceId']
        from utils.starclustercfg import AdversaryServer, SCConfigError
        from utils import starclustercfg
        try:
            ams = AdversaryServer(instance_id, cluster_name, no_create=True )
        except SCConfigError as e:
            current_app.logger.error("Attempt to create unkown cluster: [%r]" % e)
            return jsonify({'status': 'error', 'error': 'Invalid Request'})
        s_bin = '/home/sgeadmin/.local/bin/starcluster'
        url =  'https://price.adversary.us/scconfig'
        master_name = instance_id 
        args = (s_bin, url, master_name, cluster_name)
        p = multiprocessing.Process(target=starclustercfg.run_sc, args=args)
        p.start()
        ams.set_startup_pid(p.pid)
        ams.set_active()
        return jsonify({'status':'success', 'cluster_name': cluster_name})
    else:
        return jsonify({'status': 'error', 'error': 'Invalid Request'})

@cm.route('/gpucluster', methods=['POST'])
@secure_page
def gpu_cluster():
    from tcdiracweb.utils import starclustercfg
    s_bin = '/home/sgeadmin/.local/bin/starcluster'
    url =  'https://price.adversary.us/scconfig'
    
    instance_id =  boto.utils.get_instance_identity()['document']['instanceId']
    master_name = instance_id 
    valid_actions = ['start', 'stop', 'status']
    current_app.logger.error( "%r" % request.form )
    if request.method == 'POST':
        cluster_name = request.form['cluster_name']
        if request.form['component'] == 'logserver-daemon':
            if request.form['action'] in valid_actions:
                args = (s_bin, url, master_name, cluster_name, 
                        request.form['action'])
                p = multiprocessing.Process(
                        target=starclustercfg.gpu_logserver_daemon, 
                        args=args)
                p.start()
            else:
                abort(400)
        elif request.form['component'] == 'gpuserver-daemon':
            gid = int(request.form['gid'])
            if request.form['action'] in valid_actions and gid in (0,1):
                args = (s_bin, url, master_name, cluster_name, gid, request.form['action'])
                p = multiprocessing.Process( target=starclustercfg.gpu_daemon, args=args)
                p.start()
            else:
                abort(400)
        elif request.form['component'] == 'restart':
            args = (s_bin, url, master_name, cluster_name)
            p = multiprocessing.Process( target=starclustercfg.cluster_restart, 
                        args=args)
            p.start()
        elif request.form['component'] == 'terminate':
            args = (s_bin, url, master_name, cluster_name)
            p = multiprocessing.Process( target=starclustercfg.cluster_terminate, 
                        args=args)
            p.start()
        else:
            abort(400)
        return jsonify({'master_name':master_name, 'cluster_name': cluster_name, 'pid':p.pid})
    else:
        abort(400)

@cm.route('/datacluster', methods=['POST'])
@secure_page
def data_cluster():
    from tcdiracweb.utils import starclustercfg
    s_bin = '/home/sgeadmin/.local/bin/starcluster'
    url =  'https://price.adversary.us/scconfig'
    instance_id =  boto.utils.get_instance_identity()['document']['instanceId']
    master_name = instance_id 
    valid_actions = ['start', 'stop', 'status']
    current_app.logger.error( "%r" % request.form )
    if request.method == 'POST':
        cluster_name = request.form['cluster_name']
        if request.form['component'] == 'terminate':
            args = (s_bin, url, master_name, cluster_name)
            p = multiprocessing.Process( target=starclustercfg.cluster_terminate, 
                        args=args)
            p.start()
        elif request.form['component'] == 'restart':
            args = (s_bin, url, master_name, cluster_name)
            p = multiprocessing.Process( target=starclustercfg.cluster_restart, 
                        args=args)
            p.start()
        else:
            abort(400)
        return jsonify({'master_name':master_name, 'cluster_name': cluster_name, 'pid':p.pid})
    else:
        abort(400)

@cm.route('/workerdefault', methods=['GET'])
@cm.route('/workerdefault/<cluster_type>', methods=['GET'])
@cm.route('/workerdefault/<cluster_type>/<aws_region>', methods=['POST', 'GET', 'DELETE'])
def worker_default( cluster_type=None, aws_region=None ):
    import masterdirac.models.worker as wkr
    valid_fields = ['instance_type','image_id',
            'cluster_size', 'plugins', 'force_spot_master', 'spot_bid']
    current_app.logger.info( "%r" % request )
    if request.method == 'POST':
        req_d = request.get_json(silent=True)
        for key, value in req_d.iteritems():
            try:
                req_d[key] = value.strip()
            except AttributeError as ae:
                pass
        if not req_d:
            req_d = request.form.to_dict()
        if 'cluster_type' in req_d:
            cluster_type = req_d['cluster_type']
        if 'aws_region' in req_d:
            aws_region = req_d['aws_region']
        #create/update'
        current_app.logger.info( req_d )
        if cluster_type is None or aws_region is None:
            #missing information
            msg =  {'error': 'Invalid URI for insert/update',
                'cluster_type': str(cluster_type),
                'aws_region': str(aws_region)}
            return Response( json.dumps( msg ), mimetype='application/json', 
                    status=400)
        result_clean = dict([(key,value) for key, value in req_d.iteritems()
            if key in valid_fields])
        if 'spot_bid' in result_clean:
            result_clean['spot_bid'] = float( result_clean['spot_bid'] )
        if 'cluster_size' in result_clean:
            result_clean['cluster_size'] = int( result_clean['cluster_size'] )
        if 'force_spot_master' in result_clean:
            result_clean['force_spot_master'] = \
                    result_clean['force_spot_master'] in ['True','true','1', True] 
        wkr.insert_ANWorkerBase( cluster_type, aws_region, **result_clean )
        result = wkr.get_ANWorkerBase( cluster_type, aws_region )
        return Response( json.dumps( result ),
                mimetype='application/json', status=200)
    elif request.method == 'DELETE':
        try:
            wkr.delete_ANWorkerBase( cluster_type, aws_region )
            return Response( json.dumps(
                {'message':'Deleted %s(%s)' % ( cluster_type, aws_region )} ),
                mimetype='application/json', status=200)
        except wkr.ANWorkerBase.DoesNotExist as dne:
            return Response( json.dumps(
                {
                    'error':'Cannot find element', 
                    'model': req_d,
                }), 
                mimetype='application/json', status=404)
    else:
        result = None
        if aws_region is None and 'aws_region' in request.args:
            aws_region = request.args['aws_region']
        result = wkr.get_ANWorkerBase( cluster_type, aws_region )
        if result:
            status = 200
        else:
            status = 404
        return Response( json.dumps(result),
                mimetype='application/json', status=status)

@cm.route('/manageworkerdefault')
def manage_worker_default():
    return render_template('workerdefault.html', app=current_app)

@cm.route('/scconfig/<master_name>/<cluster_name>')
def scget_config(master_name, cluster_name):
    from utils.starclustercfg import AdversaryServer, SCConfigError
    try:
        ams = AdversaryServer(master_name, cluster_name, no_create=True )
        return ams.config + render_template('sc-plugins.cfg') + \
            render_template('sc-security-group.cfg')
    except SCConfigError as scce:
        return  jsonify({'error': scce.message})

@cm.route('/sclogupdate', methods=['POST'])
def sc_log_update():
    from tcdiracweb.utils import starclustercfg
    runs = starclustercfg.log_sc_startup()
    if runs:
        return jsonify({'status': 'updates', 'clusters': runs})
    else:
        return jsonify({'status': 'unchanged'})

@cm.route('/config/<master_name>/<cluster_name>')
def config(master_name, cluster_name):
    from masterdirac.models.worker import ANWorker
    item = ANWorker.get(master_name, cluster_name) 
    if item:
        config_settings = item['starcluster_config']
        """= {
        'cluster_name':'dummy-cluster',
        'aws_region':'us-east-1',
        'key_name': 'somekey',
        'key_location': '/home/sgeadmin/somekey.key',
        'cluster_size': 1,
        'node_instance_type': 'm1.xlarge',
        'node_image_id': 'ami-1234567',
        'iam_profile':'some-profile',
        'force_spot_master':True,
        'spot_bid':2.00,
        'plugins':'p1,p2,p3'
    }"""
    return render_template('sc-main.cfg', **config_settings) +\
        render_template('sc-plugins.cfg') + \
        render_template('sc-security-group.cfg')
