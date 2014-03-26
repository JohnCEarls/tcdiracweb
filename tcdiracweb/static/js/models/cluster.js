
var ClustersModel = Backbone.Collection.extend({
  model: ClusterModel,
  url: '/cm/cluster'
});

var ClusterModel = Backbone.Model.extend({
  defaults : {'log':'None', 
    'active':0,
    'ready':0,
    '_launching':false,
    '_autofetch' : false,
    'display_state': 'default'
    },
  urlRoot:'/cm/cluster',
  idAttribute: "cluster_name",
  initialize : function(){
    this._getLog();
    //don't want all clusters firing at same time
    //so inject a little anarchy
    setInterval( this.autofetch(this), (40 + 30*Math.random())*1000 );
    if( this.get('active') && !this.get('ready') ){
      this.set('_launching', true);
    } else {
      this.set('_launching', false);
    }

    this.bind("change:ready", function(){
        
        if(this.get('ready') == 1){
            this.set('_launching', false);
        }
    });
  },

  launchable : function(){
    return this.get('active') == 0 && !this.get('_launching');
    },
   restartable : function(){
    return this.get('ready') == 1;
   },
   terminatable : function(){
     return this.get('active') == 1;
   },

   startable : function(){
     return this.get('active') == 1;
   },
   startloggable : function(){
     return this.get('active') == 1;
   },
   startgpuable : function(gpu_id){
     return this.get('active') == 1;
   },

   launch : function(){
      if(this.launchable()){
         this.set('display_state', 'warning');
         this.set('_launching', true);
         var c_launch = $.post('/createcluster', 
                 {cluster_name: this.get('cluster_name')});
         var that = this;
         c_launch.done( function( response ){
            if (response['status'] == 'error'){
                show_message('Error', 'Error launching ' +
                  that.get('cluster_name') + '.');
                } else {
                show_message('Info', 'Launching ' +
                   that.get('cluster_name') + '.');
                }
            });
        setTimeout( function(){update_status(); }, 5000);      
       }
   },


  autofetch : function(that){
    if (that.get('_launching')){
      console.log( 'Autofetching ' + that.get('cluster_name'));
      that.refresh();
    }
  },

  terminate :function(){
      if (this.terminatable()){
         if( this.isGPU() ){
              var t_url =  '/cm/gpucluster';
         } else {
              var t_url =  '/cm/datacluster';
         }
         var c_term = $.post(t_url, 
                 {cluster_name: this.get('cluster_name'),
                 component:'terminate'
                 });
         var that = this;
         c_term.done( function( response ){
            if (response['status'] == 'error'){
                show_message('Error', 'Error terminating ' +
                  that.get('cluster_name') + '.');
                } else {
                show_message('Info', 'Terminating ' +
                   that.get('cluster_name') + '.');
                }
                });
         }
         setTimeout( function(){update_status(); }, 5000);      
         console.log(this.get('cluster_name') + ' terminate');
    },
    restart : function(){
      if(this.restartable()){
         if( this.isGPU() ){
              var t_url =  '/cm/gpucluster';
         } else {
              var t_url =  '/cm/datacluster';
         }
         var c_term = $.post(t_url, 
                 {cluster_name: this.get('cluster_name'),
                 component:'restart'
                 });
         var that = this;
         c_term.done( function( response ){
            if (response['status'] == 'error'){
                show_message('Error', 'Error restarting ' +
                  that.get('cluster_name') + '.');
                } else {
                show_message('Info', 'Restarting ' +
                   that.get('cluster_name') + '.');
                }
                });
        setTimeout( function(){update_status(); }, 5000);      
     
        console.log( this.get('cluster_name') + ' restart');
      }
    },
  startLogger : function(){
    if(this.isGPU() && this.startloggable()){
         var c_term = $.post('/gpucluster', 
                 {cluster_name: this.get('cluster_name'),
                  component:'logserver-daemon',
                  action:'start',
                 });
         var that = this;
         c_term.done( function( response ){
            if (response['status'] == 'error'){
                  show_message('Error', 'Error starting gpu-logger' +
                  ' on ' + that.get('cluster_name') + '.');
                } else {
                  show_message('Info', 'Starting gpu-logger' +
                    ' on ' + that.get('cluster_name') + '.');
                }
                });
         setTimeout( function(){update_status(); }, 5000);      
    console.log( this.get('cluster_name')+' startLogger');
    }
  },
  startGPU : function(gid){
    if(this.isGPU() && this.startgpuable(gid)){
        this.actGPU( gid, 'start');
        setTimeout( function(){update_status(); }, 5000);      
    }
  },
             
  actGPU : function( gid, action ){

         var c_term = $.post('/gpucluster', 
                 {cluster_name: this.get('cluster_name'),
                  component:'gpuserver-daemon',
                  action:'start',
                  gid: gid
                 });
         var that = this;
         c_term.done( function( response ){
            if (response['status'] == 'error'){
                show_message('Error', 'Error ' + action + 'ing gpu' + gid +
                  'on ' + that.get('cluster_name') + '.');
                } else {
                show_message('Info', action+'ing gpu' + gid +
                    ' on ' + that.get('cluster_name') + '.');
                }
                console.log(response);
                });
      console.log( this.get('cluster_name') + ' startGPU' + gid );
  },
  startDataCluster: function(){
    if(this.isData() && this.startable() ){
       show_message('Error', 'Starting a datacluster server is not supported yet');
      console.log( this.get('cluster_name') + ' startDataCluster' );
    }
  },


  isGPU : function(){
    return this.get("cluster_type") == "gpu";
  },
  isData : function(){
    return this.get("cluster_type") == "data";
  },
  _getLog : function(){
    if( this.get("active") != 0 ){
    var that = this;
                
    var s3 = new AWS.S3;
    var configString = 'None';
    var req = s3.getObject({Bucket:'ndp-adversary', 
        Key: 'logs/sc_startup/' +  g_instance_id + '/' + that.get('cluster_name') + '.log'})
    req.on('error', function(error, response){
        if (error.name == "NoSuchKey"){ 
            configString = 'No log for ' + that.get('cluster_name');
        } else {
            configString = error.message;
        }
        if (that.get('log') != configString){
          that.set('log', configString)
        }
    });
    req.on('success', function(response){
        //testing_var = response;
        //console.log(response);
        configString = response.data.Body.toString();
        that.set('log', remove_header(configString));
    });
    req.send();
  }
  },
setDisplayState : function(){
    if (this.get('ready')){
        this.set('display_state', 'success');
    }
    else if( this.get('active') && !this.get('ready') ){
        this.set('display_state', 'warning');
    }
    else if( !this.get('active') && this.isData() ){
        this.set('display_state', 'primary');
    } else if( !this.get('active') && this.isGPU() ){
        this.set('display_state', 'info');
    }
    /**
      else if( this.get('terminated') ){
        this.set('display_state', 'danger');
      }
    **/
},
refresh : function(){
    this.fetch();
    this.setDisplayState();
    this._getLog();
  }

});

