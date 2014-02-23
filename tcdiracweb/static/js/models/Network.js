var Network = Backbone.Model.extend({
    defaults : {
        'name': '',
        'source':'',
        'information_uri':''
        'geneIds':[]
    },
    idAttribute: 'name'
});
