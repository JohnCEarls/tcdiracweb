var Run = Backbone.Model.extend({
    //see masterdirac.models.run
    defaults : {'run_id': '',
                'workers': [],
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
    }

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
    }

});

