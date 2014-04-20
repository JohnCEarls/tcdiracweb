import masterdirac.models.worker as wkr
from tcdiracweb.utils.common import json_prep

class Worker:
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
