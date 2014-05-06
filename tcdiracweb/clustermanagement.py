from flask import Blueprint, Response, make_response
from flask import jsonify, abort, current_app
from flask import render_template, flash, request

from tcdiracweb.utils.app_init import crossdomain, secure_page, check_id

from tcdiracweb.utils.common import json_prep

import json
import boto

cm = Blueprint('cm', __name__, template_folder = 'templates', static_folder = 'static')

@cm.route('/console')
@secure_page
def console():
    """
    Main console page.  Displays current run and clusters
    """
    return render_template('clusterconsole.html', app=current_app)

@cm.route('/master', methods=['GET'])
def get_master():
    """
    API
    Returns currently active master instance
    """
    current_app.logger.info('get_master')
    import masterdirac.models.master as mstr
    master = mstr.get_active_master()
    if master is not None:
        msg = {'status' : 'complete',
               'data' : json_prep(master) }
        status = 200
    else:
        msg = {'status' : 'error',
                   'data' : '',
                   'message':'No Active Master'}
        status = 404
    return Response( json.dumps( msg ), mimetype='application/json',
                        status = status )

@cm.route('/pending/run', methods=['GET'])
@cm.route('/pending/run/<run_id>', methods=['GET'])
def get_pending_run( run_id=None ):
    """
    API
    Returns runs that are configured, but not active
    """
    import tcdiracweb.controllers.run as rn
    pr = rn.PendingRun(current_app, run_id )
    msg, status = pr.GET( request )
    return Response( json.dumps( msg ), mimetype='application/json',
                        status = status )

@cm.route('/active/run', methods=['GET'])
@cm.route('/active/run/<run_id>', methods=['GET', 'POST'])
def get_active_run( run_id = None ):
    """
    API
    Returns an active run
    """
    import tcdiracweb.controllers.run as rn
    ar = rn.ActiveRun(current_app, run_id )
    if request.method == 'GET':
        msg, status = ar.GET( request )
    elif request.method == 'POST':
        msg, status = ar.POST( request )
    return Response( json.dumps( msg ), mimetype='application/json',
                        status = status )

@cm.route('/init/worker', methods=['POST'])
def initialize_worker( ):
    """
    REQUEST LIKE:
    {'cluster_type': ...
        'aws_region':...
        'master_name': ...}
    """
    import tcdiracweb.controllers.worker as wkr
    w = wkr.Worker( current_app, None)
    (msg, status) = w.POST( request, 'init')
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )


@cm.route('/activate/worker/<worker_id>', methods=['POST'])
def activate_worker( worker_id ):
    """
    REQUEST IRRELEVANT
    ==================
    should add some security features, but this is fine for now
    """

    import tcdiracweb.controllers.worker as wkr
    w = wkr.Worker( current_app, worker_id)
    (msg, status) = w.POST( request, 'active')
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )

@cm.route('/activate/server/<worker_id>', methods=['POST'])
def activate_server( worker_id ):
    """
    REQUEST IRRELEVANT
    ==================
    should add some security features, but this is fine for now
    """

    import tcdiracweb.controllers.worker as wkr
    w = wkr.Worker( current_app, worker_id)
    (msg, status) = w.POST( request, 'activate-server')
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )

@cm.route('/stop/server/<worker_id>', methods=['POST'])
def stop_server( worker_id ):
    """
    REQUEST IRRELEVANT
    ==================
    should add some security features, but this is fine for now
    """

    import tcdiracweb.controllers.worker as wkr
    w = wkr.Worker( current_app, worker_id)
    (msg, status) = w.POST( request, 'stop-server')
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )

@cm.route('/status/server/<worker_id>', methods=['POST'])
def status_server( worker_id ):
    """
    REQUEST IRRELEVANT
    ==================
    should add some security features, but this is fine for now
    """

    import tcdiracweb.controllers.worker as wkr
    w = wkr.Worker( current_app, worker_id)
    (msg, status) = w.POST( request, 'status-server')
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )

@cm.route('/terminate/worker/<worker_id>', methods=['POST'])
def terminate_worker( worker_id ):
    """
    Terminate a worker cluster if it is running
    Cancel in dbase if not
    """
    import tcdiracweb.controllers.worker as wkr
    w = wkr.Worker( current_app, worker_id)
    (msg, status) = w.POST( request, 'terminate')
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )

@cm.route('/active/worker', methods=['GET'])
@cm.route('/active/worker/<worker_id>', methods=['GET'])
def get_active_worker( worker_id=None ):
    """
    Returns active worker clusters
    """
    import tcdiracweb.controllers.worker as wkr
    current_app.logger.info('get_active_worker')
    worker = wkr.Worker( current_app, worker_id )
    (msg, status) =  worker.GET( request )
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )

@cm.route('/managerun')
@secure_page
def manage_run():
    """
    Manage active and pending runs
    """
    return render_template('run.html', app=current_app)

@cm.route('/run', methods=['GET'])
@cm.route('/run/<run_id>', methods=['GET', 'POST','PUT', 'DELETE'])
@secure_page
def run( run_id=None ):
    """
    API
    Run CRUD
    """
    current_app.logger.info("run API")
    from controllers.run import Run
    run = Run( current_app, run_id)
    if request.method in ['POST','PUT']:
        msg, status  = run.POST( request )
    elif request.method == 'DELETE':
        msg, status = run.DELETE()
    else:
        msg, status = run.GET()
    return Response( json.dumps( msg ), mimetype="application/json",
            status= status )

@cm.route('/managedefaultworker')
@secure_page
def manage_worker_default():
    """
    Web page for inserting/updating default worker cluster
    configurations
    """
    return render_template('defaultworker.html', app=current_app)

@cm.route('/defaultworker', methods=['GET'])
@cm.route('/defaultworker/<cluster_type>', methods=['GET'])
@cm.route('/defaultworker/<cluster_type>/<aws_region>', methods=['POST', 'GET', 'DELETE'])
@secure_page
def worker_default( cluster_type=None, aws_region=None ):
    """
    API
    to getting/setting information about
    the default worker cluster configurations
    """
    current_app.logger.info( "worker_default-\n%r" % request )
    from controllers.defaultworker import DefaultWorker
    dw = DefaultWorker( current_app, cluster_type, aws_region)
    if request.method == 'POST':
        msg, status = dw.POST( request )
    elif request.method == 'DELETE':
        msg, status = dw.DELETE()
    else:
        msg, status = dw.GET(request)
    return Response( json.dumps( msg ), mimetype='application/json',
                        status = status )

@cm.route('/config/<worker_id>')
def config(worker_id):
    import masterdirac.models.worker as wrkr

    worker_model = wrkr.get_ANWorker( worker_id = worker_id )
    if worker_model:
        config_settings = worker_model['starcluster_config']
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

@cm.route('/createcluster', methods=['POST'])
@secure_page
def create_cluster():
    """
    Deprecated
    """
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
    """
    Deprecated
    """
    raise Exception("Deprecated")
    #delete after able to start, restart, etc ...
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
    """
    Deprecated
    """
    raise Exception("Deprecated")
    #delete after able to start, restart, etc ...
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


@cm.route('/createclusterconfig', methods=['POST','GET'])
@secure_page
def scgenerate_config():
    """
    Deprecated
    """
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
    Deprecated
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

@cm.route('/clustermain')
@secure_page
def clustermain():
    """
    Deprecated
    """
    instance_id =  boto.utils.get_instance_identity()['document']['instanceId']
    return render_template('clustermain.html', instance_id=instance_id, app=current_app)
