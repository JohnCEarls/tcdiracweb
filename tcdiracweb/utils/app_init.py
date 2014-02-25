from flask_oauthlib.client import OAuth
from flask import Flask, redirect, url_for, session, request, jsonify, \
        render_template, flash, abort, Response
from functools import wraps
from tcdiracweb import app

def get_google( app ):
    app.config['GOOGLE_ID'] =  '580557226207-ukigt720g3834henmlj546ucld47elnk.apps.googleusercontent.com' 
    app.config['GOOGLE_SECRET'] = 'G4QqN3B6Skock2eNiJfEk527'
    oauth = OAuth(app)
    google = oauth.remote_app(
        'google',
        consumer_key=app.config.get('GOOGLE_ID'),
        consumer_secret=app.config.get('GOOGLE_SECRET'),
        request_token_params={
            'scope': ['profile', 'https://www.googleapis.com/auth/userinfo.email']          
        },
        base_url='https://www.googleapis.com/oauth2/v1/',
        request_token_url=None,
        access_token_method='POST',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
    )
    return google

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

import tcdiracweb.utils.user_management as u_man
import tcdiracweb.views 
def secure_page(f):
    @wraps(f)
    def decorated_function( *args, **kwargs ):
        app.logger.warning( dir(f) )
        if 'user_data' not in session:
            flash('Credentials corrupted', 'error')
            return redirect(url_for('logout'))
        if u_man.user_registered(session['user_data']['id']):
            if  u_man.user_active(session['user_data']['id']):
                if tcdiracweb.views.check_id():
                    return f(*args, **kwargs)
                else:
                    flash('Credentials corrupted', 'error')
                    return redirect(url_for('logout'))
            else:
                flash(('User not active. Contact john.c.earls@gmail.com' 
                ' to activate.'), 'warning')
        else:
            flash('Not Registered.  Click Register.')
        return redirect(url_for('login'))
    return decorated_function

