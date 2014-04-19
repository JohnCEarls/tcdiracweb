var MasterView = Backbone.View.extend({
    type : "MasterView",
    template : _.template( $('#template-master').html() ),
    tagName : "div",
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
    template : _.template( $('#template-cluster-row-master').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)));
        this.model.on('change', this.render, this);
        this.model.fetch();
        return this;
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
});
