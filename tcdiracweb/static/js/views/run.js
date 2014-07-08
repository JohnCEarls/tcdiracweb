/**
 *  The RunView takes a single Run and displays it
 *  in a panel
 * **/
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

    events : {
        'click .edit': 'loadEditForm',
        'click .delete': 'deleteModel',
        'click .initialize' : 'initializeRun',
    },

    loadEditForm : function(){
        if( app.rfv !== undefined ){
            //a form is active, so remove it
            app.rfv.remove();
        }

        app.rfv = new RunFormView({ 
            collection : this.collection,
            model: this.model });
        app.rfv.render();
        app.rfv.$el.get(0).scrollIntoView(); 
        this.$el.find('.collapse').collapse('hide');
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

    initializeRun : function(){
        if( this.model.get('status') == -10 ){
            this.model.initializeRun();
        } else {
            alert('You can only initialize runs with CONFIG(-10) status');
        }
    },
    getSQSCount : function(){
        fd2g = this.model.get('intercomm_settings').sqs_from_data_to_gpu;
        console.log('getSQSCounts');
        console.log(fd2g);
        console.log( $('span.badge#' + fd2g) );
        getSQSCount( fd2g, $('span.badge#' + fd2g));
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

    /* Adds a runview to the collection view  */
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

    /** send run to form **/
    loadInsertForm : function(){
        var new_model = new Run();
        if( app.rfv !== undefined ){
            app.rfv.remove()
        }
        app.rfv = new RunFormView( { 
            collection : this.collection,
            model : new_model } );
        app.rfv.render();
        app.rfv.$el.get(0).scrollIntoView(); 
    },


});
/** The form for editting **/
var RunFormView = Backbone.View.extend({
    tagName:"div",
    className : "panel panel-info",
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
        var data = {};
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
        if( this.model.get('run_id') !== data.run_id)
        {
            //run_id is immutable, changing it makes a copy
            //of the run
            var new_model = new Run(data);
            new_model.save();
            this.collection.add(new_model);
        } else {
            this.model.save( data );
        }
        this.remove();
    },



});
