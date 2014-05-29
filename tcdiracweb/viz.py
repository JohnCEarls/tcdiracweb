from flask import Blueprint, Response, make_response
from flask import jsonify, abort, current_app
from flask import render_template, flash, request

from tcdiracweb.utils.app_init import crossdomain, secure_page,secure_json, check_id

from tcdiracweb.utils.common import json_prep

import json
import boto

viz = Blueprint('viz', __name__, template_folder = 'templates', static_folder = 'static')

@viz.route('/netresults')
def show_net_results():
    return render_template('network_results.html')

@viz.route('/netresultsfordisplay')
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

@viz.route("/pvals",methods=['GET'])
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
    current_app.logger.warning(str(cutoffs))
    current_app.logger.warning(table.columns)
    for k,v in cutoffs.iteritems():
        #valid.append( table[table[k] >= v[request.form['alpha']]['network'].to_list() )
        valid += table[table[k] <= v['0.05']]['networks'].tolist()
        current_app.logger.warning(len(set(valid)))
    table = table.set_index('networks')

    trimmed = np.log10(table.loc[list(set(valid)), :])
    if output_format == 'backgrid':
        return Response( json.dumps(tsv.dataframe_to_backgrid(trimmed)), 
                mimetype='application/json')


    res = "{'table': %s, 'cutoffs': %s}" %(  trimmed.to_json(orient='split'), json.dumps(cutoffs) )
    return  Response( trimmed.to_json(orient='split'), mimetype='application/json')

@viz.route('/expression',methods=['GET'])
def get_expression():
    run_id = request.form['run_id']
    timestamp = request.form['timestamp']
    pathway = request.form['pathway']
    by_rank = request.form['by_rank']
    result = maketsv.get_expression_from_run(run_id, timestamp, pathway, by_rank)
    return jsonify( result )

@viz.route('/comparegenes/<pathway_id>')
def genedifference( pathway_id ):
    return render_template('differencechart.html', pathway_id=pathway_id)

