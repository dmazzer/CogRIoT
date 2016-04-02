
""" 
zmqPub.py: CogRIoT ZMQ Publish helper function

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"

import zmq
from Logger import Logger

class zmqDissInfo():
    def __init__(self, listener_address):
        '''
        Create class to disseminate information using ZMQ protocol 
        '''
        logger = Logger()
        if listener_address is None:
            logger.error("listener_address cannot be null")
            SystemExit()
            
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(listener_address)
        
    def SendMessage(self, msg):
        #ts = datetime.now()
        #fmtmsg = str(ts) + ',' + msg
        fmtmsg = msg
        self.socket.send_json(fmtmsg)
        
        
