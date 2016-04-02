""" 
CellController.py: CogRIoT SISA Information Filter Plug-in

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


import sys
from bson.objectid import ObjectId
from threading import Thread
from time import sleep
sys.path.append("../../")
from utils.logmsgs.logger import Logger
from database.dao import UserDao

logger = Logger()

class SimpleChannel(object):
    '''
    InformationFilter
    
    This filter gets sensing information by channel, discarding time and date information.
    '''
    def __init__(self,
                 queue,
                 informationdatabase_name, 
                 informationdatabase_address):
        '''
        
        '''
        logger.log("Database Processing Information Filter [simplefilter] - Starting")   
        
        # starting information database dao
        self.InformationDAO = UserDao(informationdatabase_name, informationdatabase_address)
        self.SISAInformationFilterName = 'SimpleChannel'
        self.SISAInformationFilterDocName = 'info'

        # starting worker thread
        self.doProcessWorker_t = Thread(target=self.doProcessWorker,
                                  name='simplechannel_t',
                                  args=(queue,))
        self.doProcessWorker_t.daemon = True
        self.doProcessWorker_t.start()

    def doProcessWorker(self, queue):
        '''
        Thread that receives a queue with data from database and do a processing to data aggregation
        '''
        logger.log('Thread started')
        

        
        while True:
            # TODO: Read InformationDataBase structure and store in RAM.
            # All received data in queue is received the processing is done in RAM
            # After all received data have been processed, the database is updated.
              
            while not queue.empty():
                # load information structure storage for local (ram) processing
                LocalInformation = self.LoadInformationFromDatabase() 

                ToProcess = queue.get()
#                 logger.log('queue length: ' + str(len(ToProcess)))
                for k in ToProcess:
                    sector = k['sector']
                    sensor= k['sensor']
                    freq=k['freq']
                    date=k['date']
                    
                    # updtade local information structure
                    LocalInformation = self.UpdateLocalInformationDatabase(LocalInformation, sensor, sector, freq, date)
                
                # update remote db
                self.StoreInformationOnDatabase(LocalInformation)
                
            sleep(0.1)

    def UpdateLocalInformationDatabase(self, infoData, sensor, sector, freq, date):
#         print("."),
#         print(infoData)
        strfreq = str(freq)
        if strfreq in infoData:
#             logger.log('last: ' + str(infoData[strfreq]) + ' sensor: ' + str(sensor))
            infoData[strfreq] = (infoData[strfreq] + sensor)/2.0
#             logger.log('now: ' + str(infoData[strfreq]))
        else:
            infoData[strfreq] = sensor
        
        return infoData

    def StoreInformationOnDatabase(self, infoData):
        rcvd =  self.InformationDAO.findDocument(self.SISAInformationFilterName, {}, 1)
#         print rcvd
        
        if len(rcvd) == 0:
            logger.log('InformationDatabase not found. Creating...')
            self.InformationDAO.insert(self.SISAInformationFilterName, {})
            rcvd =  self.InformationDAO.findDocument(self.SISAInformationFilterName, {}, 1)
        
        docid = rcvd[0]['_id']
        self.InformationDAO.update(self.SISAInformationFilterName,  '_id', ObjectId(docid), infoData)
        logger.log('local information structure saved')
    
    def LoadInformationFromDatabase(self):
        logger.log('loading local information structure')
        document = self.InformationDAO.findDocument(self.SISAInformationFilterName, {}, 1)
        if len(document) == 0:
            # create sample document
            logger.log('remote information structure not found, will be created')
            documentReturned = {}
        else:
            documentReturned = document[0]
            
#         print documentReturned
        
        logger.log('remote information structure loaded on local information structure')
        return documentReturned
