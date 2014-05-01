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

    activate : function(){
        var url = '/cm/activate/worker/' + this.get('worker_id');
        var msg = { 'todo': 'add security features'}
        $.post( url )
            .done( function(data, textStatus, jqXHR){
                console.log( 'Activate done.' );
                console.log( data );
                console.log( textStatus );
                console.log( jqXHR );
               })
            .fail( function( jqXHR, textStatus, errorThrown ) {
                console.log( 'Activate error' );
                console.log( jqXHR );
                console.log( textStatus );
                console.log( errorThrown );
            })

    },

    terminate : function(){

    }

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
