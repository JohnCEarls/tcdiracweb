from datadirac import data
import itertools
import pandas
from collections import defaultdict
import numpy as np
import os.path
import json
import boto
from boto.s3.key import Key
import cPickle as pickle
import random
import re
import string
import masterdirac.models.run as run_mdl

opj = os.path.join
class TSVGen:
    def __init__(self, net_table, net_source_id, source_dataframe, metadata_file, app_path, source_bucket, data_path):
        self._net_table = net_table
        self._net_source_id = net_source_id
        self.df = source_dataframe
        self.meta = metadata_file
        self._app_path = app_path
        self._data_path = data_path
        self._source_bucket = source_bucket
        self._local_data_path = opj( self._app_path, self._data_path.strip('/') )
        self.getData()
        self.loadData()

    def getData(self):
        self._download_data( self.df )
        self._download_data( self.meta )

    def _download_data(self, fname):
        if not os.path.exists(  opj( self._local_data_path, fname ) ):
            s3 = boto.connect_s3()
            b = s3.get_bucket(self._source_bucket)
            k = Key(b)
            k.key = fname 
            f = self.strip_path( fname )
            k.get_contents_to_filename( opj( self._local_data_path, f ) ) 
    
    def strip_path( self, key_name):
        p, f = os.path.split( key_name )
        return f

    def loadData( self ):
        sd = data.SourceData()
        sd.load_dataframe( opj( self._local_data_path, self.strip_path(self.df)) )
        sd.load_net_info(self._net_table, self._net_source_id )
        mi = data.MetaInfo( opj( self._local_data_path, self.strip_path(self.meta) ) )
        self._sd = sd
        self._mi = mi

    def jitter( self, ages, order=.001):
        """
        Given a list of ages, adjust each randomly by a small amount.
        This is done to make each age unique, if we don't want aggregation.
        """
        return [age + (random.random()*order) for age in ages]

    def gen_bivariate( self, pathway, by_rank=False, jitter=True ):
        genes = self._sd.get_genes( pathway )
        descriptions = []
        web_path = self._data_path 
        by_rank = False
        for i in range(2):
            for strain in self._mi.get_strains():
                alleles = self._mi.get_nominal_alleles( strain )
                for a1, a2 in itertools.combinations(alleles,2):
                    sid1 = self._mi.get_sample_ids( strain, a1)
                    ages1 = [self._mi.get_age( s ) for s in sid1] 
                    if jitter:
                        ages1 = self.jitter(ages1)
                    sid2 = self._mi.get_sample_ids( strain, a2)
                    ages2 =  [self._mi.get_age( s ) for s in sid2]
                    if jitter:
                        ages2 = self.jitter(ages2)
                    sub1 = self._sd.get_expression( sid1 )
                    pw_sub1 = sub1.loc[genes,:]
                    if by_rank:
                        pw_sub1T = pw_sub1.transpose().rank(axis=1, ascending=False)
                    else:
                        pw_sub1T = pw_sub1.transpose()

                    series_1 = {}
                    for gene in genes:
                        a2s_map = defaultdict(list)
                        for a,sid in zip(ages1,sid1):
                           a2s_map[a].append(sid) 
                        new_series = pandas.Series(np.zeros(len(a2s_map)), index=a2s_map.keys()) 
                        for a,samps in a2s_map.iteritems():
                            new_series.ix[a] = pw_sub1T[gene].ix[ samps ].median()
                        new_series.name = "%s" % (a1,)
                        series_1[gene] = new_series

                    sub2 = self._sd.get_expression( sid2 )
                    pw_sub2 = sub2.loc[genes,:]
                    
                    if by_rank:
                        pw_sub2T = pw_sub2.transpose().rank(axis=1, ascending=False)
                    else:
                        pw_sub2T = pw_sub2.transpose()
                    series_2 = {}

                    for gene in genes:
                        a2s_map = defaultdict(list)
                        for a,sid in zip(ages2,sid2):
                           a2s_map[a].append(sid) 
                        new_series = pandas.Series(np.zeros(len(a2s_map)), index=a2s_map.keys()) 
                        for a,samps in a2s_map.iteritems():
                            new_series.ix[a] = pw_sub2T[gene].ix[ samps ].median()
                        new_series.name = "%s" % (a2,)
                        series_2[gene] = new_series
                    avg_rank = 0
                    for gene in genes:
                        a,b = series_1[gene].align(series_2[gene])
                        a = a.interpolate().bfill().ffill()
                        b = b.interpolate().bfill().ffill()
                        q = pandas.DataFrame(a)
                        q = q.join(b)
                        series_1[gene].name = series_1[gene].name + '-true';
                        series_2[gene].name = series_2[gene].name + '-true';
                        q = q.join(series_1[gene]);
                        q = q.join(series_2[gene]);
                        if by_rank:
                            res_type= 'rank'
                        else:
                            res_type='expression'

                        fname = "%s-%s-%s-%s.tsv" % (res_type, strain, gene,  
                                    '-V-'.join(q.columns))
                        q.to_csv(opj(self._local_data_path, fname), sep='\t', 
                            index_label="age", na_rep='null')
                        if by_rank:

                            fname = "%s-%s-%s.tsv" % (strain, gene,  
                                    '-V-'.join(q.columns))
                            description = { 
                                    'filename-rank' : os.path.join(web_path, 'rank-'+fname),
                                    'filename-expression' : os.path.join( web_path, 'expression-' + fname),
                                    'strain': strain,
                                    'gene': gene,
                                    'age' : 'age',
                                    'base' : a1,
                                    'baseLong': a1,
                                    'comp' : a2,
                                    'compLong':a2, 
                                    'avg_rank': a.mean()
                                    }
                            descriptions.append(description)
            by_rank = True
        return json.dumps( sorted( descriptions , key=lambda x: x['avg_rank'] ))

    def genNetworkGeneExpTables(self, pathway, by_rank=False): 
        genes = self._sd.get_genes( pathway )
        web_path = self._data_path 
        rstr = 'rank' if by_rank else 'exp'
        tables = {'type': rstr,
                'pathway': pathway
                }
        for strain in self._mi.get_strains():
            tables[strain] = {}
            alleles = self._mi.get_nominal_alleles( strain )
            for allele in self._mi.get_nominal_alleles( strain ):
                tables[strain][allele] = {}
                sid = self._mi.get_sample_ids( strain, allele)
                ages = [self._mi.get_age( s ) for s in sid] 

                ages = self.jitter(ages)
                sub = self._sd.get_expression( sid )
                pw_sub = sub.loc[genes,:]
           
                s_a_map = dict([(s,a) for s,a in zip( sid, ages )])
                pw_sub.rename( columns=s_a_map, inplace=True )
                pw_sub = pw_sub.reindex_axis(sorted(pw_sub.columns), axis=1)
                if by_rank:
                    pw_subT = pw_sub.transpose().rank(axis=1, ascending=False)
                else:
                    pw_subT = pw_sub.transpose()
                tables[strain][allele]['samples'] = [sn for a,sn in sorted(zip(ages,sid))]
                tables[strain][allele]['ages'] = pw_subT.index.tolist()
                tables[strain][allele]['genes'] = pw_subT.columns.tolist()
                tables[strain][allele]['table'] =  pw_subT.values.tolist()
        return tables

from datadirac.aggregate import DataForDisplay
import tempfile
from datadirac.utils import stat
import boto
from boto.s3.key import Key
class NetworkTSV:
    def __init__( self ):
        pass

    def _available(self):
        res = DataForDisplay.scan()
        results = {}
        for r in res:
            results[r.identifier +'-' +r.timestamp] = r.attribute_values
        return results

    def get_display_info(self, select=[], display_vars=['network', 'description', 'alleles', 'strains'] ):
        always = ['identifier', 'timestamp']
        _vars = always + display_vars;
        result = []
        current = self._available()
        if select:
            for s_id in select:
                if s_id in current:
                    selected = {'id':s_id}
                    for v in _vars:
                        if type( current[s_id][v] ) is set:
                            selected[v] = list( current[s_id][v] )
                        else:
                            selected[v] = current[s_id][v]
                    result.append(selected)
        else:
            for s_id in current.keys() :
                if s_id in current:
                    selected = {'id':s_id}
                    for v in _vars:
                        if type( current[s_id][v] ) is set:
                            selected[v] = list( current[s_id][v] )
                        else:
                            selected[v] = current[s_id][v]
                    result.append(selected)
        return result

    def set_qval_table( self, identifier, timestamp ):
        res = DataForDisplay.get(identifier, timestamp)
        s3 = boto.connect_s3()
        bucket = s3.get_bucket( res.data_bucket )
        k = bucket.get_key( res.data_file )
        with tempfile.TemporaryFile() as fp:
            k.get_contents_to_file(fp)
            fp.seek(0)
            qv = stat.get_qval_table(fp)
        with tempfile.TemporaryFile() as fp2:
            qv.to_csv( fp2, sep='\t', index_label='networks' )
            fp2.seek(0)
            k = Key(bucket)
            k.key = 'qvals-' + identifier + '-' + timestamp + '.tsv'
            k.set_contents_from_file(fp2)
        res.qvalue_file = 'qvals-' + identifier + '-' + timestamp + '.tsv'
        res.save()


    def get_fdr_cutoffs( self, identifier, timestamp, alphas=[.05]):
        """
        By benjamini-hochberg
        """
        res = DataForDisplay.get(identifier, timestamp)
        s3 = boto.connect_s3()
        bucket = s3.get_bucket( res.data_bucket )
        k = bucket.get_key( res.data_file )
        with tempfile.TemporaryFile() as fp:
            k.get_contents_to_file(fp)
            fp.seek(0)
            res = stat.get_fdr_cutoffs(fp, alphas=alphas)
        return res

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute

class NetworkInfo(Model):
    table_name = 'net_info_table'
    src_id = UnicodeAttribute(hash_key=True)
    pw_id = UnicodeAttribute(range_key=True)
    broad_url=UnicodeAttribute(default='')
    gene_ids=UnicodeAttribute(default='')

class CrossTalkMatrix:
    """
    Dataframe where df[a,b] says what percent of a is shared with b
    """
    def __init__(self):
        self.edge_list = defaultdict(set)

    def generate(self, networks=[]):
        """
        networks is a list of tuples (src_id, pw_id)
        """
        
        if networks:
            for item in NetworkInfo.batch_get(networks):
                self.add_item( item )
        else:
            for item in NetworkInfo.scan():
                self.add_item(item)
        n = len(self.edge_list)
        self.cross_talk = pandas.DataFrame(np.zeros((n,n)), 
            index=self.edge_list.keys(), columns=self.edge_list.keys())

        for index, igeneset in self.edge_list.iteritems():
            for column, ggeneset in self.edge_list.iteritems():
                self.cross_talk.at[index, column] = len(igeneset.intersection( ggeneset )) / float(len(igeneset))
        return self.cross_talk

    def add_item(self, item ):
        net_string = item.gene_ids
        self.edge_list[item.pw_id] = set(net_string[6:].strip().split('~:~'))

    def read_pickle(self, file_name):
        self.cross_talk = pandas.read_pickle(file_name)

    def get_crosstalk(self, networks, bucket=None, file_name=None):
        if not bucket:
            return self.generate( networks )
        else:
            conn = boto.connect_s3()
            b = conn.get_bucket(bucket)
            k = b.get_key(file_name)
            with tempfile.SpooledTemporaryFile() as f:
                k.get_contents_to_file(f)
                f.seek(0)
                self.cross_talk = pickle.load(f)
            if not isinstance(networks[0], basestring):
                networks = [n for _,n in networks]
            return self.cross_talk.loc[networks, networks]

from datadirac.aggregate import RunGPUDiracModel, DataForDisplay
import base64
import json
import pprint
import boto
import tempfile
import pandas
import json
import numpy as np

def get_sig(run_id, sig_level = .05):
    """
    Returns the significant networks at the given significance by 
    Benjamini-Hochberg
    """
    myitem = None
    for item in DataForDisplay.query(run_id):
        if not myitem:
            myitem = item
        elif myitem and item.timestamp > myitem.timestamp:
            myitem = item
    bucket = myitem.data_bucket
    pv_file = myitem.data_file
    conn = boto.connect_s3()
    b = conn.get_bucket(bucket)
    k = b.get_key(pv_file)
    with tempfile.TemporaryFile() as fp:
        k.get_contents_to_file(fp)
        fp.seek(0)
        table = pandas.read_csv(fp, sep='\t')
    nv = NetworkTSV()
    cutoffs = nv.get_fdr_cutoffs( myitem.identifier, myitem.timestamp, [sig_level] )
    valid = []
    for k,v in cutoffs.iteritems():
        for cut in v.itervalues():
            valid += table[table[k] <= cut]['networks'].tolist()
    return list(set(valid))

def dumpExpression():
    runs = {}
    ignore = ['black_6_go_wt_v_q111']
    for item in RunGPUDiracModel.scan():
        if item.run_id not in ignore:
            runs[item.run_id] =  json.loads(base64.b64decode( item.config ))
    for k in runs.keys():
        net_table = runs[k]['network_config']['network_table']
        net_source_id = runs[k]['network_config']['network_source']
        source_dataframe = runs[k]['dest_data']['dataframe_file']
        metadata_file = runs[k]['dest_data']['meta_file']
        source_bucket = runs[k]['dest_data']['working_bucket']
        app_path = '/home/sgeadmin/.local/lib/python2.7/site-packages/tcdiracweb-0.1.0-py2.7.egg/tcdiracweb'
        data_path = 'static/data'
        runs['tsvargs'] = (net_table, net_source_id, source_dataframe, metadata_file, app_path, source_bucket, data_path)
        runs['sig_nets'] = get_sig(k)
        t = TSVGen( *runs['tsvargs'] )
        for pw in runs['sig_nets']:
            for rank in [True,False]:
                for j in [True,False]:
                    print t.genNetworkGeneExpTables(pw,  by_rank=rank)
                    return
            print pw

def get_expression_from_run( run_id, pathway, by_rank ):
    res = RunGPUDiracModel.get( run_id, timestamp )
    config = json.loads(base64.b64decode( res.config ))
    net_table = config['network_config']['network_table']
    net_source_id = config['network_config']['network_source']
    source_dataframe = config['dest_data']['dataframe_file']
    metadata_file = config['dest_data']['meta_file']
    source_bucket = config['dest_data']['working_bucket']
    app_path = '/home/sgeadmin/.local/lib/python2.7/site-packages/tcdiracweb-0.1.0-py2.7.egg/tcdiracweb'
    data_path = 'static/data'
    args =  (net_table, net_source_id, source_dataframe, metadata_file, 
            app_path, source_bucket, data_path)
    tsv = TSVGen( * args )
    return t.genNetworkGeneExpTables( pathway, by_rank=by_rank )

def dataframe_to_backgrid( dataframe, type_map={}, sorter=None ):
    columns = []
    index_name = dataframe.index.name
    def df2bgtype( column ):
        dftype = column.dtype
        name = column.name
        if name in type_map:
            return type_map[name]
        if dftype == object:
            return 'string'
        elif dftype == int:
            return 'integer'
        elif dftype == float:
            return 'number'
    
    def pretty_name( ugly_name ):
        prettier = ' '.join(re.split( r'[_-]', ugly_name))
        return string.capwords( prettier )
        
    columns.append({ 'name':'id',
        'label': index_name if index_name else 'Index',
        'editable': False,
        'cell' : df2bgtype(dataframe.index)
        })
    for i in range(len(dataframe.columns)):
        columns.append({'name': dataframe.iloc[:,i].name,
            'label': pretty_name(dataframe.iloc[:,i].name),
            'cell': df2bgtype( dataframe.iloc[:,i] )
                        })
    table = []
    for indx in dataframe.index:
        row = {'id':indx}
        for col in dataframe.columns:
            row[col] = dataframe.at[indx,col]
        table.append(row)

    return { 'columns' : columns, 'table': table }


if __name__ == "__main__":
    dumpExpression()
    """
    base = "/home/earls3/secondary/tcdiracweb/tcdiracweb/static/data"

    #t = TSVGen( base + "/exp_mat_b6_wt_q111.pandas", base + "/metadata_b6_wt_q111.txt")
    #t.genBivariate('HISTONE_MODIFICATION')
    conn = boto.connect_s3()
    bucket = conn.get_bucket('ndp-hdproject-csvs')
    k = Key(bucket)
    k.key = 'crosstalk-biocartaUkeggUgoUreactome-pandas-dataframe.pkl'
    k.set_contents_from_filename('ct.pkl')"""
    """
    ntsv = NetworkTSV()
    di =  ntsv.get_display_info()
    for k in di:
        print ntsv.set_qval_table(k['identifier'], k['timestamp'])
        print ntsv.get_fdr_cutoffs(k['identifier'], k['timestamp'], alphas=[.05])
    
    cm = CrossTalkMatrix()
    ctm =  cm.generate( networks=[('c2.cp.kegg.v4.0.symbols.gmt', 'KEGG_LEISHMANIA_INFECTION'),
        ('c2.cp.biocarta.v4.0.symbols.gmt', 'BIOCARTA_41BB_PATHWAY'), 
        ('c2.cp.biocarta.v4.0.symbols.gmt', 'BIOCARTA_ACTINY_PATHWAY')] )
    network = ['KEGG_LEISHMANIA_INFECTION', 'BIOCARTA_41BB_PATHWAY', 'BIOCARTA_ACTINY_PATHWAY']
    print cm.get_crosstalk(network,  bucket='ndp-hdproject-csvs', 
        file_name='crosstalk-biocartaUkeggUgoUreactome-pandas-dataframe.pkl')"""
