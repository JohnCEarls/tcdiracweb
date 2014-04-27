import masterdirac.models.worker as wkr
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
                        'node_instance_type': result['node_instance_type'],
                        'node_image_id': result['node_image_id'],
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
                else:
                    msg = {'status': 'error',
                            'data' : '',
                            'message': 'Unable to initialize worker'}
                    status = 404
                return msg, status
                            



    def _gen_name( self, master_name,  prefix ):
        N = 5
        seed = string.ascii_uppercase * N + string.digits * N
        random_post = ''.join(random.sample( seed, N ))
        #extremely unlikely to have a collision, but possible, sigh ...
        while wkr.get_ANWorker( master_name=master_name, prefix+random_post ):
            random_post = ''.join(random.sample( seed, N ))



 
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
