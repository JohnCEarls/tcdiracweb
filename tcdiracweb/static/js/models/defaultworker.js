var DefaultWorker = Backbone.Model.extend({
    defaults : {'cluster_type': 'None',
                'aws_region': 'None',
                'instance_type': 'None',
                'image_id':'None',
                'cluster_size':0,
                'spot_bid':0.0,
                'plugins':'None',
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

});

var DefaultWorkerCollection = Backbone.Collection.extend({
    model: DefaultWorker,
    url : '/cm/workerdefault',
    comparator : 'aws_region',
});

