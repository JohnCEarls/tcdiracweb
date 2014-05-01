var Master = Backbone.Model.extend({
    defaults:{  'master_name': 'None',
                'date_created':'',
                'aws_region': '',
                'key_pairs':{},//ex: {'us-east-1':'ue1-key_name'}
                'instance_id':'',
                'comm_queue':'',
                'status':-10
    },
    url: '/cm/master',

    parse : function ( response ){
        console.log( response );
        if( response.data ){
            return response.data;
        }
    },

    str_status : function(){
        var status_map = { 
            '-10' : 'NA',
            '0' : 'Initialized',
            '10' : 'Managing Run',
            '30' : 'Terminated'
        };

        return status_map[this.get('status').toString()];
    },

});
