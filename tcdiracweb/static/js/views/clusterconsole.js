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

});


var WorkerCollectionView = Backbone.View.extend({
    el : "#worker-table",
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)))
        this.collection.bind('add', this.addWorker);
        this.collection.fetch();
    },
    render : function(){
        return this;
    },
    addWorker : function( worker ){
        var worker_view = new WorkerRow( { model: worker } );
        this.$el.append( worker_view.render().el );
    }
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
        this.model.fetch();
        return this;
    },
    events : {
        'click .worker-info' : 'loadSideView',
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
            app.sidePanel = new WorkerView( {model: this.model} );
            $('#small-container').append( app.sidePanel.render().el );
        }
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
       console.log("Add Cluster");
    },
});
