from flask import Blueprint, Response, make_response
from flask import jsonify, abort, current_app
from flask import render_template, flash, request

from tcdiracweb.utils.app_init import crossdomain, secure_page,secure_json, check_id

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

@cm.route('/console/messages', methods=['GET'])
@secure_json
def cluster_manager():
    import tcdiracweb.controllers.messages as m
    console_messages = m.Console( current_app )
    msg, status = console_messages.GET()
    return Response( json.dumps( msg ), mimetype='application/json',
                        status = status )


@cm.route('/master', methods=['GET'])
@secure_json
def get_master():
    """
    API
    Returns currently active master instance
    """
    current_app.logger.info('get_master')
    import masterdirac.models.master as mstr
    import masterdirac.models.systemdefaults as sys_def
    local_settings = sys_def.get_system_defaults('local_settings',
            'Master')
    master = mstr.get_active_master( local_settings['branch'] )
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
@cm.route('/pending/run/<run_id>', methods=['GET', 'POST'])
@secure_json
def get_pending_run( run_id=None ):
    """
    API
    Returns runs that are configured, but not active

    a post requests that master change the run status from config to INIT
    """
    import tcdiracweb.controllers.run as rn
    current_app.logger.info("get_pending_run")
    pr = rn.PendingRun(current_app, run_id )
    if request.method == 'GET':
        msg, status = pr.GET( request )
    elif request.method == 'POST':
        #this is only for activating a run
        #that causes a message to be sent to the master
        current_app.logger.debug('Activating run_id[%s]' % run_id)
        msg, status = pr.POST( request )
    return Response( json.dumps( msg ), mimetype='application/json',
                        status = status )

@cm.route('/active/run', methods=['GET'])
@cm.route('/active/run/<run_id>', methods=['GET', 'POST'])
@secure_json
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
@secure_json
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
@secure_json
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
@secure_json
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
@secure_json
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
@secure_json
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
@secure_json
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
@secure_json
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

@cm.route('/log/worker/<worker_id>', methods=['GET'])
@secure_json
def get_worker_log( worker_id ):
    import tcdiracweb.controllers.worker as wkr
    worker = wkr.WorkerLog( current_app, worker_id )
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
@cm.route('/run/<run_id>', methods=['GET', 'POST','PUT', 'DELETE','PATCH'])
@secure_json
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
    elif request.method == 'PATCH':
        msg, status  = run.PATCH( request )
 
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
@secure_json
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
    """=
        example config 
        {
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
    import masterdirac.models.worker as wrkr

    import masterdirac.models.systemdefaults as sys_def
    local_settings = sys_def.get_system_defaults('local_settings',
            'Master') 
    worker_model = wrkr.get_ANWorker( worker_id = worker_id )
    if worker_model:
        config_settings = worker_model['starcluster_config']
        if local_settings['branch']=='develop':
            def devify( pl ):
                t = ['dev-tgr']
                for plugin in pl.split(','):
                    if plugin.strip() == 'gpu-bootstrap':
                        t.append('gpu-dev-bootstrap')
                    elif plugin.strip() == 'data-bootstrap':
                        t.append('data-dev-bootstrap')
                    else:
                        t.append(plugin)
                return ', '.join(t)
            config_settings['plugins'] = devify( config_settings['plugins'] )
    return Response( render_template('sc-main.cfg', **config_settings) +
        render_template('sc-plugins.cfg') + 
        render_template('sc-security-group.cfg'), mimetype="text/plain" )

