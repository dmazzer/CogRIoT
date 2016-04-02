""" 
simpleanalyzer.py: CogRIoT SISA Information Filter Plug-in 

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
from dateutil.parser import parse
from math import floor

logger = Logger()

class AnalysisPlugIn(object):
    '''
    AnalysisPlugIn
    
    This class is a Plug-In Analysis Filter for SISA block
    This class do a simple analysis, storing mean usage of each channel frequency.
    '''
    def __init__(self,
                 queue,
                 informationdatabase_name, 
                 informationdatabase_address):
        '''
        
        '''
        logger.log("Database Processing Information Filter [simpleanalyzer] - Starting")   
        
        self.__ConstHourSlotsSize = 1 # value in hours
        
        # starting information database dao
        self.InformationDAO = UserDao(informationdatabase_name, informationdatabase_address)
        self.SISAInformationFilterName = 'SimpleAnalyzer'
#         self.SISAInformationFilterDocName = 'info'

        # starting worker thread
        self.doProcessWorker_t = Thread(target=self.doProcessWorker,
                                  name='analyzerplugin_t',
                                  args=(queue,))
        self.doProcessWorker_t.daemon = True
        self.doProcessWorker_t.start()

    def doProcessWorker(self, queue):
        '''
        Thread that receives a queue with data from database and do a processing to data aggregation
        '''
        logger.log('Thread started')
        
        while True:
            while not queue.empty():
                SensingDataToProcess = queue.get()
#                 logger.log('Items received: ' + str(len(SensingDataToProcess)))
                for k in SensingDataToProcess:
                    scc_id = k['cellid']
                    sector = k['sector']
                    sensor = k['sensor']
                    freq = k['freq']
                    AcquireDate = k['date']
                    AcquireDateParsed = parse(AcquireDate) 
                    HourSlotIdx = str(int(floor(AcquireDateParsed.hour/self.__ConstHourSlotsSize)))
                    AcquireYearMonthDay = AcquireDateParsed.strftime("%Y-%m-%d")
#                     logger.log('Date: ' + str(AcquireDateParsed) + ' - Hslot: ' + HourSlotIdx + ' - ' + AcquireYearMonthDay)
                    self.UpdateDatabase(AcquireYearMonthDay, scc_id, sector, freq, HourSlotIdx, sensor)
                             
            sleep(0.2)

    def UpdateDatabase(self, AcquireDayMonthYear, scc_id, sector, freq, HourSlotIdx, sensor):
        '''
        This method fetch data from database and update the mean sensing information if existent.
        If not existent, the register will be created
        '''
        
        QueryResult = self.QuerySensingData(AcquireDayMonthYear, scc_id, sector, freq, HourSlotIdx)
        
        if QueryResult.count() == 0:
#             print 'c',
            self.InsertSensingData(AcquireDayMonthYear, scc_id, sector, freq, HourSlotIdx, sensor)       
        else:
#             print 'u',
            for doc in QueryResult:
                OldSensorValue = doc['sensor']
                NewSensorValue = (OldSensorValue + sensor) / 2.0
#                 print ('old: ' + str(OldSensorValue) + ', new: ' + str(NewSensorValue))
                self.UpdateSensingData(doc['date'], doc['scc_id'], doc['sector'], doc['freq'], doc['time_slot'], NewSensorValue)
            
        
    def QuerySensingData(self, date, scc_id, sector, freq, time_slot):
        querystring = {'date' : str(date), 'scc_id' : str(scc_id), 'freq': str(freq), 'sector': str(sector), 'time_slot': str(time_slot)}
        queryresult = self.InformationDAO.findDocument2(self.SISAInformationFilterName, querystring)
        return queryresult
        
    def UpdateSensingData(self, date, scc_id, sector, freq, time_slot, sensor):
        querystring = {'date' : str(date), 'scc_id' : str(scc_id), 'freq': str(freq), 'sector': str(sector), 'time_slot': str(time_slot)}
        updateid = self.InformationDAO.update2(self.SISAInformationFilterName, querystring, {'sensor':sensor})
        return updateid

    def InsertSensingData(self, date, scc_id, sector, freq, time_slot, sensor):
        sensingdata = {'date' : str(date), 'scc_id' : str(scc_id), 'freq': str(freq), 
                       'sector': str(sector), 'time_slot': str(time_slot), 'sensor': sensor}
        insertid = self.InformationDAO.insert(self.SISAInformationFilterName, sensingdata)
        return insertid
         
