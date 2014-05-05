// views/clusterconsole.js
var MasterView = Backbone.View.extend({
    type : "MasterView",
    template : _.template( $('#template-master').html() ),
    tagName : "div",
    id : "masterview",
    className : "panel panel-primary",
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        this.model.fetch();
        return this;
    },

    render : function() {
        var st_status = this.model.str_status();
        if( this.model.get('status') === 0 ){
            this.className = "panel panel-warning";
        } else if ( this.model.get('status') === 10 ){
            this.className = "panel panel-success";
        } else {
            this.className = "panel panel-danger";
        }
        json_model = this.model.toJSON();
        json_model['st_status'] = st_status;
        $(this.el).html( this.template( json_model ) );
        this.el.className = this.className;
        return this;
    },
});

var MasterRow = Backbone.View.extend({
    type : "MasterRow",
    tagName : "tr",
    className : "default",
    id : "masterRow",
    template : _.template( $('#template-cluster-row-master').html() ),

    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        this.model.fetch();
        return this;
    },

    events : {
        'click .master-info' : 'loadSideView',
        'click .refresh' : 'refresh',
    },

    render : function() {
        if( this.model.get('status') === 0 ){
            this.className = "warning";
        } else if ( this.model.get('status') === 10 ){
            this.className = "success";
        } else {
            this.className = "danger";
        }
        json_model = this.model.toJSON();
        json_model['st_status'] = this.model.str_status();
        $(this.el).html( this.template( json_model ) );
        this.el.className = this.className;
        return this;
    },

    loadSideView : function(){
        var displayed = false;
        if( app.sidePanel !== undefined ){
            if(app.sidePanel.model &&
                app.sidePanel.type === "WorkerView" &&
                app.sidePanel.model.get("worker_id") ===
                this.model.get("worker_id")){
                displayed = true;
            }
            try{
                app.sidePanel.remove();
            } catch(err){
                //not there, so just continue
            }
            app.sidePanel = {};
        }
        if( ! displayed){
            app.sidePanel = new MasterView( {model: this.model} );
            $('#small-container').append( app.sidePanel.render().el );
        }
    },

    refresh : function(){
        this.model.fetch();
    },

});


var WorkerCollectionView = Backbone.View.extend({
    el : "#worker-table",
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)))
        this.collection.bind('add', this.addWorker);
        this.collection.fetch(
            { add : true,
              success : this.loadCompleteHandler,
              error : this.loadErrorHandler
            }
        );

    },
    render : function(){
        return this;
    },

    addWorker : function( worker ){
        this.removeEmpty();
        var worker_view = new WorkerRow( { model: worker } );
        this.$el.append( worker_view.render().el );
    },

    loadCompleteHandler : function( collection, response, options){
        console.log("loadCompleteHandler");
    },

    loadErrorHandler : function( collection, response, options){
        //what the server actually returned
        var msg = response.responseJSON;
        if( response && response.responseJSON ){
            this.showEmpty( msg );
        }
    },

    showEmpty : function( message ){
        this.removeEmpty();//lazy
        var t = _.template( $('#template-worker-empty').html() );
        $('#large-container').append( t( message ) );
    },

    removeEmpty : function(){
        $('#large-container').find('#worker-empty').remove();
    },

});

var WorkerRow = Backbone.View.extend({
    type : "WorkerRow",
    tagName : "tr",
    className : "default",
    id : "workerRow",
    template : _.template( $('#template-cluster-row-worker').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        app.master_model.on('change', this.render, this);
        this.model.fetch();
        return this;
    },

    events : function(){
        var events = {
        'click .worker-info' : 'loadSideView',
        'click .refresh' : 'refresh',
        };
        switch( this.model.get('status') )
        {
            case 0: //configured
                events['click .activate'] = 'activate';
                events['click .terminate'] = 'terminate';
                break;
            case 10: //Starting
                events['click .terminate'] = 'terminate';
                break;
            case 20: //ready
                events['click .terminate'] = 'terminate';
                events['click .activate'] = 'activate';
                break;
            case 30: //running
                events['click .terminate'] = 'terminate';
                break;
            case 35: //marked for termination
                events['click .terminate'] = 'terminate';
                break;
            case 40:
                break;
            default:
                console.log('Error: unmatched status');
                break;
        }
        return events;
    },

    manageControls : function () {
        //add functions to the button, depending on current status
        var dm = this.$el.find('.dropdown-menu');
        var status = this.model.get('status');
        switch( status )
        {
            case 0: //configured
                dm.append('<li><a href="#" class="activate">Launch Cluster</a></li>');
                dm.append( '<li><a href="#" class="terminate">Remove</a></li>');
                break;
            case 10: //Starting
                dm.append( '<li><a href="#" class="terminate">Terminate</a></li>');
                break;
            case 20: //ready
                dm.append('<li><a href="#" class="activate">Start Server</a></li>');
                dm.append( '<li><a href="#" class="terminate">Terminate</a></li>');
                break;
            case 30: //running
                dm.append( '<li><a href="#" class="terminate">Terminate</a></li>');
                break;
            case 35: //marked for termination
                dm.append( '<li><a href="#" class="terminate">Remove</a></li>');
                break;
            default:
                console.log('Error: unmatched status');
                break;
        }
    },

    inconsistent_state : function(){
        if( app && app.master_model && 
            app.master_model.get('master_name') !==
                this.model.get('master_name') ){
            console.log( this.model.get('master_name') );
            return true;
        } else {
            return false;
        }
    },

    render : function() {
        switch( this.model.get('status') )
        {
            case 0: //configured
                this.className = "default";
                break;
            case 10: //Starting
                this.className = "info";
                break;
            case 20: //ready
                this.className = "primary";
                break;
            case 30: //running
                this.className = "success";
                break;
            case 35: //marked for termination
                this.className = "warning"
                break;
            case 37: //terminating
                this.className = "warning"
                break;
            case 40://terminated
                this.className = "default"
                break;
            default:
                this.className = "danger"
                console.log('Error: unmatched status');
                break;
        }
        if( this.inconsistent_state() ){
            //points at wrong master
            this.className = "danger";
        } 
        json_model = this.model.toJSON();
        json_model['st_status'] = this.model.str_status();
        $(this.el).html( this.template( json_model ) );
        this.el.className = this.className;
        this.manageControls();
        this.delegateEvents();
        return this;
    },

    loadSideView : function(){
        var displayed = false;
        if( app.sidePanel !== undefined ){
            if(app.sidePanel.model &&
                app.sidePanel.type === "WorkerView" &&
                app.sidePanel.model.get("worker_id") ===
                this.model.get("worker_id")){
                displayed = true;
            }
            try{
                app.sidePanel.remove();
            } catch(err){
                //not there, so just continue
            }
            app.sidePanel = {};
        }
        if( ! displayed){
            app.sidePanel = new WorkerView( {model: this.model} );
            $('#small-container').append( app.sidePanel.render().el );
        }
    },

    refresh : function(){
        this.model.fetch();
    },

    activate : function(){
        this.model.activate();
    },

    terminate : function(){
        console.log('terminate in view');
        this.model.terminate();
    },

});

var WorkerView = Backbone.View.extend({
    type : "WorkerView",
    template : _.template( $('#template-worker').html() ),
    tagName : "div",
    id : "workerview",
    className : "panel panel-primary",
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        this.model.fetch();
        return this;
    },

    render : function() {
        var st_status = this.model.str_status();
        switch( this.model.get('status') )
        {
            case 0: //configured
                this.className = "default";
                break;
            case 10: //Starting
                this.className = "info";
                break;
            case 20: //ready
                this.className = "primary";
                break;
            case 30: //running
                this.className = "success";
                break;
            case 35: //marked for termination
                this.className = "warning"
                break;
            case 37: //terminating
                this.className = "warning"
                break;
            case 40://terminated
                this.className = "default"
                break;
            default:
                this.className = "danger"
                console.log('Error: unmatched status');
                break;
        }
        json_model = this.model.toJSON();
        json_model['st_status'] = st_status;
        $(this.el).html( this.template( json_model ) );
        this.el.className = this.className;
        return this;
    },
});

var DefaultWorkerButtonView = Backbone.View.extend({
    type : "DefaultWorkerButtonView",
    el :"#defaultworker-button",
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.collection.bind('add', this.addDW);
        this.collection.fetch();
        this.render();
    },
    render : function(){
        return this;
    },
    addDW : function( default_worker ){
        console.log( default_worker );

        var worker_view = new DefaultWorkerDropdownView( { model: default_worker } );
        this.$el.find('#add-cluster-button').append( worker_view.render().el );
    }
});

var DefaultWorkerDropdownView = Backbone.View.extend({
    type : "DefaultWorkerDropdown",
    template : _.template( $('#template-defaultworker-dropdown').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        return this;
    },
    render : function(){
        $(this.el).html( this.template( this.model.toJSON() ));
        return this;
    },

    events : {
        'click .add-cluster' : 'addCluster',
    },
    addCluster : function(){

        if( app.master_model && app.master_model.get('master_name') !== "None"){
            msg = {
                cluster_type : this.model.get('cluster_type'),
                aws_region : this.model.get('aws_region'),
                master_name : app.master_model.get('master_name')
             }
            console.log(msg);
            $.post('/cm/init/worker', msg,
                    function( data, textStatus, jqXHR )
                    {
                        app.worker_collection.add( new Worker(data.data) );
                        console.log( 'successful init worker post' );
                        console.log( data );
                        console.log( textStatus );
                        console.log( jqXHR );
                    }
             );
       } else {
           alert('You cannot add a cluster without a master');
       }
       console.log("Add Cluster");
    },
});
