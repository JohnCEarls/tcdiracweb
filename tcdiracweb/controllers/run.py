import masterdirac.models.run as run
import boto

import masterdirac.models.systemdefaults as sys_def_mdl
import boto.sqs
from boto.sqs.message import Message
import json

class Run:
    """
    CRUD class for managing data runs
    """
    def __init__(self, app, run_id=None):
        self.app = app
        self.run_id = run_id

    def GET( self ):
        """
        Returns a single run
        """
        self.app.logger.info("Run.GET(%r)" % self.run_id)
        result = run.get_ANRun( self.run_id )
        self.app.logger.info("%r" % result)
        result = self._clean_response( result )
        if result:
            status = 200
        else:
            status = 404
        msg = {'status':'complete',
                'data': result }
        return (msg, status)


    def POST( self, request):
        """
        Insert/update run
        """
        self.app.logger.info("PendingRun.POST()")
        req = self._req_to_dict( request )
        self.app.logger.debug( "request %r" % req )
        #make no distinction between insert and update
        self.app.logger.info("Update %s" % self.run_id )
        req.pop('run_id', None)#remove run_id from dict, using one in const.
        req.pop('date_created', None) #created is non-writeable
        req.pop('status') #status unwriteable from web
        result = run.insert_ANRun( self.run_id, **req )
        result = self._clean_response( result )
        msg = {'status': 'complete',
                'data': result }
        return (msg, 200)

    def DELETE( self ):
        """
        Delete a run
        """
        self.app.logger.info("DELETE")
        try:
            run.delete_ANRun( self.run_id )

            msg = {'status':'complete',
                    'data' : {'run_id': self.run_id }
                    }
            return ( msg, 200 )
        except run.ANRun.DoesNotExist as dne:
            msg =  {'status': 'error',
                    'data' : {'run_id': run_id },
                    'message': 'Element not found'}
            return ( msg, 404 )

    def _clean_response(self, resp ):
        """
        Converts variables to jsonable format
        """
        if type(resp) is dict:
            for key, value in resp.iteritems():
                try:
                    #if datetime convert to string
                    resp[key] = value.isoformat()
                except AttributeError as ae:
                    pass
            return resp
        elif type(resp) is list:
            return [self._clean_response( item ) for item in resp]
        else:
            return resp

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

class PendingRun(Run):
    """
    Class for interacting with pending runs (runs in configure state)
    Read only
    """
    def __init__(self, app, run_id=None):
        Run.__init__(self, app, run_id)

    def GET( self, request):
        self.app.logger.info("PendingRun.GET(%r)" % self.run_id)
        result = run.get_pending_run()
        result = self._clean_response( result )
        if result:
            status = 200
        else:
            status = 404
        msg = {'status':'complete',
                'data': result }
        return (msg, status)

    def POST( self, request):
        self.app.logger.info("Pending run %r" % request )
        req_d = self._req_to_dict( request )
        return self._activate_run( req_d )

    def _activate_run( self, req_d ):
        """
        Generate message for launcher in queue to request that
        the master starts the cluster
        """
        launcher_message = {'action': 'activate-run',
                            'run_id': self.run_id,
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

    def DELETE( self ):
        raise Exception("Cannot delete PendingRun Object")

class ActiveRun(Run):
    def __init__(self, app, run_id=None):
        Run.__init__(self, app, run_id)

    def GET( self, request):
        self.app.logger.info("ActiveRun.GET(%r)" % self.run_id)
        master_id = None
        if 'master_id' in request.args:
            master_id = request.args['master_id']
        result = run.get_active_ANRun(run_id= self.run_id, master_id=master_id  )
        self.app.logger.info("%r" % result)
        result = self._clean_response( result )
        if result:
            msg = {'status':'complete',
                'data': result }
            status = 200
        else:
            msg = {
                'status' : 'error',
                'data' : result,
                'message' : 'No Active Runs' }
            status = 404
        return (msg, status)

    def POST( self, request ):
        """
        This is a request to interact with a Run
        it gets passed to the master via sqs
        """
        req_d = self._req_to_dict( request )
        if self.run_id is not None:
            req_d['run_id'] = self.run_id
        import masterdirac.models.systemdefaults as sys_def 
        l_config = sys_def.get_system_defaults( component='Master', 
                setting_name='launcher_config' )
        conn =  boto.sqs.connect_to_region("us-east-1")
        l_q = conn.create_queue( l_config['launcher_sqs_in'] )
        l_q.write( Message(body=json.dumps(req_d)))
        msg = {'status': 'complete',
               'data':req_d}
        status=200
        return ( msg, status )

    def DELETE( self ):
        self.app.logger.error("Attempt to delete active run.")
        raise Exception("Cannot delete an ActiveRun")
