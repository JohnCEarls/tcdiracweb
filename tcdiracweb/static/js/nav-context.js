function add_context( context_specific ){
    console.log('add_context');
    var template = _.template( $('#page-specific-link').html() );
    var outputHtml = template( context_specific );
    $('ul#page-specific-dd').append(outputHtml);
}

function get_context(){
    console.log('get_context');
    var cm_match = new RegExp("\/cm\/");
    if( cm_match.test(document.URL) ){
        return "cm";
    }
    return "general";
}

function set_context_label( label ){
    $('span#context_label').html(label);
}

function set_context(){
    console.log('context function');
    switch( get_context() ){
        case "cm":
            set_context_label('Cluster Opt.');
            add_context(
                { 
                    link: '/cm/managedefaultworker',
                    text: 'Default Cluster Settings'
                });
            add_context( {
                link: '/cm/managerun',
                text: 'Configure Run'
            });
            break;
        case "general":
            set_context_label('General Opt.');
            break;
        default:
            break;
    }
}
$(function(){
    set_context();
});
