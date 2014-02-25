define(['jquery', 'underscore', 'backbone', 'models/Network'], function($, _, Backbone, NetworkModel){
    var NetworkView = Backbone.View.extend({
        type: 'NetworkView',
        template: _.template($('#collapse-network').html()),
        initialize : function(){
            this.model.on("change", this.NetworkChanged, this);
        },
        NetworkChanged : function( model, changes){
            console.log(model.get('name') + 'changed');
        },
        render: function(){
            console.log(this.model);
            var oh = this.template(this.model.toJSON());
            this.$el.html( oh );
            return this;
        }
    });

    var NetworkCollectionView = Backbone.View.extend({
        type: 'NetworkCollectionView',
        tagName: 'div',
        className: 'panel-group',
        id: 'accordion',
        model: NetworkModel.Model,
        initialize : function(){
            _.bindAll.apply(_, [this].concat(_.functions(this)));
            this.render();
            this.collection.bind('add', this.processNetwork);
            
            this.collection.fetch({
                add:true,
                success: function(){ console.log('fetching');},
                error: this.errorHandler
            });
            
        },
        processNetwork : function( network ){
            console.log("processNetwork");
            console.log(network);
            var nv = new NetworkView({model: network});
            nv.render();
            this.$el.append( nv.el );
        },
        errorHandler : function( error ){
            console.log(error)
        }
    })
    return {View: NetworkView, CollectionView: NetworkCollectionView};
});