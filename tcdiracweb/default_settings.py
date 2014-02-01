class Config(object):
    DEBUG = False
    TESTING = False
    SOURCE_DATA_BUCKET='hd_working_0'
    DEFAULT_NET_TABLE='net_info_table'

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
