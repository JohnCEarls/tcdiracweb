define(['underscore', 'backbone'], function(_, Backbone){
    if(window.location.hostname == 'localhost'){
        var baseUrl = 'https://price.adversary.us/';
    }else{
        var baseUrl = 'api/';
    }
    var Network = Backbone.Model.extend({
        type:'Network',
        defaults : {
            'name': '',
            'source':'',
            'information_uri':'',
            'geneIDs':[]
        },
        urlRoot: 'api/network',
        idAttribute: 'name'
    });
    var NetworkCollection = Backbone.Collection.extend({
        type: 'NetworkCollection',
        model: Network,
        url: baseUrl + 'api/network'
    });
    return {Model : Network, Collection: NetworkCollection};
});
