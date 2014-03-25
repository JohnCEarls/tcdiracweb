import logging
class Config(object):
    DEBUG = False
    TESTING = False
    SOURCE_DATA_BUCKET='hd_working_0'
    DEFAULT_NET_TABLE='net_info_table'
    STARCLUSTER_KEY_LOCATION = '/home/sgeadmin'
    GOOGLE_ID = '580557226207-ukigt720g3834henmlj546ucld47elnk.apps.googleusercontent.com'
    GOOGLE_SECRET = 'G4QqN3B6Skock2eNiJfEk527'
    LOGGING_LEVEL = logging.INFO


class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
