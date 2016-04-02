""" 
SectorController.py: CogRIoT Sensing Cell Sector Controller application 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


import zmqPub
from Logger import Logger



class SectorController():
    def __init__(self, listener_address):
        self.logger = Logger()
        self.logger.log("SectorController - Starting")

        self.__listener_address = listener_address
        
        self.zmqPublisher = zmqPub.zmqDissInfo(self.__listener_address);        

        self.sector_reset()

        self.logger.log("SectorController - Started")
        
    def sector_change(self):
        self.logger.log('SectorController - Sector Changed')
        msg = '0' # Not implemented, should send the sector index number
        self.zmqPublisher.SendMessage(msg)
        
    def sector_reset(self):
        self.logger.log('SectorController - Sector reset')
        msg = '0' # Not implemented, should send the sector index number
        self.zmqPublisher.SendMessage(msg)
        