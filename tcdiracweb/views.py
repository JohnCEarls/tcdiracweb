from tcdiracweb import app
import tcdiracweb.utils.app_init
import tcdiracweb.utils.user_management as u_man
import logging
from flask import Flask, redirect, url_for, session, request, jsonify, render_template, flash
from functools import wraps
from werkzeug.security import generate_password_hash, \
             check_password_hash
import multiprocessing


google = tcdiracweb.utils.app_init.get_google( app )
app.logger.setLevel(logging.DEBUG)
import boto.utils

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

@app.route('/comparegenes/<pathway_id>')
def genedifference( pathway_id ):
    return render_template('differencechart.html', pathway_id=pathway_id)

@app.route('/clustermain')
@secure_page
def clustermain():
    instance_id =  boto.utils.get_instance_identity()['document']['instanceId']
    return render_template('clustermain.html', instance_id=instance_id)

@app.route('/createcluster', methods=['POST','GET'])
def scgenerate_config():
    app.logger.debug(repr(request))
    from tcdiracweb.utils.starclustercfg import AdversaryMasterServer
    if request.method == 'POST':
        allowed = ['cluster_size', 'cluster_prefix', 'region', 'availability_zone','spot_bid']
        args = {}
        for k, v in request.form.iteritems():
            if k in allowed and v != 'na' and k != 'cluster_type':
                args[k] = str(v.strip())
        if 'force_spot_master' in request.form and request.form['force_spot_master'] == 'true':
            args['force_spot_master'] = True
        else:
            args['force_spot_master'] = False
        ms = AdversaryMasterServer()
        app.logger.debug( str(args) )
        app.logger.debug( str(request.form))
        if request.form['cluster_type'] == 'data':
            ms.configure_data_cluster(**args)
        elif request.form['cluster_type'] == 'gpu':
            ms.configure_gpu_cluster(**args)
        return jsonify({'info':'Config generation complete'});

@app.route('/createcluster/<cluster_name>')
def create_cluster( cluster_name ):
    from tcdiracweb.utils import starclustercfg
    s_bin = '/home/sgeadmin/.local/bin/starcluster'
    url =  'https://price.adversary.us/scconfig'
    instance_id =  boto.utils.get_instance_identity()['document']['instanceId']
    master_name = instance_id 
    args = (s_bin, url, master_name, cluster_name)
    p = multiprocessing.Process(target=starclustercfg.run_sc, args=args)
    p.start()
    return jsonify({'master_name':master_name, 'cluster_name': cluster_name, 'pid':p.pid})

@app.route('/scconfig/<master_name>/<cluster_name>')
def scget_config(master_name, cluster_name):
    from utils.starclustercfg import AdversaryServer, SCConfigError
    try:
        ams = AdversaryServer(master_name, cluster_name, no_create=True )
        return ams.config + render_template('sc-plugins.cfg') + \
            render_template('sc-security-group.cfg')
    except SCConfigError as scce:
        return  jsonify({'error': scce.message})

@app.route('/sclogupdate')
def sc_log_update():
    from tcdiracweb.utils import starclustercfg
    runs = starclustercfg.log_sc_startup()
    if runs:
        return jsonify({'status': 'updates', 'clusters': runs})
    else:
        return jsonify({'status': 'unchanged'})

def check_id():
    if 'user_data' in session and 'id' in session['user_data']:
        me = google.get('userinfo')
        if 'id' in me.data:#server reboot fubars this, just log user out
            app.logger.debug( me.data['id'] )
            app.logger.debug(   session['user_data']['id'] )
            return u_man.hash_id( me.data['id'] ) == session['user_data']['id']
    return False


