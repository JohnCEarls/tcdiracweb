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
            k.get_contents_to_filename( opj( self._local_data_path, fname ) ) 

    def loadData( self ):
        sd = data.SourceData()
        sd.load_dataframe( opj( self._local_data_path,self.df) )
        sd.load_net_info(self._net_table, self._net_source_id )
        mi = data.MetaInfo( opj( self._local_data_path, self.meta ) )
        self._sd = sd
        self._mi = mi

    def gen_bivariate( self, pathway, by_rank=False ):
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
                    sid2 = self._mi.get_sample_ids( strain, a2)
                    ages2 =  [self._mi.get_age( s ) for s in sid2]
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
        print "have networks"
        n = len(self.edge_list)
        self.cross_talk = pandas.DataFrame(np.zeros((n,n)), 
            index=self.edge_list.keys(), columns=self.edge_list.keys())

        ctr = 0
        for index, igeneset in self.edge_list.iteritems():
            if ctr % 100 == 0:
                print "%i of %i" % (ctr, n)
            ctr += 1
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



if __name__ == "__main__":
    base = "/home/earls3/secondary/tcdiracweb/tcdiracweb/static/data"

    #t = TSVGen( base + "/exp_mat_b6_wt_q111.pandas", base + "/metadata_b6_wt_q111.txt")
    #t.genBivariate('HISTONE_MODIFICATION')
    """
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
        print ntsv.get_fdr_cutoffs(k['identifier'], k['timestamp'], alphas=[.05])"""
    
    cm = CrossTalkMatrix()
    """
    ctm =  cm.generate( networks=[('c2.cp.kegg.v4.0.symbols.gmt', 'KEGG_LEISHMANIA_INFECTION'),
        ('c2.cp.biocarta.v4.0.symbols.gmt', 'BIOCARTA_41BB_PATHWAY'), 
        ('c2.cp.biocarta.v4.0.symbols.gmt', 'BIOCARTA_ACTINY_PATHWAY')] )"""
    network = ['KEGG_LEISHMANIA_INFECTION', 'BIOCARTA_41BB_PATHWAY', 'BIOCARTA_ACTINY_PATHWAY']
    print cm.get_crosstalk(network,  bucket='ndp-hdproject-csvs', 
        file_name='crosstalk-biocartaUkeggUgoUreactome-pandas-dataframe.pkl')
