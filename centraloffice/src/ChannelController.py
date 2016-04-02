#!/usr/bin/env python2

""" 
ChannelController.py: CogRIoT Sensing Cell Channel Controller  

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"

import threading
import time
from datetime import datetime
from math import ceil
from gnuradio import eng_notation
from Logger import Logger
import zmqPub


class ChannelController():
    def __init__(self, tbObject, listener_address, SectorController, start_freq, stop_freq, band_width):
        '''
        
        :param tbObject: GNU Radio TopBlock object to have the receiver controller
        :param SectorController: SectorController object
        :param start_freq: Sensing start Frequency
        :param stop_freq: Sensing stop Frequency
        :param band_width: Sensing band width
        
        '''
        self.logger = Logger()
        self.logger.log("ChannelController - Starting")
        
        self.__tb = tbObject;
        self.__start_freq = start_freq
        self.__stop_freq = stop_freq
        self.__band_width = band_width
        self.__SectorController = SectorController
        self.__listener_address = listener_address
        
        if self.__SectorController is None:
            print("Missing value")
            raise SystemExit, 1

        if self.__band_width is None:
            print("Missing value")
            raise SystemExit, 1
            
        if self.__start_freq is None:
            print("Missing value")
            raise SystemExit, 1

        if self.__stop_freq is None:
            print("Missing value")
            raise SystemExit, 1
        
        self.set_num_bands()
           
        self.zmqPublisher = zmqPub.zmqDissInfo(self.__listener_address);
           
        # starting thread ChannelController thread
        timerThread = threading.Thread(name='ChannelControllerRun', target=self.ChannelControllerRun)
        timerThread.daemon = True
        timerThread.start()
            
        self.logger.log("ChannelController - Started")
            
    def get_band_idx_postinc(self):
        '''
        Return __band_idx and post increment its value
        Every time the channel index returs to 0, the SectorController.sector_change is called
        '''
        tmp_idx = self.__band_idx
        if ((self.__band_idx + 1) < self.__num_bands):
            self.__band_idx += 1
        else:
            self.__band_idx = 0

        if(self.__band_idx == 1):
            self.__SectorController.sector_change()
        
        return tmp_idx
        
        
    def ChannelControllerRun(self):
        self.next_call = time.time()
        while True:
            self.set_freq_by_idx(self.get_band_idx_postinc())
            #print datetime.datetime.now()
            self.next_call = self.next_call+1;
            time.sleep(self.next_call - time.time())
               
    def set_freq_by_idx(self, band_idx):
        abs_freq = self.__start_freq + (self.__step_freq * band_idx)
        self.__tb.set_rx_freq(abs_freq)
        self.logger.log('switched to channel idx ' + str(band_idx) + ' freq ' + str(abs_freq))
        #msg = str(band_idx) + ',' + str(abs_freq)
        msg = { 'band_idx': band_idx, 'freq': abs_freq }
        self.zmqPublisher.SendMessage(msg)
       
    def set_num_bands(self):
        '''
        Calculates the number of bands and the step frequency in Hz.
        Must be called before starting ChannelControllerRun 
        '''
        
        self.__band_idx = 0
        
        k = self.__stop_freq - self.__start_freq
        #self.logger.log('Calculating frequency band parameters')
        if k <= 0:
            self.logger.log('Error - Wrong frequency range')
            raise SystemExit, 1
    
        self.__num_bands = int(ceil(k / self.__band_width))
        self.__step_freq = int(ceil(k / self.__num_bands))
            
        if self.__num_bands <= 0:
            self.logger.log('Error - Wrong frequency range')
            raise SystemExit, 1
        
        self.logger.log('Number of bands ' + str(self.__num_bands))
        self.logger.log('Frequency step  ' + eng_notation.num_to_str(self.__step_freq))       
