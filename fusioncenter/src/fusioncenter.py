#!/usr/bin/env python2
##################################################
# GNU Radio Python Flow Graph
# Title: Multi-Setorial Spectrum Sensing Platform - Fusion Center
# Author: Daniel Mazzer
# Generated: Tue Aug 18 08:26:05 2015
##################################################

import ConfigParser
from gnuradio.eng_option import eng_option
from optparse import OptionParser


import sys
sys.path.append("../../")
from utils.logmsgs.logger import Logger


class Configuration:
    def __init__(self, config_filename):
        logger.log("Configuration - Starting")
        
        self.config_filename = config_filename;
        self.LoadConfigFile(self.config_filename)
    
        logger.log("Configuration - Started")

        
    def LoadConfigFile(self, config_filename):
        try:
            
            # ConfigParser initialization and configuration file read
            
            configfile = ConfigParser.ConfigParser()
            configfile.read(config_filename)
            rawconfigfile = ConfigParser.RawConfigParser()
            rawconfigfile.read(config_filename)
            
            # Reading all configutarion data from config file
            
            # fusion center section
            self.Load_fusioncenter_output_folder(configfile)
            

            # cellcontroller section
            self.Load_cellcontrollers(rawconfigfile)
          
        except Exception as inst:
            print("Problem reading configuration file")
            print inst
            pass


    # fusion center section
    def Load_fusioncenter_output_folder(self, configfile):
        self.fusioncenter_output_folder = configfile.get('fusioncenter', 'output_folder')

    # cell controllers section
    def Load_cellcontrollers(self, rawconfigfile):
        
        # create cell controllers dictionary (structure)
        self.CellControllerServers = dict()
        
        # read controllers from config file
        self.rawconfigfile = rawconfigfile
        section_list = self.rawconfigfile.sections()
        section_name_prefix = "cellcontroller-"
        controllers = []
        controllers_names = "" 
        for i in range (len(section_list)):
            if section_name_prefix in section_list[i]:
                controllers.append(section_list[i]) 
                controllers_names += ((section_list[i])[len(section_name_prefix):]) + ' '
        logger.log("Cell Controllers available: " + str(controllers_names))
        
        
        # load controllers listeners address and connect (ZMQ) to them
        
        for i in range (len(controllers)):
            channelcontroller_address = self.rawconfigfile.get(controllers[i], 'channelcontroller_address')
            sectorcontroller_address = self.rawconfigfile.get(controllers[i], 'sectorcontroller_address')
            self.AddCellControllerListeners(self, controllers, channelcontroller_address, sectorcontroller_address)
            
        def AddCellControllerServers(self, controllers, channelcontroller_address, sectorcontroller_address):
            self.CellControllerServers
        
        def Load_fusioncenter_output_folder(self, configfile):
        self.fusioncenter_output_folder = configfile.get('fusioncenter', 'output_folder')
       

        #todo: pelo arquivo de configuracao, obter os cell controllers


if __name__ == '__main__':
    

    logger = Logger()
    logger.log("Remote Sensor application started.")
        
    # Options parser
    
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option("-c", "--config-filename", action="store", type="string", dest="config_filename", help="load configuration file")
    (options, args) = parser.parse_args()
    if(str(options.config_filename) == "None"):
        print("config-filename cannot be empty")
        quit()
    
    # Configurations load from file
    
    config = Configuration(options.config_filename);
    
    # Applying configurations to TopBlock

    # Starting Controllers
    
    logger.log("Application terminated")