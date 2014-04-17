import masterdirac.models.run as run

class Run:
    def __init__(self, app, run_id=None):
        self.app = app
        self.run_id = run_id

    def GET( self ):
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
        self.app.logger.info("Run.POST()")
        req = self._req_to_dict( request )
        self.app.logger.debug( "request %r" % req )
        #make no distinction between insert and update
        self.app.logger.info("Update %s" % self.run_id )
        req.pop('run_id', None)#remove run_id from dict, using one in const.
        result = run.insert_ANRun( self.run_id, **req )
        result = self._clean_response( result )
        msg = {'status': 'complete',
                'data': result }
        return (msg, 200)

    def DELETE( self ):
        self.app.logger.info("DELETE")
        try:
            run.delete_ANRun( self.run_id )

            msg = {'status':'complete',
                    'data' : {'run_id': run_id }
                    }
            return ( msg, 200 )
        except run.ANRun.DoesNotExist as dne:
            msg =  {'status': 'error',
                    'data' : {'run_id': run_id },
                    'message': 'Element not found'}
            return ( msg, 404 )

    def _clean_response(self, resp ):
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
        Takes a Request object and returns a dictionary
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
