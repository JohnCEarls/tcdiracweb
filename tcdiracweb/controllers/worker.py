import masterdirac.models.worker as wkr
import masterdirac.models.master as mstr
import masterdirac.models.systemdefaults as sys_def_mdl
import boto.sqs
from boto.sqs.message import Message
import json
from tcdiracweb.utils.common import json_prep
import random
import string

class Worker:
    """
    Read only worker object
    """
    def __init__( self, app, worker_id=None):
        self.app = app
        self.worker_id = worker_id

    def GET( self, request):
        if self.worker_id is None:
            #return active workers
            workers = wkr.get_active_workers()
            workers = [json_prep( worker ) for worker in workers]
            if workers:
                msg = {
                        'status' : 'complete',
                        'data' : workers
                      }
                status = 200
            else:
                msg = {
                        'status' : 'error',
                        'data' : [],
                        'message': 'No workers available'
                        }
                status = 404
        else:
            result = wkr.get_ANWorker( worker_id=self.worker_id )
            if result:
                msg = {'status' : 'complete',
                        'data' : json_prep( result )
                        }
                status = 200
            else:
                msg = {'status': 'error',
                        'data' : {'worker_id' : self.worker_id},
                        'message' : 'Worker not found'
                        }
                status = 404
        return ( msg, status )

    def POST( self, request, action):
        req_d = self._req_to_dict( request )
        if action == 'init':
            return self._init_worker( req_d )
        elif action == 'active':
            return self._activate_worker( req_d )
        elif action == 'activate-server':
            return self._activate_server( req_d )
        elif action == 'stop-server':
            return self._stop_server( req_d )
        elif action == 'status-server':
            return self._status_server( req_d )
        elif action == 'terminate':
            return self._terminate_worker( req_d )
        else:
            msg = {'status': 'error',
                    'data' : req_d,
                    'message': 'Unknown action [%s]' % action}
            status = 404
            return (msg, status)

    def _init_worker( self, req_d):
        msg = {'status': 'error',
                'data' : '',
                'message': 'Unable to initialize worker'}
        status = 404
        result = None
        if( req_d['master_name'] and req_d['master_name'] != "None"):
            result = wkr.get_ANWorkerBase( req_d['cluster_type'], req_d['aws_region'] )
        if result:
            new_worker_settings = {
                    'master_name': req_d['master_name'],
                    'cluster_type': result['cluster_type'],
                    'aws_region' : result['aws_region'],
                    'cluster_name' : self._gen_name( req_d['master_name'],
                        result['prefix'] ),
                    'num_nodes': 0,
                    'status':wkr.CONFIG,
            }
            starcluster_config = {
                    'cluster_name': new_worker_settings['cluster_name'],
                    'spot_bid': result['spot_bid'],
                    'key_name' : 'SET BY MASTER',
                    'key_location': 'SET BY MASTER',
                    'iam_profile': result['iam_profile'],
                    'force_spot_master': result['force_spot_master'],
                    'cluster_size': result['cluster_size'],
                    'plugins': result['plugins'],
                    'node_instance_type': result['instance_type'],
                    'node_image_id': result['image_id'],
                    'aws_region': result['aws_region']
                    }
            new_worker = None
            try:
                new_worker = wkr.insert_ANWorker(starcluster_config=starcluster_config,
                    **new_worker_settings)
            except Exception as e:
                self.app.logger.error("Attempted to create [%r] [%r]" % (
                    new_worker_settings, starcluster_config ))
                self.app.logger.error("Received exception [%r]" % (e))
                pass
            if new_worker:
                msg = {'status' : 'complete',
                        'data' : json_prep( new_worker )}
                status=200
        return (msg, status)

    def _activate_worker( self, req_d ):
        """
        Generate message for launcher in queue to request that
        the master starts the cluster
        """
        launcher_message = {'action': 'activate',
                            'worker_id': self.worker_id,
                }
        launcher_config = sys_def_mdl.get_system_defaults(
                setting_name = 'launcher_config', component='Master' )
        conn = boto.sqs.connect_to_region('us-east-1')
        lq = conn.create_queue( launcher_config['launcher_sqs_in'] )
        mess = Message(body=json.dumps( launcher_message ))
        lq.write( mess )
        msg = {'status': 'complete',
                'data': launcher_message }
        status = 200
        return ( msg, status )

    def _activate_server( self, req_d ):
        """
        Generate message for launcher in queue to request that
        the master starts the cluster
        """
        launcher_message = {'action': 'activate-server',
                            'worker_id': self.worker_id,
                }
        launcher_config = sys_def_mdl.get_system_defaults(
                setting_name = 'launcher_config', component='Master' )
        conn = boto.sqs.connect_to_region('us-east-1')
        lq = conn.create_queue( launcher_config['launcher_sqs_in'] )
        mess = Message(body=json.dumps( launcher_message ))
        lq.write( mess )
        msg = {'status': 'complete',
                'data': launcher_message }
        status = 200
        return ( msg, status )

    def _stop_server( self, req_d ):
        """
        Generate message for launcher in queue to request that
        the master starts the cluster
        """
        launcher_message = {'action': 'stop-server',
                            'worker_id': self.worker_id,
                }
        launcher_config = sys_def_mdl.get_system_defaults(
                setting_name = 'launcher_config', component='Master' )
        conn = boto.sqs.connect_to_region('us-east-1')
        lq = conn.create_queue( launcher_config['launcher_sqs_in'] )
        mess = Message(body=json.dumps( launcher_message ))
        lq.write( mess )
        msg = {'status': 'complete',
                'data': launcher_message }
        status = 200
        return ( msg, status )

    def _status_server( self, req_d ):
        """
        Generate message for launcher in queue to request that
        the master starts the cluster
        """
        launcher_message = {'action': 'status-server',
                            'worker_id': self.worker_id,
                }
        launcher_config = sys_def_mdl.get_system_defaults(
                setting_name = 'launcher_config', component='Master' )
        conn = boto.sqs.connect_to_region('us-east-1')
        lq = conn.create_queue( launcher_config['launcher_sqs_in'] )
        mess = Message(body=json.dumps( launcher_message ))
        lq.write( mess )
        msg = {'status': 'complete',
                'data': launcher_message }
        status = 200
        return ( msg, status )

    def _activate_server( self, req_d ):
        """
        Generate message for launcher in queue to request that
        the master starts the cluster
        """
        launcher_message = {'action': 'activate-server',
                            'worker_id': self.worker_id,
                }
        launcher_config = sys_def_mdl.get_system_defaults(
                setting_name = 'launcher_config', component='Master' )
        conn = boto.sqs.connect_to_region('us-east-1')
        lq = conn.create_queue( launcher_config['launcher_sqs_in'] )
        mess = Message(body=json.dumps( launcher_message ))
        lq.write( mess )
        msg = {'status': 'complete',
                'data': launcher_message }
        status = 200
        return ( msg, status )

    def _terminate_worker( self, req_d ):
        #check if 
        worker = wkr.get_ANWorker( worker_id=self.worker_id )
        self.app.logger.info("%r" % worker )
        if worker['status'] in [wkr.CONFIG, wkr.NA]:
            worker = wkr.update_ANWorker( self.worker_id, 
                        status=wkr.TERMINATED)
            msg = {'status':'complete',
                    'data' : json_prep( worker )}
            status = 200
        elif wkr.confirm_worker_running( worker ):
            #we have an active cluster
            master = mstr.get_active_master()
            if master:
                launcher_message = {'action':'terminate',
                                    'worker_id': self.worker_id}
                launcher_config = sys_def_mdl.get_system_defaults(
                        setting_name = 'launcher_config', component='Master' )
                conn = boto.sqs.connect_to_region('us-east-1')
                lq = conn.create_queue( launcher_config['launcher_sqs_in'] )
                worker = wkr.update_ANWorker( self.worker_id, 
                        status=wkr.MARKED_FOR_TERMINATION)
                mess = Message(body=json.dumps( launcher_message ))
                lq.write( mess )
                msg = {'status':'complete',
                        'data' : json_prep( worker ) }
                status = 200
            else:
                msg = {'status': 'error',
                        'data' : {'worker_id': self.worker_id},
                        'message' : 'Running Cluster without an active master'
                        }
                status = 409 #Conflict
        else:
            worker = wkr.update_ANWorker( self.worker_id, 
                        status=wkr.TERMINATED_WITH_ERROR)
            msg = {'status':'complete',
                    'data' : json_prep( worker )}
            status = 200
        return (msg, status)

    def _gen_name( self, master_name,  prefix ):
        N = 5
        seed = string.ascii_uppercase * N + string.digits * N
        random_post = ''.join(random.sample( seed, N ))
        #extremely unlikely to have a collision, but possible, sigh ...
        while wkr.get_ANWorker( master_name=master_name, cluster_name=prefix+random_post ):
            random_post = ''.join(random.sample( seed, N ))
        return prefix + random_post

    def _req_to_dict( self, request):
        """
        Takes a Request object(form or json) and returns a dictionary
        """
        req_d = request.get_json(silent=True)
        if not req_d:
            req_d = request.form.to_dict()
        for key, value in req_d.iteritems():
            try:
                #if datetime convert to string
                req_d[key] = value.isoformat()
            except AttributeError as ae:
                pass
            try:
                req_d[key] = value.strip()
            except AttributeError as ae:
                pass
        return req_d
