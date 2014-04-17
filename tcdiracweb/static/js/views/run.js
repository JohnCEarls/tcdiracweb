/**
 *  The DefaultWorkerView takes a single DefaultWorker and displays it
 *  in a panel
 * **/
var RunView = Backbone.View.extend({
    type : "RunView",
    template : _.template( $('#template-run').html() ),
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
        console.log("in loadEditForm");
        if( app.rfv !== undefined ){
            //a form is active, so remove it
            app.rfv.remove();
        }

        app.rfv = new RunFormView({ 
            collection : this.collection,
            model: this.model });
        app.rfv.render();
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

var RunCollectionView = Backbone.View.extend({
    type : "RunCollectionView",
    template : _.template( $('#template-run-list').html() ),
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

    /* Adds a defaultworkerview to the collection view  */
    addOne: function(foo) {
        var $children = this.$el.find('div#accordion').children(),
            index = this.collection.indexOf(foo),
            view = new RunView(
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
        var new_model = new Run();
        if( app.rfv !== undefined ){
            app.rfv.remove()
        }
        app.dwfv = new RunFormView( { 
            collection : this.collection,
            model : new_model } );
        app.rfv.render();
    },


});
/** The form for editting **/
var RunFormView = Backbone.View.extend({
    tagName : "div",
    type : "RunFormView",
    template : _.template( $('#template-run-form').html() ),
    initialize : function(){
        _.bindAll.apply(_, [this].concat(_.functions(this)))
    },

    render : function(){
        var outputHtml = this.template( this.model.toJSON() );
        $(this.el).html( outputHtml );
        $('#run-form-container').append(this.el);
    },

    events : {
        'click #template-run-button' : 'submitForm',
    },

    submitForm : function(){
        var arr = this.$el.find('form#run_config').serializeArray();
        console.log( arr );
        data = {};
        for( var i = 0; i < arr.length ; i++ ){
            var field = arr[i];
            var temp = field.name.split("__");
            var value = field.value;
            if( $.isNumeric(field.value) ){
                var value = Number( field.value );
            }
            if( temp.length > 1 ){
                var p_name = temp[0];
                var s_name = temp[1];
                if( data[p_name] === undefined ){
                    data[p_name] = {};
                }
                data[p_name][s_name] = value;

            } else {
                data[field.name] = value;
            }
        }
        console.log(data);
        /**
        var data = _(arr).reduce( function( acc, field ){
            var temp = field.name.split("__");
            console.log( temp );
            console.log( temp[0] );
            
            if( temp.length > 1 ){
                var base = temp[0];
                var secondary = temp[1];
                console.log(temp);
                console.log( base );
                console.log( secondary );
                console.log( field.value )
                acc[base] = {};
                acc[base][secondary] = field.value
            }else{
                acc[field.name] = field.value;
            }
            return acc;
        }, {});
        console.log( data );
       **/
        /**
        if( data.force_spot_master === undefined){
            data.force_spot_master = false;
        } else {
            data.force_spot_master = true;
        }
        if( this.model.get('run_id') !== data.run_id)
        {
            var new_model = new Run(data);
            new_model.save();
            this.collection.add(new_model);
        } else {
            this.model.save( data );
        }
        this.remove();
        **/
    }

});
