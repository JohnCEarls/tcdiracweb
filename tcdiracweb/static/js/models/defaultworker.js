var DefaultWorker = Backbone.Model.extend({
    defaults : {'cluster_type': 'None',
                'aws_region': 'None',
                'instance_type': 'None',
                'image_id':'None',
                'cluster_size':0,
                'spot_bid':0.0,
                'plugins':'base-tgr',
                'force_spot_master':true
                },
    url : function( ){
        return this.urlRoot + '/' +
        this.get('cluster_type') + '/' + this.get('aws_region');
    },
    urlRoot : '/cm/workerdefault',
    delete : function( successCallback, errorCallback){
        $.ajax( {
            url: this.url(),
            type: 'DELETE',
            success: successCallback || $.noop,
            error: errorCallback || $.noop,
        });
    },
    idAttribute : 'cid',
    parse : function( response ){
        if( response.data){
            return response.data;
        }
        return response;
    }

});

var DefaultWorkerCollection = Backbone.Collection.extend({
    model: DefaultWorker,
    url : '/cm/workerdefault',
    //comparator : 'aws_region',
    comparator : function( a,b ){
        console.log("in comparator");
        
        if( a.get('cluster_type').toLowerCase() 
            > b.get('cluster_type').toLowerCase() ){
            return 1;
        }
        if( a.get('cluster_type').toLowerCase() < 
            b.get('cluster_type').toLowerCase() ){
            return -1;
        }
        if( a.get('cluster_type') === b.get('cluster_type') ){
            if(a.get('aws_region').toLowerCase() > 
                b.get('aws_region').toLowerCase()){
                return 1;
            } else {
                return -1;
            }
        }
        return 0;//all equal, should not happen
    },
    parse : function( response ){
        if( response.data ){
            return response.data;
        }
        return response;
    }

});

