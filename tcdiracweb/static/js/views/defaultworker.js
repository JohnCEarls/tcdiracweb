/**
 *  The DefaultWorkerView takes a single DefaultWorker and displays it
 *  in a panel
 * **/
var DefaultWorkerView = Backbone.View.extend({
    type : "DefaultWorkerView",
    template : _.template( $('#template-default-worker').html() ),
    tagName:"div",
    className : "panel panel-default",
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        this.model.on('delete', this.clear)
    },

    render : function(){
        var outputHtml = this.template( this.model.toJSON() );
        $(this.el).html(outputHtml);
        return this;
    },

    events : {
        'click .edit': 'loadEditForm',
        'click .delete': 'deleteModel',
    },

    loadEditForm : function(){
        if( app.dwfv !== undefined ){
            //a form is active, so remove it
            app.dwfv.remove();
        }

        app.dwfv = new DefaultWorkerFormView({ 
            collection : this.collection,
            model: this.model });
        app.dwfv.render();
    },

    deleteModel : function(){
        this.collection.remove(this.model);
        that = this;
        this.model.delete( function( data, textStatus, jqXHR){
            // success
            that.collection.remove( that.model );
            that.remove();
        },
        function( jqXHR, textStatus, errorThrown){
            //error
            console.log('Error on delete');
            console.log( jqXHR );
            console.log( textStatus );
            console.log( errorThrown );
        });
    },
}); 

var DefaultWorkerCollectionView = Backbone.View.extend({
    type : "DefaultWorkerCollectionView",
    template : _.template( $('#template-default-worker-list').html() ),
    initialize : function(){
        this.domList = new Array();
        _.bindAll.apply(_, [this].concat(_.functions(this)))
        this.collection.bind('add', this.addOne); 
    },

    render : function(){
        var outputHtml = this.template();
        $(this.el).html( outputHtml );
        that = this;
        this.collection.fetch({
            add: true,
            success: that.loadComplete,
            error: that.loadError
        });
        return this;
    },
    loadComplete : function(){},
    /*
    addOne replaced this, but I am too much of a coward to just delete it
    if you run into this later and no problems, delete
    processCluster : function( cluster ){
        var mydcv = new DefaultWorkerView(
            {collection: this.collection,
                model:cluster});
        console.log(this.collection);
        mydcv.render();
        this.$el.find('div#accordion').append(mydcv.el);
    },
    */

    /* Adds a defaultworkerview to the collection view  */
    addOne: function(foo) {
        var $children = this.$el.find('div#accordion').children(),
            index = this.collection.indexOf(foo),
            view = new DefaultWorkerView(
            {collection: this.collection,
                model:foo});
        if (this.domList.length == 0) {
          //add first element
          this.domList.push(index);
          this.$el.find('div#accordion').append(view.render().el);
        } else {
          //add collection to domList and sort
          this.domList.push(index);
          this.domList.sort(function(a,b){
            return (a-b)});
          //get position of element in list and add one to offset
          //initial dom element that contains insert button
          var ins = this.domList.indexOf(index) + 1;
          //gives element at current position
          var pos = $children.eq(ins);
          console.log( pos );
          if (pos.length > 0) {//there are elements that will follow
            pos.before(view.render().el);
          } else {
            //add to the end
            this.$el.find('div#accordion').append(view.render().el);
          }
        }
    },

    events : {
        'click .insert' : 'loadInsertForm'
    },

    /** send default worker to form **/
    loadInsertForm : function(){
        var new_model = new DefaultWorker();
        if( app.dwfv !== undefined ){
            app.dwfv.remove()
        }
        app.dwfv = new DefaultWorkerFormView( { 
            collection : this.collection,
            model : new_model } );
        app.dwfv.render();
    },


});
/** The form for editting **/
var DefaultWorkerFormView = Backbone.View.extend({
    tagName : "div",
    type : "DefaultWorkerFormView",
    template : _.template( $('#template-default-worker-form').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)))
    },

    render : function(){
        var outputHtml = this.template( this.model.toJSON() );
        $(this.el).html( outputHtml );
        $('#cluster-form-container').append(this.el);
    },

    events : {
        'click #template-default-worker-button' : 'submitForm',
    },

    submitForm : function(){
        var arr = this.$el.find('form#cluster_config').serializeArray();
        var data = _(arr).reduce( function( acc, field ){
            acc[field.name] = field.value;
            return acc;
        }, {});
        if( data.force_spot_master === undefined){
            data.force_spot_master = false;
        } else {
            data.force_spot_master = true;
        }
        if( this.model.get('cluster_type') !== data.cluster_type ||
                    this.model.get('aws_region') !== data.aws_region)
        {
            var new_model = new DefaultWorker(data);
            new_model.save();
            this.collection.add(new_model);
        } else {
            this.model.save( data );
        }
        this.remove()
    }

});
