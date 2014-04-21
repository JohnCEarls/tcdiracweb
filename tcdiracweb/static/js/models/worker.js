var Worker = Backbone.Model.extend({
    idAttribute : 'worker_id',
    urlRoot : '/cm/active/worker',
    parse : function( response ){
        console.log( response );
        if( response.data ){
            return response.data;
        }
        return response;
    },

    str_status : function(){
        var status_map = {
            '-10':'NA',
            '0':'Configured',
            '10': 'Starting',
            '20':'Ready',
            '30': 'Running',
            '40':'Terminated'}
        return status_map[ this.get('status').toString() ];
    },


});

var WorkerCollection = Backbone.Collection.extend({
    model: Worker,
    url : '/cm/active/worker',
    parse : function( response ){
        console.log( response );
        if( response.data ){
            console.log("In response.data");
            console.log( response.data );
            return response.data;
        }
        return response;
    },
});
