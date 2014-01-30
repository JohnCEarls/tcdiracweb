from tcdiracweb import app
import tcdiracweb.utils.app_init 
import tcdiracweb.utils.user_management as u_man
import logging
from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
from functools import wraps
from werkzeug.security import generate_password_hash, \
             check_password_hash

google = tcdiracweb.utils.app_init.get_google( app )
app.logger.setLevel(logging.DEBUG)


def secure_page(f):
    @wraps(f)
    def decorated_function( *args, **kwargs ):
        if u_man.user_registered(session['user_data']['id']):
            if  u_man.user_active(session['user_data']['id']):
                if check_id():
                    return f(*args, **kwargs)
                else:
                    flash('Credentials corrupted', 'error')
                    return redirect(url_for('logout'))
            else:
                flash('User not active. Contact john.c.earls@gmail.com to activate.', 'warning')
        else:
            flash('Not Registered.  Click Register.')
        return redirect(url_for('login'))
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))


@app.route('/google')
@google.authorized_handler
def authorized(resp):
    if resp is None:
        flash( 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']), 'error')
        return redirect(url_for('login'))
    flash('Logged In.', 'welcome')
    app.logger.debug( str(resp) )
    session['google_token'] = (resp['access_token'], '')
    session['id_token'] = resp['id_token']
    me = google.get('userinfo')
    app.logger.debug(str(google.get('*').data))
    me.data['google_token'] = session['google_token']
    session['user_data'] = { 'name': me.data['name'],
                            'id':  u_man.hash_id( me.data['id'] ),
                            'email':me.data['email'],
                            'picture':me.data['picture']}
    session['user_data']['registered'] = u_man.user_registered(session['user_data']['id'])
    session['user_data']['active'] = u_man.user_active(session['user_data']['id'])
    if session['user_data']['registered'] and not session['user_data']['active']:
        flash("You are registered but not active.", 'info')
    app.logger.debug(str(me.data))
    return redirect(url_for('index'))

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route('/awssqs')
@secure_page
def awssqs():
    if check_id():
        return render_template('awssqs.html')
    else:
        return redirect(url_for('logout'))

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    session.pop('id_token', None)
    session.pop('user_data', None)
    return redirect(url_for('index'))

@app.route('/register')
def register():
    if check_id():
        ud = session['user_data']
        if u_man.add_user( ud['id'], ud['name'], ud['email'] ):
            flash("%s[%s] has been added. Your account will be reviewed and you will be notified upon approval. Contact john.c.earls@gmail.com for assistance." % ( ud['name'], ud['email'] ), 'info' )
        else:
            flash("%s[%s] already exists and has not been activated.  Contact john.c.earls@gmail.com for assistance."  % ( ud['name'], ud['email'] ), 'warning' )
        session['user_data']['registered'] = u_man.user_registered(session['user_data']['id'])
        return redirect(url_for('login'))
    else:
        flash("You need to be logged in before you register")
        return redirect(url_for('logout'))
@app.route('/d3test')
def d3test():
    return render_template('differencechart.html')

def check_id():
    if 'user_data' in session and 'id' in session['user_data']:
        me = google.get('userinfo')
        app.logger.debug( me.data['id'] )
        app.logger.debug(   session['user_data']['id'] )
        return u_man.hash_id( me.data['id'] ) == session['user_data']['id']
    return False


