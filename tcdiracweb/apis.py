from flask import Blueprint, Response, make_response, jsonify,abort
from flask import current_app
import json
from tcdiracweb.utils.app_init import crossdomain, secure_page
from pynamodb.exceptions import DoesNotExist

api = Blueprint('api', __name__, template_folder = 'templates', static_folder = 'static')

@api.errorhandler(404)
def not_found(error):
    current_app.logger.error("%r" % error)
    return make_response(jsonify( { 'error': 'Not found' } ), 404)
   
@api.route('/network', methods=['GET'])
@api.route('/network/<name>', methods=['GET'])
@crossdomain(origin='http://localhost:8000')
def network(name=None):
    from dbModels.Networks import Network
    from dbModels.utils import item_to_dict
    import json
    result = {}
    if name is None:
        result = []
        current_app.logger.debug("API: get all networks")
        for network in Network.scan():
            result.append(item_to_dict( network ))
    else:
        try:
            
            current_app.logger.debug("API: get networks[%s]" % name)
            result = item_to_dict( Network.get( name ) )
        except DoesNotExist:
            abort(404)
    current_app.logger.debug('network: %r' % result)
    current_app.logger.debug('network as json' %  json.dumps( result ))
    return Response( json.dumps( result ), mimetype='application/json')

@api.route('/cluster', methods=['GET'])
@api.route('/cluster/<cluster_name>', methods=['GET'])
def cluster_get( cluster_name = None ):
    from tcdiracweb.utils.starclustercfg import StarclusterConfig
    import boto.utils
    instance_id = boto.utils.get_instance_identity()['document']['instanceId']
    if cluster_name:
        try:
            res = StarclusterConfig.get( instance_id, cluster_name )
            return jsonify( res.attribute_values )
        except DoesNotExist:
            abort(404)
    else:
        res = StarclusterConfig.scan(master_name__eq = instance_id )
        if res:
            return Response( json.dumps([r.attribute_values for r in res]), 
                    mimetype = 'application/json')

@api.route( '/awscred', methods=['GET'])
def google_id():
    try:
        cred = {'RoleArn':'arn:aws:iam::686625824462:role/aurea-nebula-google-web-role',
                'WebIdentityToken': session['id_token']
        }
        return Response(
            json.dumps(cred),
            mimetype='application/json')
    except:
        abort(404) 
