
var ClustersView = Backbone.View.extend({
  type: "ClustersView",
  template: _.template($('#template-clusters').html()),
  el: "#cluster-table-container",
  _rendered : false,
  table_header: {
    title : 'Cluster Management',
    headers : ['Name', 'Region', 'Size', ' ', ' ', 'Log', ' ' ] 
  },
  initialize: function (){
    this.render();
    _.bindAll.apply(_, [this].concat(_.functions(this)))
    this.collection.bind('add', this.processCluster);
  },
  render : function(){
    if (!this._rendered){
    this._rendered = true;
    var outputHTML = this.template( this.table_header );
    this.$el.append(outputHTML);
    }
    
    return this;
  },
  load: function(){
    this.collection.fetch({
        add: true,
        success: this.loadCompleteHandler,
        error: this.errorHandler
    });
  },  
  loadCompleteHandler: function(){
      console.log('loadCompleteHandler');                     
  },
  errorHandler : function(){
    throw "error loading collection";
  },

  processCluster : function(cluster ){
    if(!this._rendered){
      this.render();
    }
    var myclusterView = new ClusterView({ model: cluster });
    myclusterView.render();
    //console.log(cluster);
    //console.log("processCluster");
    //console.log(myclusterView);
    this.$el.find('tbody#cluster-body').append(myclusterView.el);
  }
});

var ClusterView = Backbone.View.extend({
  type : "ClusterView",
  template: _.template($('#template-cluster').html()),
  tagName: "tr",
  className: "clusterRow",
  url: '/cluster',
  initialize : function(){
    this.clickables();
    this.model.on("change", this.clusterChanged, this);
  },

  clusterChanged: function( model, changes ){
    this.clickables(); 
    
    console.log("clusterChanged:" + model.get("cluster_name"));
    console.log(changes);
    this.checkState();
  },
  events : {
    //cluster actions
    'click .launch': 'launchCluster',
    'click .restart': 'restartCluster',
    'click .terminate': 'terminateCluster',
    //server action
    //gpu
    'click .start-logger': 'startLogger',
    'click .start-gpu0': 'startGPU0',
    'click .start-gpu1': 'startGPU1',
    //data server
    'click .start-data-cluster': 'startDataCluster',

    'click .glyphicon-info-sign': 'setLog',
    'click  .glyphicon-refresh': 'refresh'
  },

  render: function () {
    var outputHtml = this.template(this.model.toJSON());
    this.$el.html(outputHtml);
    this.clickables();
    this.checkState();
    return this;
  },

clickables : function(){
    if(!this.model.launchable()){this.$('li.launch').addClass("disabled");}
    else {this.$('li.launch').removeClass("disabled");
    }

    if(!this.model.restartable()){this.$('li.restart').addClass("disabled");} 
    else { this.$('li.restart').removeClass("disabled"); }

    if( !this.model.terminatable() ){this.$('li.terminate').addClass("disabled");} 
    else { this.$('li.terminate').removeClass("disabled");
    }

    if( this.model.isData() ){
        if(!this.model.startable() ){this.$('li.start-data-cluster').addClass("disabled");} 
        else { this.$('li.start-data-cluster').removeClass("disabled");

        }
    } else {
        if(!this.model.startloggable()){
            this.$('li.start-logger').addClass('disabled');
        } else {
            this.$('li.start-logger').removeClass('disabled');
        }
        if(!this.model.startgpuable(0)){
            this.$('li.start-gpu0').addClass('disabled');
        } else {
            this.$('li.start-gpu0').removeClass('disabled');
        }
        if( !this.model.startgpuable(1) ){
            this.$('li.start-gpu1').addClass('disabled');
        } else {
            this.$('li.start-gpu1').removeClass('disabled');
        }
    }


  },
    
  removeLabels : function( selector ){
      var labels = ['label-default', 'label-primary', 'label-success', 
      'label-info', 'label-warning', 'label-danger'];
       labels.forEach( function( label ){
               //console.log(selector);
       selector.removeClass(label);
      });
      return selector;
  },

  checkState : function(){
     this.model.setDisplayState()
     var state = this.model.get('display_state');
     sel = this.removeLabels( this.$('span.label') );
     sel.addClass( 'label-' +  state  );
  },

  launchCluster: function(){
    this.model.launch();
  },
  restartCluster: function(){
    this.model.restart();
  },
  terminateCluster: function(){
    this.model.terminate();
  },
  startLogger: function(){
    this.model.startLogger();
  },
  startGPU0: function(){
    this.model.startGPU(0);
  },
  startGPU1: function(){
    this.model.startGPU(1);
  },
  startDataCluster: function(){
    this.model.startDataCluster()
                    },
  refresh : function(){
    console.log("refreshing");
    this.model.refresh();
  },              
  setLog : function(){
    $('h4#active-cluster').text( this.model.get('cluster_name') + ' Logs');
    $('textarea.logs')[0].value = this.model.get('log');
  }
});

