//helper functions
function add_cluster( cluster ){
  c = '<tr class="';
  if( cluster['active'] == 0 ){
        c += 'warning"';
  } else {
        c += 'success"';
  }
  c+= '" id="' + cluster['cluster_name'] +'" ';
  c+= '>';
  c+= '<td id="cluster_name">';
  c+= cluster['cluster_name'];
  c+= '</td>';
  c+= '<td id="cluster_type">';
  c+= cluster['cluster_type'];
  c+= '</td>';
  c+= '<td id="region">'
  c+= cluster['region'];
  c+=  '<span class="badge">' + cluster['num_nodes'] + '</span>';
  c+= '</td>';
  c+= '<td><button id="' + cluster['cluster_name'] + '" class="btn';
  c+= ' btn-default btn-sm" onclick="create_cluster(';
  c+= '\''+ cluster['cluster_name'] +'\')">Start</button></td>';
  c+= '<td id="status-' + cluster['cluster_name'] + '" >';
  c+= '<textarea id="ssh-cmd-' + cluster['cluster_name'];
  c+= '">';
  c+= '~/.local/bin/starcluster -c ';
  c+= 'https://price.adversary.us/scconfig/' + cluster['master_name'];
  c+= '/' + cluster['cluster_name'];
  c+= ' sshmaster -u sgeadmin ' + cluster['cluster_name'];
  c+= '</textarea>';
  c+= '</td>';
  c+= '<td id="info-glyph">';
  c+= '<span class="'
  c+= "glyphicon glyphicon-info-sign"
  c += '" onclick="toggleLog(';
  c+= "'" + cluster['cluster_name'] + "'";
  c +=  ') " ></span>';
  c+= '</td>';
  c+= '</tr>';
  c+= '<tr id="';
  c+= cluster['cluster_name'] + '-logs" class="log-row" >';
  c+= "<td colspan='7'><textarea class='logs' name='" + cluster['cluster_name'] + '-logs';
  c+= "'></textarea></td></tr>";
  return c;
}

function toggleLog( cname ){
  row =  $('tr#' + cname + '-logs');
  for(var i=0; i< row.length; i++){
      row[i].hidden = !row[i].hidden;
  }
}

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

function get_table(){
    var dynamodb = new AWS.DynamoDB();
    var adversary_atts = ['master_name', 'cluster_name', 'num_nodes', 
    'cluster_type','region', 'active'];
    params = {'TableName':'sc-adversary-config',
      'AttributesToGet':adversary_atts,
      'ScanFilter': {  "master_name":
                    {'AttributeValueList':[ {"S": g_instance_id  } ],
                            "ComparisonOperator": "EQ"
                        }
                    },
    };
    var scan_results = []
    dynamodb.scan(params, function (err, data) {
    if (err) {
      if (err.statusCode != '200'){
       show_message( 'Error', '(' + err.statusCode + ': AWS)'+
       err.message )
    }
       console.log(err); // an error occurred
    } else {
    console.log(data); // successful response
    items = data.Items;
    items.forEach( function( item ){ 
      cluster = Object();
      adversary_atts.forEach( function(att){
          try{
              var my_att = '';
              if (item[att].N){
                  my_att = item[att].N;
              } else if (item[att].S ){
                  my_att = item[att].S;
              }
              cluster[att] = my_att;
              console.log( my_att );
              } catch(err) {
                console.log(err);
            }
        });
        scan_results.push(cluster);
    });
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
    });
}

function create_cluster( cluster_name ){
    $.get("/createcluster/" + cluster_name, function( data ){
        $('button#'+cluster_name).prop('disabled', true);
    });
}
function update_status(){
    $('a#update-status').prop('disabled', true);
    $.post("/sclogupdate", function( data ){
        if(data['status'] == 'updates'){
           show_message( 'Info', data['clusters'].join() + ' have updates');
        } else {
           show_message( 'Info', 'No updates');
        }
        $('update_status').prop('disabled', false);
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
        console.log(data);
        if (data['error']){
            show_message('Error',data['error']);
            } else {
            show_message('Info', data['info']);
            $('tbody#cluster-body').empty();
            get_table();
        }
    });
})
get_table();
$("#cluster-table").tablesorter();
//context specific functions
$('ul#page-specific-dd').append('<li><a href="#" id="update-status" onclick="update_status()">Update Status</a></li>')


  set_cluster_default($('#cluster_type option:selected').val());
  $('select#cluster_type').change( function(){
    set_cluster_default(
          $('select#cluster_type option:selected').val()
        );
  });

});
