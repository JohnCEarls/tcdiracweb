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
    current_message = $('div.alert.alert-'+__type_of_message[mtype]);
    if( current_message.length > 0){
        $(current_message[0]).find('strong').after(': ' + message );
    } else {
    m =  '<div class="alert alert-' + __type_of_message[mtype] + ' alert-dismissable">'
    m += '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>'
    m += '<strong>' + type + '</strong>: ' + message +'</div>'
    $('body').prepend(m)
    }
}

function auth_check(){
    $.get('/auth_check')
        .done( function(){
            //hurray, we logged in
            app.sessionActive = true;
        })
        .fail( function(){
            if (confirm("Session timeout.")){
                app.sessionActive = false;
                window.location = '/logout';
            }
        });
}
