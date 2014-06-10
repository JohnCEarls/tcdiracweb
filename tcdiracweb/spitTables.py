from tcdiracweb.utils import maketsv
import masterdirac.models.run as run_mdl
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
import os
import os.path

from multiprocessing import Pool

class NetworkInfo(Model):
    class Meta:
        table_name = 'net_info_table'
    src_id = UnicodeAttribute(hash_key=True)
    pw_id = UnicodeAttribute(range_key=True)
    broad_url=UnicodeAttribute(default='')
    gene_ids=UnicodeAttribute(default='')


runs = run_mdl.get_ANRun()

def writeit( r):
    try:
        if r['run_id'] in ['b6-q111-kegg', 'fvb-analysis1']:
            return 
        if r['status'] == run_mdl.COMPLETE:
            print r['run_id']
        net_table = r['network_config']['network_table']
        net_source_id = r['network_config']['network_source']
        source_dataframe = r['dest_data']['dataframe_file']
        metadata_file = r['dest_data']['meta_file']
        source_bucket = r['dest_data']['working_bucket']
        app_path = '/home/sgeadmin/temp'
        data_path = 'data'

        for rank in [True, False]:
            for p in  NetworkInfo.query(net_source_id):
                try:
                    TSV = maketsv.TSVGen( net_table, net_source_id, source_dataframe, metadata_file, app_path, source_bucket, data_path)
                    t = TSV.genNetworkGeneExpTables( p.pw_id, rank )

                    for strain in t.keys():
                        if type(t[strain]) is dict:
                            for allele in t[strain].keys():
                                current = t[strain][allele]
                                dp = '/home/sgeadmin/temp/forjocelyn/%s/%s/%s/%s' % (
                                        r['run_id'], net_source_id, p.pw_id, allele)
                                try:
                                    os.makedirs( dp )
                                except:
                                    print "Cannot make dp"
                                    pass
                                if rank:
                                    fname = 'rank.csv'
                                else:
                                    fname = 'exp.csv'
                                with open(os.path.join(dp, 'age-'+fname), 'w') as f:
                                    f.write(p.pw_id + ',' + ','.join( map(str, current['ages']) ) + '\n' )
                                    for i,gene in enumerate(current['genes']):
                                        f.write( gene )
                                        for row in current['table']:
                                            f.write(',')
                                            f.write(str(row[i]))
                                        f.write('\n')
                                print "wrote %s" % os.path.join(dp, 'age-'+fname)
                except Exception as e:
                    print e
                    pass
    except Exception as e:
        print "ERROR"
        print r

p = Pool(8)
p.map(writeit, runs)
