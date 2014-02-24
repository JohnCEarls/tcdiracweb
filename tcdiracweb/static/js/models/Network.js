define(['underscore', 'backbone'], function(_, Backbone){
    var Network = Backbone.Model.extend({
        defaults : {
            'name': '',
            'source':'',
            'information_uri':'',
            'geneIds':[]
        },
        idAttribute: 'name'
    });
    var NetworkCollection = Backbone.Collection.extend({
        model: Network,
        url: 

    });
    return {Model : Network, Collection: NetworkCollection};
});
