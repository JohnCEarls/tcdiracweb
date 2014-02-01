function gene_info( hdr ){
qstring = 'http://mygene.info/v2/query?q=' + hdr.gene;
$('#gene-info').empty()
$.getJSON(qstring)
  .done( function( data ){
    $('#gene-info').empty(); 
    var set = {};
    var msg = '<ul class="list-group" id="gene-info-list">';
    data.hits.forEach(function( element, index, array){
      if (!(element.entrezgene in set) && element.entrezgene){
        set[element.entrezgene] = true;
        //console.log(element);
        msg += '<li class="list-group-item">';
        msg += '<a href = "http://www.ncbi.nlm.nih.gov/gene';
        msg += '?cmd=Retrieve&dopt=full_report&list_uids=';
        msg += element.entrezgene;
        msg += '">';
        msg += element.name; 
        msg += '</a>';
        msg += '</li>';
      }
    });

    msg += '</ul>';
    $('#gene-info').append(msg); 
  })
  .fail( function( jqxhr, textStatus, error )
    {
      $('body').append(
        '<div class="alert alert-warning alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" ' +
        'aria-hidden="true">&times;</button>' +
        '<strong>Warning</strong>Unable to load information for ' + hdr.gene + 
        '</div>'
      );
    });
}

function gene_button( hdr, index, array){
  d = document.createElement('div');
  $(d).addClass('btn btn-default')
    .html(hdr.gene)
    .attr('data-info', hdr)
    .attr('id', hdr.gene)
    .appendTo( $('div#gene-choosers') )
    .click( function(){
        $('svg#d3svg').empty();
        current_gene_element = index;
        comparison_graph(hdr);
        var tstring =  hdr.gene + ": <small>Comparing " + hdr.type + " between " + hdr.base + "(black line) and " + hdr.comp + "</small>";
        $('#expression-title').html( tstring );
        gene_info(hdr);
    });
}
