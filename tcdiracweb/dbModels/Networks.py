from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection
from pynamodb.attributes import UnicodeAttribute, UnicodeSetAttribute
from pynamodb.models import Model

class SourceIndex( GlobalSecondaryIndex ):
    read_capacity_units = 2
    write_capacity_units = 1
    projection = KeysOnlyProjection()
    source = UnicodeAttribute( hash_key=True )
    name = UnicodeAttribute( range_key=True )

class Network( Model ):
    table_name = 'network'
    name = UnicodeAttribute( hash_key=True )
    source = UnicodeAttribute( default='' )
    information_uri = UnicodeAttribute( default='')
    geneIds = UnicodeSetAttribute( default=[] )
    source_index = SourceIndex()

if __name__ == "__main__":
    if not Network.exists():
        Network.create_table(read_capacity_units=2, write_capacity_units=1, wait=True)

