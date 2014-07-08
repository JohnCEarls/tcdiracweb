var Run = Backbone.Model.extend({
    //see masterdirac.models.run
    defaults : {'run_id': '',
                'workers': [],
                'master_name': '',
                'source_data': {
                    'bucket':'',
                    'data_file':'',
                    'meta_file':'',
                    'annotations_file':'',
                    'agilent_file':'',
                    'synonym_file':''
                },
                'dest_data':{
                    'working_bucket' : '',
                    'working_bucket_path' : '',
                    'meta_file' : '',
                    'dataframe_file' : ''
                },
                'description':'',
                'network_config':{
                    'network_table':'',
                    'network_source':''
                },
                'run_settings':{
                    'run_meta_table':'',
                    'run_truth_table':'',
                    'run_id':'',
                    'server_initialization_queue':'',
                    'k':0,
                    'sample_block_size' : 0,
                    'pairs_block_size' : 0,
                    'nets_block_size' : 0,
                    'heartbeat_interval' : 0,
                    'permutations' : 0,
                    'chunksize' :0
                },
                'intercomm_settings':{
                    'sqs_from_data_to_gpu':'',
                    'sqs_from_gpu_to_agg':'',
                    'sqs_from_data_to_agg':'',
                    'sqs_from_data_to_agg_truth':'',
                    's3_from_data_to_gpu':'',
                    's3_from_gpu_to_agg':''
                },
                'aggregator_settings':{},
                'status':0,
                },
    urlRoot : '/cm/run',
    delete : function( successCallback, errorCallback){
        $.ajax( {
            url: this.url(),
            type: 'DELETE',
            success: successCallback || $.noop,
            error: errorCallback || $.noop,
        });
    },
    idAttribute : 'run_id',
    parse : function( response ){
        if( response.data){
            return response.data;
        }
        return response;
    },

    initializeRun : function(){

        var msg = { 'todo': 'add security features'}
        that = this;
        if( this.get('status') == -10){
        $.post( url )
            .done( function(data, textStatus, jqXHR){
                alert('Initialization request sent');
             })
            .fail( function( jqXHR, textStatus, errorThrown ) {
                alert("Error on startup " + textStatus);
            });
        } else {
            alert( 'Invalid status for initialization(' + this.get('status') + ')' );
        }
    },
    str_status : function(){
        var status_map = {
            '-10': 'CONFIG',
            '0': 'INIT',
            '10': 'ACTIVE',
            '15': 'ACTIVE_ALL_SENT',
            '20': 'COMPLETE',
            '30': 'ABORT'
        }
        return status_map[ this.get('status').toString() ];
    },

});

var RunCollection = Backbone.Collection.extend({
    model: Run,
    url : '/cm/run',
    comparator : 'run_id',

    parse : function( response ){
        if( response.data ){
            return response.data;
        }
        return response;
    },
});

var PendingRunCollection = Backbone.Collection.extend({
    model: Run,
    url : '/cm/pending/run',

    parse : function( response ){
        if( response.data ){
             return response.data;
        }
        return response;
    },

});

var ActiveRunCollection = Backbone.Collection.extend({
    model: Run,
    url : '/cm/active/run',

    parse : function( response ){
        if( response.data ){
             return response.data;
        }
        return response;
    },
});
