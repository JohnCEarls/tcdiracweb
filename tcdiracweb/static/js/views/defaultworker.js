var DefaultWorkerView = Backbone.View.extend({
    type : "DefaultWorkerView",
    template : _.template( $('#template-default-worker').html() ),
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
            app.dwfv.remove();
        }

        app.dwfv = new DefaultWorkerFormView({ 
            collection : this.collection,
            model: this.model });
        app.dwfv.render();
    },

    deleteModel : function(){
        console.log( 'deleting model' );
        this.collection.remove(this.model);
        that = this;
        this.model.delete( function( data, textStatus, jqXHR){
            console.log( that.collection );
            that.collection.remove( that.model );
            that.clear();
            console.log( that.collection );
        },
        function( jqXHR, textStatus, errorThrown){
            console.log( jqXHR );
            console.log( textStatus );
            console.log( errorThrown );
        });
    },
    clear : function(){
        this.$el.html('');
    }

}); 

var DefaultWorkerCollectionView = Backbone.View.extend({
    type : "DefaultWorkerCollectionView",
    template : _.template( $('#template-default-worker-list').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)))
        this.collection.bind('add', this.processCluster);
        this.render();
    },
    render : function(){
        console.log("rendering");
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
    loadComplete : function(){
        console.log("loadComplete");
    },
    processCluster : function( cluster ){
            //if(cluster !== undefined && cluster.cluster_type !== 'None')
            //{//stupid hack
                var mydcv = new DefaultWorkerView(
                    {collection: this.collection,
                        model:cluster});
                mydcv.render();
                this.$el.find('div#accordion').append(mydcv.el);
            //}
    },


    
    events : {
        'click .insert' : 'loadInsertForm'
    },

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

var DefaultWorkerFormView = Backbone.View.extend({
    //el: '#cluster-form-container',
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
        //if( data.cluster_type !== 'None' )
        //{//stupid hack
            if( this.model.get('cluster_type') !== data.cluster_type ||
                        this.model.get('aws_region') !== data.aws_region)
            {
                console.log('update')
                console.log( this.model )
                console.log( data )
                    var new_model = new DefaultWorker(data);
                    new_model.save();
                    this.collection.add(new_model);
            } else {
                console.log('insert')
                console.log( this.model )
                console.log( data )
                this.model.save( data );
            }
        //}

        this.remove()
    }

});
