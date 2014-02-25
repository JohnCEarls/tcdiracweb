requirejs.config({
    baseUrl :'static/js/lib',
    paths: {
        jquery :'jquery-2.1.0',
        underscore:'underscore',
        backbone: 'backbone',
        d3: 'd3.v3.js' ,
        bootstrap: 'bootstrap',
        models: '../models',
        views: '../views',
        aws: 'aws-sdk'
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
        },
        'aws' :{
            exports: 'AWS'
        }

    },  
});

require(['jquery', 'backbone', 'models/Network', 'views/Network', 'aws','bootstrap'], 
    function($, Backbone, Network, NetworkView, AWS){
        AWS.config.update({ accessKeyId : 'AKIAICSUGQN6QC454K3A' , 
            secretAccessKey:'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' });
        AWS.config.region = 'us-east-1';
        ddb = new AWS.DynamoDB();
        req = ddb.describeTable({'TableName':'network'});
        req.send();
        req.on('success', function(data){
            console.log("success");
            console.log(data);
        })

    $('body').append('<h1>Test</h1>');
    console.log(Network);
    console.log(NetworkView);
    console.log(AWS);
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
    //var nc = new Network.Collection();
    //console.log(nc);
    //nc.fetch();
    //nv = new NetworkView.View({model:net});
    //nv.render();
    //$('#accordion').append(nv.el);
    //console.log(nv);
    var nc2 = new Network.Collection();
    ncv = new NetworkView.CollectionView({collection: nc2});
    $('body').append(ncv.el);
});