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
        'click .start-all-clusters' : 'startAllClusters',
        'click .terminate-all-clusters' : 'terminateAllClusters',
        'click .activate-all-workers' : 'activateAllWorkers',
        'click .stop-all-workers' : 'stopAllWorkers',
        'click .status-all-workers' : 'statusAllWorkers',
    },
    startAllClusters : function(){
        this.sendAllCommand('/cm/activate/worker/all');

    },
    terminateAllClusters : function(){
        if( confirm("Terminate all clusters") ){
            this.sendAllCommand('/cm/terminate/worker/all');
        }
    },

    activateAllWorkers : function(){
        this.sendAllCommand('/cm/activate/server/all');
    },
    statusAllWorkers : function(){
        this.sendAllCommand('/cm/status/server/all');
    },
    stopAllWorkers : function(){
        this.sendAllCommand('/cm/stop/server/all');
    },
    sendAllCommand : function(url){
        if( app.worker_collection.length === 0){
            alert('No clusters configured');
            return;
        }
        $.post(url, {},
            function( data, textStatus, jqXHR )
            {
                if(data.data){
                    _.forEach(data.data, function( worker_id ){
                        for(var i=0; i<40; i++){
                            var time =i*i*100 +  5000 * i + 1000 * Math.random();
                            var wrk_mdl = app.worker_collection.get( worker_id );
                            setTimeout( function(){
                                var wrk_mdl = app.worker_collection.get( worker_id );
                                wrk_mdl.fetch();
                            }, time );
                        }
                    });
                }
            }
        );
    },

    render : function() {
        if(this.model.get('master_name') == 'None'){
            this.showEmpty();
        } else {
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
            this.addGroupActivationButtons();
            this.addWorkerButtons();
        }
        return this;
    },

    addWorkerButtons : function(){
        that = this;
        console.log('adding worker buttons')
        var dfwbv = new DefaultWorkerButtonView(
            { collection : new DefaultWorkerCollection(),
               master_model : that.model,
               el : that.$el.find('#master-action-menu'),
        });
    },

    addGroupActivationButtons : function(){
        menu = this.$el.find('#master-action-menu');
        menu.append('<li><a href="#" class="start-all-clusters">' +
                    '<span class="glyphicon glyphicon-music"></span> ' +
                    'Launch All Clusters</a></li>');
        menu.append('<li><a href="#" class="terminate-all-clusters">'+
                    '<span class="glyphicon glyphicon-remove"></span>' +
                    ' Terminate All Clusters</a></li>');
        menu.append('<li class="divider"></li>');
        menu.append('<li><a href="#" class="activate-all-workers"><span class="glyphicon glyphicon-heart"></span> Start All Servers</a></li>');
        menu.append('<li><a href="#" class="status-all-workers"><span class="glyphicon glyphicon-info-sign"></span> Stat All Servers</a></li>');

        menu.append('<li><a href="#" class="stop-all-workers"><span class="glyphicon glyphicon-exclamation-sign"></span> Stop All Servers</a></li>');
        menu.append('<li class="divider"></li>');
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

    showEmpty : function( message ){
        this.removeEmpty();//lazy
        var t = _.template( $('#template-master-empty').html() );
        this.$el.append( t( {message: 'No active master server'} ) );
    },

    removeEmpty : function(){
        this.$el.find('#empty-row').remove();
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
                events['click .start'] = 'start';
                break;
            case 30: //running
                events['click .terminate'] = 'terminate';
                events['click .status'] = 'status_refresh';
                events['click .stop'] = 'stop';

                break;
            case 31: //Cluster error
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
                dm.append('<li><a href="#" class="activate"><span class="glyphicon glyphicon-music"></span> Launch Cluster</a></li>');
                dm.append( '<li><a href="#" class="terminate">' +
                          '<span class="glyphicon glyphicon-remove"></span>' +
                          ' Cancel Cluster</a></li>');
                break;
            case 10: //Starting
                dm.append( '<li><a href="#" class="terminate">'+
                          '<span class="glyphicon glyphicon-remove"></span>'+
                          ' Terminate Cluster</a></li>');
                break;
            case 20: //ready
                dm.append( '<li><a href="#" class="terminate">' +
                          '<span class="glyphicon glyphicon-remove"></span>' +
                          'Terminate Cluster</a></li>');
                dm.append('<li class="divider"></li>');
                dm.append('<li><a href="#" class="start"><span class="glyphicon glyphicon-heart"></span> Start Server</a></li>');
                break;
            case 30: //running
                dm.append('<li><a href="#" class="terminate">' +
                          '<span class="glyphicon glyphicon-remove"></span>'+
                          ' Terminate Cluster</a></li>');
                dm.append('<li class="divider"></li>');
                dm.append('<li><a href="#" class="status"><span class="glyphicon glyphicon-info-sign"></span> Refresh Server Status</a></li>');
                dm.append('<li><a href="#" class="stop"><span class="glyphicon glyphicon-exclamation-sign"></span> Stop Server</a></li>');
                break;
            case 31: //Cluster error
                dm.append( '<li><a href="#" class="terminate">'+
                          '<span class="glyphicon glyphicon-remove"></span>'+
                          ' Terminate Cluster</a></li>');
                break;
            case 35: //marked for termination
                dm.append( '<li><a href="#" class="terminate">' +
                          '<span class="glyphicon glyphicon-remove"></span>' +
                          ' Remove</a></li>');
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
            case 31: //cluster error
                this.className = "danger";
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
    
    start : function(){
        this.model.start();
    },

    stop : function(){
        this.model.stop();
    },

    status_refresh : function(){
        this.model.status_refresh();
    },

    terminate : function(){
        console.log('terminate in view');
        if( confirm( "Terminate " + this.model.get('cluster_name') + "?" )){
            this.model.terminate();
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

    events : {
        'click .log-refresh' : 'displayLog',
    },
    render : function() {
        var st_status = this.model.str_status();
        this.className = "panel panel-"
        switch( this.model.get('status') )
        {
            case 0: //configured
                this.className += "default";
                break;
            case 10: //Starting
                this.className += "info";
                break;
            case 20: //ready
                this.className += "primary";
                break;
            case 30: //running
                this.className += "success";
                break;
            case 35: //marked for termination
                this.className += "warning";
                break;
            case 37: //terminating
                this.className += "warning";
                break;
            case 40://terminated
                this.className += "default";
                break;
            default:
                this.className += "danger"
                console.log('Error: unmatched status');
                break;
        }
        json_model = this.model.toJSON();
        json_model['st_status'] = st_status;
        $(this.el).html( this.template( json_model ) );
        this.el.className = this.className;
        this.displayLog();
        return this;
    },

    displayLog : function(){
        $logList = this.$el.find('.log-items');
        $logList.empty();
        $.get('/cm/log/worker/' + this.model.get('worker_id'))
        .done( function( data ){
            _.forEach(data.data, function( msg ){
                $logList.append( msg );
           })
        })
        .fail( function(){
            $logList.append('<li class="list-group-item">NA</li>');
        });


    }
});

var DefaultWorkerButtonView = Backbone.View.extend({
    type : "DefaultWorkerButtonView",
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

        if( default_worker.get('available') ){//only show if available
            var worker_view = new DefaultWorkerDropdownView( { model: default_worker } );
            this.$el.append( worker_view.render().el );
        }
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

var RunCollectionView   = Backbone.View.extend({
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)))
        this.collection.bind('add', this.addRun);
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

    addRun : function( run ){
        this.removeEmpty();
        var run_view = new RunRow( { model: run } );
        this.$el.append( run_view.render().el );
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
        var t = _.template( $('#template-run-empty').html() );
        this.$el.append( t( message ) );
    },

    removeEmpty : function(){
        this.$el.find('#empty-row').remove();
    },

});

var RunView = Backbone.View.extend({
    type : "RunView",
    template : _.template( $('#template-run').html() ),
    tagName:"div",
    className : "panel panel-primary",
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        this.model.on('delete', this.clear)
    },

    render : function(){
        json_model = this.model.toJSON();
        var st_status = this.model.str_status();
        console.log( st_status )
        json_model['st_status'] = st_status;
        $(this.el).html( this.template( json_model ) );
        this.getSQSCount();
        return this;
    },

    getSQSCount : function(){
        var interSet =  this.model.get('intercomm_settings');
        for(var setting in interSet){
            if( setting.slice(0,3) === 'sqs' ){
                var url = '/cm/sqs/status/' + interSet[setting];
                $.getJSON( url )
                    .done( function( response ){
                        var selector = 'span.badge#' + response.data['q_name'];
                        $(selector).html( numeral(response.data['count']).format('0,0') );
                    })
                    .fail( function( response ){
                        var selector = 'span.badge#' + response.responseJSON.data['q_name'];
                        $(selector).addClass('alert-danger');
                        $(selector).html('NA');
                    });
            }
        }
    },
}); 

var RunRow = Backbone.View.extend({
    type : "RunRow",
    tagName : "tr",
    className : "default",
    id : "runrow",
    template : _.template( $('#template-cluster-row-run').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        app.master_model.on('change', this.render, this);
        this.model.fetch();
        return this;
    },

    events : function(){
        var events = {
        'click .run-info' : 'loadSideView',
        'click .refresh' : 'refresh',
        };
        switch( this.model.get('status') )
        {
            case -10: //configured
                events['click .initialize'] = 'initializeRun';
                events['click .abort'] = 'abortRun';
                break;
            case 0: //initialized
                events['click .abort'] = 'abortRun';
                break;
            case 10: //active
                events['click .abort'] = 'abortRun';
                break;
            case 15: //active all sent
               events['click .abort'] = 'abortRun';
                break;
            case 20: //complete
                break;
            case 30: //abort
                break;
            default:
                console.log('Error: unmatched status');
                break;
        }
        if( this.model.get('status') !== -10 && 
           this.model.get('master_name') !== app.master_model.get('master_name') ){
            events['click .reassign'] = 'reassign';
        }
        return events;
    },

    initializeRun : function(){
        this.model.initializeRun();
    },

    abortRun : function(){
        this.model.set('status', 30);
        this.model.save();
        console.log('abort');
    },

    reassign : function(){
        this.model.set('master_name', app.master_model.get('master_name'));
        this.model.save({master_name:  app.master_model.get('master_name')},
                        {patch:true});

        console.log('reassign');
    },

    render : function(){
        switch( this.model.get('status') )
        {
            case -10: //configured
                this.className = "default";
                break;
            case 0: //initialized
                this.className = "warning";
                break;
            case 10: //active
                this.className = "success";
                break;
            case 15: //active all sent
                this.className = "success";
                break;
            case 20: //complete
                this.className = "info"
                break;
            case 30: //abort
                this.className = "danger"
                break;
            default:
                this.className = "danger"
                console.log('Error: unmatched status');
                break;
        }

        if( this.model.get('status') !== -10 && 
           this.model.get('master_name') !== app.master_model.get('master_name') ){
            //this has wrong master
            this.className = "warning"
        }
        json_model = this.model.toJSON();
        json_model['st_status'] = this.model.str_status();
        $(this.el).html( this.template( json_model ) );
        this.manageControls();
        return this;
    },
   
    getControl : function( cls, glyph, txt ){
        return '<li><a href="#" class="'+cls+'">' +
               '<span class="glyphicon glyphicon-'+glyph+'"></span>' +
               txt +'</a></li>';
    },

    manageControls : function () {
        //add functions to the button, depending on current status
        var dm = this.$el.find('.dropdown-menu');
        var status = this.model.get('status');
        that = this;
        switch( status )
        {
            case -10: //configured
                dm.append(that.getControl("initialize","heart",'Initialize'));

                dm.append(that.getControl("abort","remove","Abort"));
                this.className = "default";
                break;
            case 0: //initialized
                this.className = "warning";
                dm.append(that.getControl("abort","remove","Abort"));
                break;
            case 10: //active
                this.className = "success";
                dm.append(that.getControl("abort","remove","Abort"));
                break;
            case 15: //active all sent
                this.className = "success";
                dm.append(that.getControl("abort","remove","Abort"));
                break;
            case 20: //complete
                this.className = "info"
                break;
            case 30: //abort
                this.className = "danger"
                break;
            default:
                this.className = "danger"
                console.log('Error: unmatched status');
                break;
        }
        if( this.model.get('status') !== -10 && 
           this.model.get('master_name') !== app.master_model.get('master_name') ){
            //this has wrong master
            dm.append('<li class="divider"></li>');
            dm.append(that.getControl("reassign","wrench","Reassign master"));
        }
    },

   loadSideView : function(){
        var displayed = false;
        if( app.sidePanel !== undefined ){
            if(app.sidePanel.model &&
                app.sidePanel.type === "RunView" &&
                app.sidePanel.model.get("run_id") ===
                this.model.get("run_id")){
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
            this.model.fetch();
            app.sidePanel = new RunView( {model: this.model} );
            $('#small-container').append( app.sidePanel.render().el );
        }
    },

    refresh : function(){
        this.model.fetch();
    },

});


