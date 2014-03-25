from flask import Flask, redirect, url_for, session
from flask import request, jsonify, render_template, flash, abort, Response
from werkzeug.security import generate_password_hash, check_password_hash

from tcdiracweb import app

from clustermanagement import cm

import boto.utils
from functools import wraps
import multiprocessing
import logging

import tcdiracweb.utils.app_init
google = tcdiracweb.utils.app_init.get_google( app )

app.logger.setLevel(app.config.get('LOGGING_LEVEL'))
app.register_blueprint( cm, url_prefix='/cm')


from tcdiracweb.utils.app_init import crossdomain, secure_page, check_id
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

@app.route('/netresultsfordisplay')
def get_nets_for_display():
    from datadirac.aggregate import DataForDisplay
    import json
    res =  DataForDisplay.scan()
    rlist = [r.attribute_values for r in res]
    for a in rlist:
        for k,v in a.iteritems():
            if type(v) is set:
                a[k]=list(v)
    if res:
        return Response( json.dumps(rlist), 
                mimetype='application/json')
    else:
        abort(400)

@app.route("/pvals",methods=['GET'])
def get_pvalues():
    import boto
    import tempfile
    import pandas
    import tcdiracweb.utils.maketsv as tsv
    import json
    import numpy as np

    df = 'black_6_go_4-joined-2014.02.20.04:09:56.tsv' #request.form["data_file"]
    bucket = 'ndp-hdproject-csvs' #request.form["data_bucket"]
    output_format = 'backgrid' # request.form["output_format"]
    conn = boto.connect_s3()
    b = conn.get_bucket(bucket)
    k = b.get_key(df)
    with tempfile.TemporaryFile() as fp:
        k.get_contents_to_file(fp)
        fp.seek(0)
        table = pandas.read_csv(fp, sep='\t')
    nv = tsv.NetworkTSV()
    cutoffs = nv.get_fdr_cutoffs( 'black_6_go_4','2014.02.20.04:09:56',[.05] )
    #        request.form["black_6_go_4"], 
    #       request.form["timestamp"], alphas=[request.form['alpha']] )
    valid = []
    app.logger.warning(str(cutoffs))
    app.logger.warning(table.columns)
    for k,v in cutoffs.iteritems():
        #valid.append( table[table[k] >= v[request.form['alpha']]['network'].to_list() )
        valid += table[table[k] <= v['0.05']]['networks'].tolist()
        app.logger.warning(len(set(valid)))
    table = table.set_index('networks')

    trimmed = np.log10(table.loc[list(set(valid)), :])
    if output_format == 'backgrid':
        return Response( json.dumps(tsv.dataframe_to_backgrid(trimmed)), 
                mimetype='application/json')


    res = "{'table': %s, 'cutoffs': %s}" %(  trimmed.to_json(orient='split'), json.dumps(cutoffs) )
    return  Response( trimmed.to_json(orient='split'), mimetype='application/json')
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

@app.route('/expression',methods=['GET'])
def get_expression():
    run_id = request.form['run_id']
    timestamp = request.form['timestamp']
    pathway = request.form['pathway']
    by_rank = request.form['by_rank']
    result = maketsv.get_expression_from_run(run_id, timestamp, pathway, by_rank)
    return jsonify( result )

@app.route('/comparegenes/<pathway_id>')
def genedifference( pathway_id ):
    return render_template('differencechart.html', pathway_id=pathway_id)
