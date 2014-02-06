function show_message( type, message ){
    __type_of_message = {'error':'danger',
                    'danger':'danger',

                        'warning':'warning',
                            'info':'info',
                            'default':'default'};
    var mtype = 'default'
    if( type.toLowerCase() in __type_of_message){
        mtype =  type.toLowerCase();
    }
    m =  '<div class="alert alert-' + __type_of_message[mtype] + ' alert-dismissable">'
    m += '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>'
    m += '<strong>' + type + '</strong>: ' + message +'</div>'
    $('body').prepend(m)
}
