var DefaultWorker = Backbone.Model.extend({
    defaults : {'cluster_type': 'None',
                'aws_region': 'None'},
    url : function( ){
        return this.urlRoot + '/' +
        this.get('cluster_type') + '/' + this.get('aws_region');
    },
    urlRoot: '/cm/workerdefault',
    get_id : function(){
        return this.get('cluster_type') + '-' + this.get('aws_region');
    },

});

var DefaultWorkerCollection = Backbone.Collection.extend({
    model: DefaultWorker,
    url : '/cm/workerdefault'

});

