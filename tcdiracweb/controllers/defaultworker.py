import masterdirac.models.worker as wkr
class DefaultWorker:
    def __init__(self, app, cluster_type, aws_region):
        self.app = app
        self.cluster_type = cluster_type
        self.aws_region = aws_region

    def GET( self, request):
        """
        Read
        The request is only used if region is not given in constructor
        If cluster_type and aws_region are given, returns a single record
        otherwise a list.
        May return an empty list
        """
        self.app.logger.info("GET")
        result = None
        if self.aws_region is None and 'aws_region' in request.args:
            self.aws_region = request.args['aws_region']
        result = wkr.get_ANWorkerBase( self.cluster_type, self.aws_region )
        if result:
            status = 200
        else:
            status = 404
        msg = {'status':'complete',
                'data': result }
        return (msg, status)

    def POST( self, request):
        """
        Insert/update
        """
        self.app.logger.info("POST")
        req_d = self._req_to_dict( request )
        if(self.cluster_type == 'None'):
            self.app.logger.info( req_d )
            self.app.logger.error( "Got a none")
            status = 404
            msg = { 'status': 'error',
                    'message': 'Received a None',
                    'data': req_d }
            return ( msg, status )
        #create/update'
        if self.cluster_type is None or self.aws_region is None:
            #missing information
            msg =  {'status': 'error',
                    'message': 'Invalid URI for insert/update',
                    'data': {
                              'cluster_type': str(self.cluster_type),
                              'aws_region': str(self.aws_region)
                            } 
                    }
            return ( msg, 400 )
        result_clean = self._clean_result( req_d )
        wkr.insert_ANWorkerBase( self.cluster_type, self.aws_region, **result_clean )
        result = wkr.get_ANWorkerBase( self.cluster_type, self.aws_region )
        msg = {'status': 'complete',
                'data' : result }
        return ( msg, 200 )

    def DELETE( self ):
        """
        Delete given cluster_type and aws_region
        """
        self.app.logger.info("DELETE")
        try:
            wkr.delete_ANWorkerBase( self.cluster_type, self.aws_region )
            msg = {'status':'complete',
                    'data' : {'cluster_type': self.cluster_type,
                              'aws_region': self.aws_region }
                    }
            return ( msg, 200 )
        except wkr.ANWorkerBase.DoesNotExist as dne:
            msg =  {'status': 'error',
                    'data' : {'cluster_type': self.cluster_type,
                              'aws_region': self.aws_region },
                    'message': 'Element not found'}
            return ( msg, 404 )

    def _req_to_dict( self, request):
        """
        Takes a Request object and returns a dictionary
        """
        req_d = request.get_json(silent=True)
        if not req_d:
            req_d = request.form.to_dict()
        for key, value in req_d.iteritems():
            try:
                req_d[key] = value.strip()
            except AttributeError as ae:
                pass
        return req_d

    def _clean_result( self, req_d):
        """
        Remove extraneous variables, coerce types
        """
        if 'cluster_type' in req_d:
            self.cluster_type = req_d['cluster_type']
        if 'aws_region' in req_d:
            self.aws_region = req_d['aws_region']
        valid_fields = ['instance_type', 'image_id', 'cluster_size', 'plugins', 
                'force_spot_master', 'spot_bid', 'iam_profile', 'prefix']
        #remove extraneous variables
        result_clean = dict([(key,value) for key, value in req_d.iteritems()
            if key in valid_fields])
        #coerce to proper data types
        if 'spot_bid' in result_clean:
            result_clean['spot_bid'] = float( result_clean['spot_bid'] )
        if 'cluster_size' in result_clean:
            result_clean['cluster_size'] = int( result_clean['cluster_size'] )
        if 'force_spot_master' in result_clean:
            result_clean['force_spot_master'] = \
                result_clean['force_spot_master'] in ['True','true','1', True] 
        return result_clean


