ClusterFormView = Backbone.View.extend({
    initialize : function(){
        this.render();
    },
    render : function(){
        var template = _.template($('#cluster-form').html(), {});
        this.$el.html( template )
    }
});
