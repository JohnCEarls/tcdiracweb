function set_cluster_default( type ){
   var default_data = {'cluster_prefix': 'gpu-data',
                        'cluster_size': '10',
                        'region':'us-east-1',
                        'spot_bid':'.50',
                        'force-spot-master':false};
   var default_gpu = {'cluster_prefix': 'gpu-server',
                    'cluster_size': '1',
                    'spot_bid':'2.00',
                    'region':'us-east-1',
                    'force-spot-master':true};
   var regions = {'data': ['us-east-1', 'us-west-1', 'us-west-2'],
                 'gpu':['us-east-1', 'eu-west-1' ]};
   if(type == 'data'){
       deflt = default_data;
       reg = regions.data;
   } else {
       deflt = default_gpu;
       reg = regions.gpu;
   }
   console.log( type );
   console.log(deflt);
   console.log(reg);
   for (var setting in deflt){
       try{
           $('span#default-' + setting).text('(' + deflt[setting] + ')');
           if(setting == 'force-spot-master'){
                $('input#force_spot_master').prop('checked',deflt[setting]);
           }
       }catch(err){
         console.log(err);
       }
   }
   $('select#region').empty();
   reg.forEach(function(arg){$('select#region').append( '<option>' + arg + '</option>' );});
}

function init_cluster(){
    var dynamodb = new AWS.DynamoDB();
    var adversary_atts = ['master_name', 'cluster_name', 'num_nodes', 
    'cluster_type','region', 'active', ];
    params = {'TableName':'sc-adversary-config',
      'AttributesToGet':['cluster_name'],
      'ScanFilter': { "master_name": {'AttributeValueList':[ {"S": g_instance_id  } ],"ComparisonOperator": "EQ" } }, };
    request = dynamodb.scan( params );
    request.send();
    clustersModels = new ClustersModel();
    request.on('success', function( response ){
        console.log('success' + response);
        console.log(response);
        response.data.Items.forEach( function( item ){
            cm = { id: item.cluster_name.S };
            console.log(cm);
            var cluster = ClusterModel( cm );
            console.log(cluster);
            clustersModels.collection.add(cluster);
        });
    });
    request.on('error', function(error){console.log(error)});
    request.on('complete', function(){console.log('complete')});

}


function get_table(){
    scan_results = get_clusters();
    if (scan_results.length > 0){
        scan_results.forEach(function(cluster){
            $('table#cluster-table tbody').append(add_cluster(cluster));
            get_startup_log( cluster['cluster_name'] );
            if( cluster['active'] == 1){
                $('button#' + cluster['cluster_name']).prop('disabled', true);
            }
        }) ;
     } else {
        show_message('Warning', 'No cluster configurations available');
     }
    $(".tablesorter").trigger("update");
    $("#cluster-table").tablesorter();


    toHide = $('tr.log-row');
    for(var i=0;i<toHide.length;i++){
        toHide[i].hidden = true;
    }
}
function create_cluster( cluster_name ){
    $.get("/createcluster/" + cluster_name, function( data ){
        $('button#'+cluster_name).prop('disabled', true);
    });
}
function update_status(){
    $.post("/sclogupdate", function( data ){
        if(data['status'] == 'updates'){
            try{
                data['clusters'].forEach( function(cluster){
                    clusters_model.get( cluster ).refresh()
                });
            } catch(err) {
                console.log(err);
            }
           show_message( 'Info', data['clusters'].join() + ' have updates');
        }
    });
}

function remove_header( configString ){
    header_patt =  /\<\/ListBucketResult\>/;
    sucky = '</ListBucketResult>';
    var start = 0;
    while (configString.substring(start).search(header_patt) > 0){
        start = configString.substring(start).search(header_patt);
        start += sucky.length;
    }
    return configString.substring(start);
}

function get_startup_log( clusterName){
    var s3 = new AWS.S3;
    var configString = 'None';
    var req = s3.getObject({Bucket:'ndp-adversary', 
        Key: 'logs/sc_startup/' +  g_instance_id + '/' + clusterName + '.log'})
    req.on('error', function(error, response){
        console.log("---------------------------------------------");
        console.log("Error on attempt to retrieve status log for " + clusterName);
        console.log(error);
        console.log(response);
        console.log("---------------------------------------------");
        if (error.name == "NoSuchKey"){ 
            configString = "No log."
            } else {
            configString = error.message;
        }
    $('tr#' + clusterName + '-logs textarea')[0].value = remove_header(configString);
    });
    req.on('success', function(response){
        testing_var = response;
        console.log(response);
        configString = response.data.Body.toString();
    $('tr#' + clusterName + '-logs textarea')[0].value = remove_header(configString);
    });
    req.send();
}
//onload functions
$(function (){
setInterval( function(){
    update_status();
}, 15*1000);
 
$('button#config-button').click( function(event){
    var sb = $('input#spot_bid').val().trim();
    var cp = $('input#cluster_prefix').val().trim();
    var ct = $('#cluster_type option:selected').val();
    var re = $('#region option:selected').val();
    var sm = $('input#force_spot_master').prop('checked')
    var mess = {'cluster_type': ct,
     'force_spot_master': sm,
     'region': re,
     'cluster_prefix': (cp) ? cp : 'na',
     'spot_bid': (sb) ? sb : 'na',
    };
    var posting = $.post( g_scgenerate_url , mess );
    posting.done( function( data ){
        //console.log(data);
        if (data['status'] == 'error'){
            show_message('Error',data['error']);
        } else {
            if( data['status'] == 'success' ){
                var cluster = new ClusterModel(
                    { cluster_name : data['cluster_name'] });
                cluster.fetch({ success : function(){
                    clusters_model.add( cluster );
                }});
            }
            //show_message('Info', data['info']);
        }
    });
})
  set_cluster_default($('#cluster_type option:selected').val());
  $('select#cluster_type').change( function(){
    set_cluster_default(
          $('select#cluster_type option:selected').val()
        );
  });

});
