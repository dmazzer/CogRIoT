""" 
collector.py: ZMQ message collector 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = ""
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


import zmq
from threading import Thread
from Queue import Queue
import threading
from Logger import Logger
import pmt
import os
import datetime
import json
from time import sleep

class CollectorThread():
    '''
    Class to be instantiated as a thread on method work.
    Subscribers will be created and the received messages are put on a queue.
    '''
    
    def __init__(self, queue, thread_lock, from_gnuradio=False):
        self.logger = Logger()
        self.thread_lock = thread_lock
        self.q = queue
        self.from_gnuradio = from_gnuradio
    
    def work(self, queue, listener_address, label):
        self.q = queue
        self.label = label
        self.listener_address = listener_address
        
        self.logger.log("init: " + self.label)
        
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.SUBSCRIBE, '')
        socket.connect(listener_address)
        
        while True:
            # Important improvement opportunity 1: The zmq socket that are transmitting to the collector
            # is sending data as json (send_json), but here the data is being received as normal string.
            # This is getenrating some inconsistency and the code should be reviewed in future.
            
            # Important improvement opportunity 2: The information transported by zmq between applications
            # may use linux socket instead of tcp socket.
             
            k = socket.recv()
            if self.from_gnuradio == True:
                # this part of code seams to be consuming alot of processing, needs verification
                try:
                    p = pmt.deserialize_str(k)
                except Exception:
                    p = None
                    self.logger.log('Error: problem deserializing message')

                if p is not None:
                    python_numpy_array = pmt.pmt_to_python.pmt_to_python(p)
                    tosend = str(python_numpy_array[0])
                    msg = (self.label, tosend)
                    with self.thread_lock:
                        self.q.put(msg)
                        
            else:
                tosend = k
                msg = (self.label, tosend)
                with self.thread_lock:
                    self.q.put(msg)
            
            sleep(0.01) # test
                

class ZMQCollector():
    '''
    Receive and aggregate ZMQ messages from ChannelController, SectorController, and CellController (aka SensingProcessor)
    Received messages are transmitted via ZMQ PUSH protocol to a specified push_address
    '''

    def __init__(self,
                 CellID, 
                 ChannelController_listener_address,  
                 SectorController_listener_address, 
                 CellController_listener_address, 
                 Collector_push_address):
        '''
        Constructor
        '''
        self.logger = Logger()
        self.logger.log("ZMQCollector - Starting")
       
        self.q = Queue()
        self.thread_lock = threading.Lock()
        
#        self.msgid = os.urandom(4)
        self.msgid = int((os.urandom(4)).encode('hex'), 16)
        self.CellID = CellID
    
        
        self.ChannelController_listener_address = ChannelController_listener_address
        self.SectorController_listener_address = SectorController_listener_address
        self.CellController_listener_address = CellController_listener_address
        self.Collector_push_address = Collector_push_address

        self.InitCollectors()
        self.InitSender()
        
        self.logger.log("ZMQCollector - Started")
    
    
    def getMsgID(self):
        self.msgid = self.msgid + 1
        return self.msgid 
    
    def getDateTime(self):
        return str(datetime.datetime.utcnow())
    
        
    def InitSender(self):
        self.Sender_t = Thread(target=self.SenderThread,
                                          name="Sender_t",
                                          args=(self.q, 
                                          self.Collector_push_address))
        self.Sender_t.daemon = True
        self.Sender_t.start()
        
        
    def SenderThread(self, queue, push_address):
        self.q = queue
        self.push_address = push_address
        
        self.logger.log("init: Sender")
        
        context = zmq.Context()
        zmq_socket = context.socket(zmq.PUSH)
        zmq_socket.bind(self.push_address)
        
        self.logger.log("socket listening")

        # the following control variables configures how many samples will be ignored after the selected channel is changed.
        # it was needed because some readings are buffered inside gnuradio and is complicated to synchronize with python.
        # to fix this, a scheme of tagged streams may be implemented, where all radio configurations is send to the 
        # gnuradio top block, with the tags the readings may be synchronized inside the oot block. 
        self.IgnoreMessages = 0
        self.NumberOfMessagesToIgnore = 2

        self.amsg = {'cellid': (),
                     'msgid': (),
                     'date': (),
                     'freq': (), 
                     'channel': (),
                     'sector': (),
                     'sensor': () }

        while True:
            
            with self.thread_lock:
                while not self.q.empty():
                    msg = self.q.get()
                    if msg[0] == "ChannelController":
                        self.logger.log("ChannelController arrived")
                        self.amsg['freq'] = json.loads(msg[1])['freq']
                        self.amsg['channel'] = json.loads(msg[1])['band_idx']
                        self.IgnoreMessages = self.NumberOfMessagesToIgnore
                        
                    if msg[0] == "SectorController":
                        self.logger.log("SectorController arrived")
                        self.amsg['sector'] = msg[1]
                        
                    if msg[0] == "CellController":
                        if self.IgnoreMessages > 0:
                            self.IgnoreMessages = self.IgnoreMessages - 1
                            continue # skip the rest of this loop
                            
                        self.logger.log("CellController arrived")
                        self.amsg['cellid'] = self.CellID
                        self.amsg['msgid'] = self.getMsgID()
                        self.amsg['date'] = self.getDateTime()
                        self.amsg['sensor'] = float(msg[1])
#                         self.logger.log(self.amsg)
                        zmq_socket.send_json(self.amsg)
#                         self.logger.log('message sent')
        sleep(0.01) # test
                    


    def InitCollectors(self):
        '''
        Start threads that listen to a ZMQ socket.
        
        To do:
        Studing python, I've found that many python threads on multicore CPUs runs very slowly,
        worse than on single core CPUs. In future, consider implement only one thread 
        or instantiate many python applications.
        '''
         
        self.ChannelController_work = CollectorThread(self.q, self.thread_lock)
        self.ChannelController_t = Thread(target=self.ChannelController_work.work,
                                          name="ChannelController_t",
                                          args=(self.q, 
                                          self.ChannelController_listener_address, 
                                          "ChannelController"))
        self.ChannelController_t.daemon = True
        self.ChannelController_t.start()
        
        self.SectorController_work = CollectorThread(self.q, self.thread_lock)
        self.SectorController_t = Thread(target=self.SectorController_work.work,
                                          name="SectorController_t",
                                          args=(self.q, 
                                          self.SectorController_listener_address, 
                                          "SectorController"))
        self.SectorController_t.daemon = True
        self.SectorController_t.start()
         
        self.CellController_work = CollectorThread(self.q, self.thread_lock, from_gnuradio=True)
        self.CellController_t = Thread(target=self.CellController_work.work,
                                          name="CellController_t",
                                          args=(self.q, 
                                          self.CellController_listener_address, 
                                          "CellController"))
        self.CellController_t.daemon = True
        self.CellController_t.start()
                