var DefaultWorkerView = Backbone.View.extend({
    type : "DefaultWorkerView",
    template : _.template( $('#template-default-worker').html() ),
    render : function(){
        var outputHtml = this.template( this.model.toJSON() );
        $(this.el).html(outputHtml);
        return this;
    },
    events : {
        'click .edit': 'loadEditForm',
    },

    loadEditForm : function(){
        var dwfv = new DefaultWorkerFormView({ model: this.model });
        dwfv.render();
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
            var mydcv = new DefaultWorkerView({model:cluster});
            mydcv.render();
            this.$el.find('div#accordion').append(mydcv.el);
    },

});

var DefaultWorkerFormView = Backbone.View.extend({
    el: '#cluster-form-container',
    type : "DefaultWorkerFormView",
    template : _.template( $('#template-default-worker-form').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)))
    },

    render : function(){
        var outputHtml = this.template( this.model.toJSON() );
        $(this.el).html( outputHtml );
    },

    events : {
        'click #template-default-worker-button' : 'submitForm',
    },

    submitForm : function(){
        var arr = this.$el.find('form#cluster_config').serializeArray();
        console.log(arr);
        var data = _(arr).reduce( function( acc, field ){
            acc[field.name] = field.value;
            return acc;
        }, {});

        if( data.force_spot_master === undefined){
            data.force_spot_master = false;
        } else {
            data.force_spot_master = true;
        }
        console.log(data);
        this.model.save( data );
    }

});
