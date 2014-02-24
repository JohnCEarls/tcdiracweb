requirejs.config({
    baseUrl :'static/js/lib',
    paths: {
        jquery :'jquery-2.1.0',
        underscore:'underscore',
        backbone: 'backbone',
        d3: 'd3.v3.js' ,
        bootstrap: 'bootstrap',
        models: '../models',
        view: '../view'
    },
    shim :{
        "bootstrap": {
            deps: ["jquery"],
            exports: "$.fn.popover"
        },
        'backbone': {
            deps: ['underscore', 'jquery'],
            exports: 'Backbone'
        },
        'underscore': {
            exports: '_'
        }
    },  
});

require(['jquery', 'backbone', 'models/Network'], function($, Backbone, Network){
    $('body').append('<h1>Test</h1>');
    console.log(Network);
    var net1 = new Network.Model();
    console.log(net1);
    var net =   new Network.Model(
                    {
                        name:'test', 
                        source:'biocarta',
                        information_uri: 'http://google.com/',
                        geneIds: ['gene1', 'gene2', 'gene3']
                    }
                );
    console.log(net);
});