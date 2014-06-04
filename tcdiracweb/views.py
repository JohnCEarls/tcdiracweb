from flask import Flask, redirect, url_for, session

from flask import request, jsonify, render_template, flash, abort, Response
from werkzeug.security import generate_password_hash, check_password_hash
from tcdiracweb import app
import datetime

from clustermanagement import cm
from viz import viz

import boto.utils
from functools import wraps
import multiprocessing
import logging
import json

import tcdiracweb.utils.app_init
google = tcdiracweb.utils.app_init.get_google( app )

app.logger.setLevel(app.config.get('LOGGING_LEVEL'))
app.register_blueprint( cm, url_prefix='/cm')
app.register_blueprint( viz, url_prefix='/viz')


from tcdiracweb.utils.app_init import crossdomain, secure_page, secure_json, check_id
import tcdiracweb.utils.user_management as u_man

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
    app.logger.info( str(resp) )
    session['google_token'] = (resp['access_token'], '')
    session['id_token'] = resp['id_token']
    future = datetime.datetime.now() + datetime.timedelta(seconds=int(resp['expires_in']))
    session['expires'] = future.strftime("%s")
    if 'refresh_token' in resp:
        session['refresh_token'] = resp['refresh_token']
    me = google.get('userinfo')
    me.data['google_token'] = session['google_token']
    app.logger.info(me.data)
    app.logger.info(me.data['id'])
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
            flash(('%s[%s] has been added. Your account will be reviewed '
                'and you will be notified upon approval. '
                'Contact john.c.earls@gmail.com for assistance.')
                % ( ud['name'], ud['email'] ), 'info' )
        else:
            flash(("%s[%s] already exists and has not been activated.  " 
                "Contact john.c.earls@gmail.com for assistance.")
                % ( ud['name'], ud['email'] ), 'warning' )
        session['user_data']['registered'] = u_man.user_registered(
                session['user_data']['id'])
        return redirect(url_for('login'))
    else:
        flash("You need to be logged in before you register")
        return redirect(url_for('logout'))

@app.route('/netresults')
def show_net_results():
    return render_template('network_results.html')
    #jsonify({'table':]}) 
@app.route("/sig_level")
def get_sig_level():
    import tcdiracweb.utils.maketsv as tsv
    run_id = 'black_6_go_4'
    timestamp = '2014.02.20.04:09:56'
    siglevel = [.05]
    nv = tsv.NetworkTSV()
    return jsonify( nv.get_fdr_cutoffs(run_id ,timestamp,siglevel ) )

@app.route('/biv/<net_source_id>/<source_dataframe>/<metadata_file>/<pathway_id>/<restype>')
@app.route('/biv/<net_table>/<net_source_id>/<source_dataframe>/<metadata_file>/<pathway_id>/<restype>')
def get_bivariate( pathway_id, net_source_id, source_dataframe,
        metadata_file, restype = 'expression',
        net_table=app.config['DEFAULT_NET_TABLE'] ):
    import json
    import tcdiracweb.utils.maketsv as tsv
    import os.path
    app.logger.warning( '/'.join([pathway_id, net_source_id, source_dataframe,
        metadata_file, restype, net_table]))
    app_path = os.path.dirname(__file__)
    source_bucket = app.config['SOURCE_DATA_BUCKET']
    data_path =  url_for('static', filename='data')
    t = tsv.TSVGen( net_table, net_source_id, source_dataframe, metadata_file, app_path, source_bucket, data_path)
    try:
        return t.gen_bivariate( pathway_id, by_rank=True )
    except Exception as e:
        app.logger.error( str(e) )
        return json.dumps({'error': str(e)})

@app.route('/auth_check')
@secure_json
def auth_check():
    msg = {'status': 'complete',
            'data': {'authenticated':True}
            }
    status = 200
    return Response( json.dumps( msg ), mimetype='application/json',
                        status = status )
