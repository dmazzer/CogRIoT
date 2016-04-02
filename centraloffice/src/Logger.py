""" 
Logger.py: CogRIoT console message log application  

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"

import logging

class Logger():
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG,
                        format='[%(asctime)s %(threadName)s] %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')
    def log(self, msg):
        self.logger.info(msg)