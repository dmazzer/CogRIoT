
""" 
databaseprocessing.py: CogRIoT DAO Information Processing 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


from database.dao import UserDao
from threading import Thread
from time import sleep
from Queue import Queue

import sys
from bson.objectid import ObjectId
# from informationfilter import simplechannel
from informationfilter import simpleanalyzer
sys.path.append("../../")
from utils.logmsgs.logger import Logger

logger = Logger()

class DataBaseExtractor():
    def __init__(self, 
                 queue,
                 controldatabase_name, 
                 controldatabase_address, 
                 SensingDAO):
        '''
        Queue used for working thread send data collected form DB to processing method
        
        This class fetches data from sensing database and put on a queue for analysis processing plugin
        This class mantains a control database to identify the sensig data already processed/analysed
        This class starts a thread that fetch data from sensing database and deliver to analysis plugins
        '''

        
        # starting control database dao
        self.ControlDAO = UserDao(controldatabase_name, controldatabase_address)

        # defining some constants, may be put on database or configuration file in future
        self.SISAControlCollectionName = 'Control'
        self.SISAControlLastDateString = 'lastDate' 
        self.SISAInformationCollectionName = 'Info'
        
        default_initial_date = '2015-01-01 12:00:00'
        
        # number of items fetched from database each time it is consulted
        self.numberOfItemsToBatchProcess = 50

        self.SensingDAO = SensingDAO
        
        # search for the only one document that may exist on SISAControlCollection collection.
        ControlDocument = self.ControlDAO.findDocument(self.SISAControlCollectionName, {}, 1)
        newDocument = {}
        if len(ControlDocument) == 0 :
            logger.log('Document not found, will be created')
            newDocument[self.SISAControlLastDateString] = default_initial_date
            self.ControlDAO.insert(self.SISAControlCollectionName, newDocument)
        elif 'lastDate' not in ControlDocument[0]:
            logger.log('Document not found, will be created')
            newDocument[self.SISAControlLastDateString] = default_initial_date
            self.ControlDAO.insert(self.SISAControlCollectionName, newDocument)
            
#         # read document ID
#         # unused?
#         self.ControlDocumentID = self.ControlDAO.findDocument(self.SISAControlCollectionName, {}, 1)[0]['_id']
#         logger.log('Control document ID: ' + str(self.ControlDocumentID))
#         
#         # unused?
#         self.ControlDocumentLastDate = self.ControlDAO.findDocument(self.SISAControlCollectionName, {}, 1)[0]['date']
#         logger.log('Control document last date: ' + str(self.ControlDocumentLastDate))
        
        self.getInformationWorker_t = Thread(target=self.getInformationWorker,
                                  name='getInformationWorker_t',
                                  args=(queue,))
        self.getInformationWorker_t.daemon = True
        self.getInformationWorker_t.start()

    def getInformationWorker(self, queue):
        '''
        Thread that keep consulting the database and collect new sensing measures.
        Acquired data are put on q queue for later processing.
        Data processing will be done by Information Filters Classes (plug-ins)
        '''
        
        logger.log('Thread started')
        while True:
            lastDate = self.ControlDAO.findDocument(self.SISAControlCollectionName, {}, 1)[0][self.SISAControlLastDateString]
            
#             logger.log('Last date processed: ' + str(lastDate))
            
            ret = self.SensingDAO.getDateInRange('blob', 
                                              lastDate, 
                                              self.numberOfItemsToBatchProcess)

            received = len(ret)

            if received > 0 :
                logger.log('Items received: ' + str(received))
#                 for data in ret:
#                     print data
                # Updating the last document processed
                newLastDate = ret[received-1]['date']
#                 logger.log('New last date : ' + newLastDate)
                rcvd =  self.ControlDAO.findDocument(self.SISAControlCollectionName, {}, 1)
                docid = rcvd[0]['_id']
                newDate = {self.SISAControlLastDateString : newLastDate}
                self.ControlDAO.update(self.SISAControlCollectionName, '_id', ObjectId(docid), newDate)

                queue.put(ret)

                if received < self.numberOfItemsToBatchProcess:
                    sleep(5)
            else:
                logger.log('Items received: 0 - going to sleep 5 seconds')
                sleep(5)
            
#             sleep(1)

class DataBaseProcessing():
    def __init__(self, 
                 controldatabase_name, 
                 controldatabase_address, 
                 informationdatabase_name, 
                 informationdatabase_address, 
                 SensingDAO):

        logger.log("Database Processing - Starting")        
        queue = Queue()
        dbe = DataBaseExtractor(queue,
                                 controldatabase_name, 
                                 controldatabase_address, 
                                 SensingDAO)
        
        # load the processing plug-in
        # verify that for future improvement:
        # http://stackoverflow.com/questions/932069/building-a-minimal-plugin-architecture-in-python
        # https://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/
        filter = simpleanalyzer.AnalysisPlugIn(queue,
                                                informationdatabase_name, 
                                                informationdatabase_address)
        
#         filter = simplechannel.SimpleChannel(queue,
#                                              informationdatabase_name, 
#                                              informationdatabase_address)
        
        logger.log("Database Processing - Started")        
        
    
if __name__ == '__main__':
    '''
    Just for test purposes
    '''
    cc_id = 'blob'
    db_id = 'SensingData'
    udao = UserDao(db_id, 'mongodb://10.0.0.104:27017/')
    dbp = DataBaseProcessing('SISAControl', 'mongodb://10.0.0.104:27017/', udao )
       
    input('Press enter to quit')
