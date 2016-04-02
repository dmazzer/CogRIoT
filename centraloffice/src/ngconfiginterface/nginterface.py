""" 
nginterface.py: NovaGenesis Interface

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Antonio Marcos Alberti"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"

import sys
import zmq
import threading
from bzrlib.plugins.launchpad.lp_api_lite import json

sys.path.append("../../")
from utils.logmsgs import logger

class NGInterface():
    '''
    Provide interface communication between CellController and NovaGenesis
    to exchange configuration parameters with NovaGenesis  
    '''
    
    def __init__(self, config, ng_local_address, ng_remote_address):
        '''
        Constructor
        Receives pull and push zmq socket address
        Also receives the instance of the class that access the oppened configuration file.
        '''

        #TODO: implement the threads (timers) to listen and to publish messages to/from novagenesis
        #TODO: Parse and return configuration changes to CellController
        #TODO: CellController must apply config changes

        self.logger = logger.Logger()

        self.logger.log('NovaGenesis interface - Starting')

        self.config = config

        contextPull = zmq.Context()
        # recieve socket
        self.consumer_receiver = contextPull.socket(zmq.PULL)
        self.consumer_receiver.connect(ng_remote_address)

        contextPush = zmq.Context()
        # transmit socket
        self.consumer_sender = contextPush.socket(zmq.PUSH)
        self.consumer_sender.bind(ng_local_address)
        
        # starting thread work thread
        workThread = threading.Thread(name='NGZMQPullerWork', target=self.ZMQPuller)
        workThread.daemon = True
        workThread.start()
        self.logger.log("NovaGenesis interface ZMQ puller thread started.")
    
        self.logger.log('NovaGenesis interface - Started')
        
    
    def setConfiguration(self, Configuration):
        self.logger.log('[NG-CommandParser] You should implement this feature some time')
        return 'ack'
    

    def getInformation(self):
        strout = {'capacities':
                    {
                        'sensing_freq_min': '100000000' ,
                        'sensing_freq_max': '1800000000',
                        'sensing_bw_min': '1024000',
                        'sensing_bw_max': '2048000',
                        'sensing_sectors': '1',
                        'sensing_direction': '0',
                    },
                    'cell_info':
                    {
                        'cellcontroller_id': self.config.cellcontroller_id ,
                        'cellcontroller_location': self.config.cellcontroller_location
                    },
                    'current_config':
                    {
                        'sensing_freq_start': [str(self.config.sensing_start_freq), "-1" ], 
                        'sensing_freq_stop': [str(self.config.sensing_stop_freq), "-1"],
                        'sensing_bw': str(self.config.sensing_band_width),
                    }
               }
        return strout

    def CommandParser(self, ReceivedCommand):
        self.logger.log('[NG-CommandParser] Received command, will be analysed')
        if 'set_config' in ReceivedCommand:
            self.logger.log('[NG-CommandParser] Received command set_config')
            return_message = self.setConfiguration(ReceivedCommand)
            if return_message is 'ack':
                answer = {'ans':'ack'}
            else:
                answer = {'ans':'nak'}
                
            self.ZMQPusher(answer) 


        elif 'get_info' in ReceivedCommand:
            self.logger.log('[NG-CommandParser] Received command get_info')
            print(ReceivedCommand)
            answer = self.getInformation()
            self.ZMQPusher(answer) 
        
        else:
            self.logger.log('[NG-CommandParser] Received unrecognized command')
            answer = {'ans':'nak'}
            self.ZMQPusher(answer) 
    
    def ZMQPuller(self):
        while True:
            JsonMessage = self.consumer_receiver.recv_json()
            DictMessage = json.dumps(JsonMessage)
            self.CommandParser(DictMessage)
    
    def ZMQPusher(self, answer):
        self.consumer_sender.send_json(answer)
        pass
    
