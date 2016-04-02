
""" 
zmqpuller.py: CogRIoT SISA ZMQ puller 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


import zmq
import threading

import sys
sys.path.append("../../")
from utils.logmsgs.logger import Logger

class ZMQPuller():
    def __init__(self, userDAO, zmqpull_address):
        '''
        Receives the userDAO, and ZMQ socket information
        
        This class starts a thread that receive samples from CentralOffice and
        store the received data in database.
        '''
        context = zmq.Context()
        # recieve work
        self.consumer_receiver = context.socket(zmq.PULL)
        self.consumer_receiver.connect(zmqpull_address)
        
        self.dao = userDAO

        # starting thread work thread
        workThread = threading.Thread(name='ZMQPullerWork', target=self.pullwork)
        workThread.daemon = True
        workThread.start()
        Logger().log("SIS ZMQ puller thread started.")

    
    def pullwork(self):
        while True:
            sensing_json_string = self.consumer_receiver.recv_json()
#             self.dao.insert(sensing_json_string['cellid'], sensing_json_string)
            self.dao.insert('blob', sensing_json_string)
