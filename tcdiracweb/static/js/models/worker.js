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
            '-5': 'Terminated with error',
            '0':'Configured',
            '10': 'Starting',
            '20':'Ready',
            '30': 'Running',
            '31': 'Cluster Error',
            '35': 'Marked for termination',
            '37': 'Terminating',
            '40':'Terminated'}
        return status_map[ this.get('status').toString() ];
    },

    activate : function(){
        var url = '';
        if( this.get('status') === 0 ){
            var url = '/cm/activate/worker/' + this.get('worker_id');
        } else {
            alert(this.str_status + " is inconsistent with a launch state");
            return;
        }

        var msg = { 'todo': 'add security features'}
        that = this;
        $.post( url )
            .done( function(data, textStatus, jqXHR){
                setTimeout( function(){
                    that.fetch();
                }, 3000);
               })
            .fail( function( jqXHR, textStatus, errorThrown ) {
                alert("Error on startup " + textStatus);
            });

    },
    start : function(){
        var url = '';
        if( this.get('status') === 20 ){
            var url = '/cm/activate/server/' + this.get('worker_id');
        } else {
            alert(this.str_status + " is inconsistent with a launch state");
            return;
        }

        that = this;
        var msg = { 'todo': 'add security features'}
        $.post( url )
            .done( function(data, textStatus, jqXHR){
                setTimeout( function(){
                    that.fetch();
                }, 10000);
               })
            .fail( function( jqXHR, textStatus, errorThrown ) {
            });
    },
    stop : function(){
        var url = '';
        if( this.get('status') === 30 ){
            var url = '/cm/stop/server/' + this.get('worker_id');
        } else {
            alert(this.str_status + " is inconsistent with a launch state");
            return;
        }
        that = this;

        var msg = { 'todo': 'add security features'}
        $.post( url )
            .done( function(data, textStatus, jqXHR){
                setTimeout( function(){
                    that.fetch();
                }, 10000);
               })
            .fail( function( jqXHR, textStatus, errorThrown ) {
            });
    },

    restart : function(){
        alert('Unimplemented');
    },

    status_refresh : function(){
        var url = '';
        if( this.get('status') === 30 || this.get('status') === 20  ){
            var url = '/cm/status/server/' + this.get('worker_id');
        } else {
            alert(this.str_status + " is inconsistent with a launch state");
            return;
        }
        that = this;

        var msg = { 'todo': 'add security features'}
        $.post( url )
            .done( function(data, textStatus, jqXHR){
                setTimeout( function(){
                    that.fetch();
                }, 10000);
               })
            .fail( function( jqXHR, textStatus, errorThrown ) {
            });
    },

    terminate : function(){
        var url = '/cm/terminate/worker/' + this.get('worker_id');
        var msg = { 'todo': 'add security features'}
        that = this;
        $.post( url )
            .done( function(data, textStatus, jqXHR){
                that.set( data.data );
                //that.trigger('change');
                console.log( 'done.' );
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
        console.log('Worker Model terminate')
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
