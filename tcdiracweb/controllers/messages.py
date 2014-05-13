import masterdirac.models.systemdefaults as sys_def
from tcdiracweb.utils.common import json_prep
import boto.sqs 
import json
class Console:
    """
    Gets messages for the console from master
    """
    def __init__(self, current_app):
        self.app = current_app
        self.logger = current_app.logger
        self._mess_flter = {}

    def GET( self ):
        launcher_config = sys_def.get_system_defaults(
                setting_name = 'launcher_config',component= 'Master')
        message_q = launcher_config['launcher_sqs_out']
        conn = boto.sqs.connect_to_region('us-east-1') 
        q = conn.create_queue( message_q )
        messages = q.get_messages( 10 )
        outbound = []
        while messages:
            for message in messages:
                message_body = message.get_body()
                message_dict = json.loads( message_body )
                self.logger.info( 'Message Rec\'d [%s]' % message_body )
                if 'recipient' not in message_dict:
                    #garbage message
                    q.delete_message( message )
                elif message_dict['recipient'] == 'console':
                    #message for this element
                    if not self._dup( message_dict['message'] ):
                        outbound.append( message_dict['message'] )
                    q.delete_message( message )
            messages = q.get_messages( 10 )
        msg = {'status':    'complete',
                'data' : [json_prep(m) for m in outbound]}
        status = 200
        return  (msg, status)

    def _dup(self, mess):
        """
        Check that we are not seeing the same message
        """
        ignore = ['timestamp']
        m = hashlib.md5()
        for k,v in mess.iteritems():
            if k not in ignore:
                m.update(v)
        _hash = m.hexdigest()
        if _hash not in self._mess_flter:
            self._mess_flter[_hash] = 1
            return False
        else:
            return True

