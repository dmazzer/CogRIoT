#!/usr/bin/env python2

""" 
sisa.py: CogRIoT SISA main application 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


from informationstorage.zmqpuller import ZMQPuller
from database.dao import UserDao
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import ConfigParser
from utils.logmsgs.logger import Logger
from uuid import uuid1
import signal
import os
from informationanalysis.databaseprocessing import DataBaseProcessing

class Configuration:
    def __init__(self, config_filename):
        logger.log("Configuration - Starting")
        
        self.config_filename = config_filename;
        self.LoadConfigFile(self.config_filename)
    
        logger.log("Configuration - Started")

    def LoadConfigFile(self, config_filename):
        try:
            
            # ConfigParser initialization and configuration file read
            
            configfile = ConfigParser.RawConfigParser()
            configfile.read(config_filename)
            
            # Reading all configutarion data from config file
            
            # sisa section
            self.Load_sisa_id(configfile, config_filename)
            
            # sensing database section
            self.Load_SensingDatabase(configfile)
            
            # control database section
            self.Load_ControlDatabase(configfile)

            # information database section
            self.Load_InformationDatabase(configfile)

            # sensing receiver section
            self.Load_sensingreceiver_zmqpull_address(configfile)
            
        except Exception as inst:
            print("Problem reading configuration file")
            print inst
            raise

    def SaveConfigFile(self, configfile, config_filename, section, option, value):
        #print(configfile, config_filename, section, option, value)
        try:
            configfile.set(section, option, value)
            with open(config_filename, 'wb') as filetowrite:
                logger.log('Saving configuration file')
                configfile.write(filetowrite)
                            
        except Exception as inst:
            print("Problem writing configuration file")
            print inst
            raise 


    def Load_SensingDatabase(self, configfile):
        self.sensingdatabase_address = configfile.get('sensingdatabase', 'address')
        self.sensingdatabase_db =  configfile.get('sensingdatabase', 'db')

    def Load_ControlDatabase(self, configfile):
        self.controldatabase_address = configfile.get('controldatabase', 'address')
        self.controldatabase_db =  configfile.get('controldatabase', 'db')

    def Load_InformationDatabase(self, configfile):
        self.informationdatabase_address = configfile.get('informationdatabase', 'address')
        self.informationdatabase_db =  configfile.get('informationdatabase', 'db')

    def Load_sisa_id(self, configfile, config_filename):
        self.cellcontroller_id = configfile.get('sisa', 'id')
        if self.cellcontroller_id == '':
            sisa_id = str(uuid1())
            logger.log('Generating UUID: ' + sisa_id)
            self.SaveConfigFile(configfile, config_filename, 'sisa', 'id' , sisa_id)

    def Load_sensingreceiver_zmqpull_address(self, configfile):
        self.sensingreceiver_zmqpull_address = configfile.get('sensingreceiver', 'zmqpull_address')


if __name__ == '__main__':


    # Platform initialization stuff
    
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

    logger = Logger()
    logger.log("SIS application started.")
    
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option("-c", "--config-filename", action="store", type="string", dest="config_filename", help="load configuration file")
    parser.add_option("-d", "--drop-database", action="store_true", dest="drop_database", help="if set, control and information databases will be initially droped")
    (options, args) = parser.parse_args()
    if(str(options.config_filename) == "None"):
        print("config-filename cannot be empty")
        quit()
    if(str(options.drop_database) == True):
        print("Dropping databases - NOT IMPLEMENTED!!")
        

    
    # Configurations load from file
    config = Configuration(options.config_filename);

    # starting sensing database dao
    SensingDAO = UserDao(config.sensingdatabase_db, config.sensingdatabase_address)
    
    # starting zmq pull task class
    zmqpuller = ZMQPuller(SensingDAO, config.sensingreceiver_zmqpull_address)
    
    # starting database processing
    dbp = DataBaseProcessing(config.controldatabase_db, config.controldatabase_address,
                             config.informationdatabase_db, config.informationdatabase_address, SensingDAO )
 
    def do_exit(sig, stack):
        raise SystemExit('Exiting')
    
    signal.signal(signal.SIGINT, do_exit)
    signal.signal(signal.SIGUSR1, do_exit)
    
    logger.log('My PID: ' + str(os.getpid()))

    signal.pause()    


