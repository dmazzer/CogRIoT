
""" 
dao.py: CogRIoT SISA Data Access Object 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


from pymongo import MongoClient

import sys
import json
sys.path.append("../../")
from utils.logmsgs.logger import Logger

class UserDao:
    '''
    Class for data abstraction layer to MongoDB
    
    Methods update, findDocument needs rewrite and code that uses it must be rewrited too
    '''
    def __init__(self, db, db_address='mongodb://localhost:27017/'):
        '''
        UserDAO Constructor
        Receives the db (unique for all Cell Controllers), collection (one for each Cell Controller) and db_address
        '''
        
        self.logger = Logger()

        self.logger.log('connecting to database ' + db + ' at ' + db_address)

        client = MongoClient(db_address)
        self.db = client[str(db)]
        
        self.logger.log('done connecting to database')

    def insert(self, CollectionName, jsonstring):
        collection = self.db[str(CollectionName)]
        post_id = collection.insert_one(jsonstring).inserted_id
        return post_id

    def update(self, CollectionName, SearchKey, SearchValue, FieldsJson):
        collection = self.db[str(CollectionName)]
        searchd = {SearchKey: SearchValue }
#         print searchd
#         print FieldsJson
#         print json.dumps(FieldsJson)
#         searchjson = ( searchd , { '$set': json.dumps(FieldsJson) } )
#         print searchjson
#         post_id = collection.update_one(searchd, '{ "$set": json.dumps(FieldsJson) }')
        post_id = collection.update_one(searchd, { "$set": FieldsJson})
        return post_id

    def update2(self, CollectionName, SearchDict, FieldsJson):
        collection = self.db[str(CollectionName)]
#         print searchd
#         print FieldsJson
#         print json.dumps(FieldsJson)
#         searchjson = ( searchd , { '$set': json.dumps(FieldsJson) } )
#         print searchjson
#         post_id = collection.update_one(searchd, '{ "$set": json.dumps(FieldsJson) }')
        post_id = collection.update_one(SearchDict, { "$set": FieldsJson})
        return post_id
    
    def getDateInRange(self, CollectionName, startDate, numberOfItems):
        '''
        Returns numberOfItems items from the database, if available data is less than numberOfItems, no data is returned. 
        '''
        searchd = {"date": {"$gt":str(startDate)}}
        return self.findDocument(CollectionName, searchd, numberOfItems)
        
    def findDocument(self, CollectionName, SearchString, SearchLimit=None):
        collection = self.db[str(CollectionName)]
        if SearchLimit is not None:
            collected = collection.find(SearchString).limit(SearchLimit)
        else:
            collected = collection.find(SearchString)
        collectedlist = []
        for data in collected:
            collectedlist.append(data)
        return collectedlist

    def findDocument2(self, CollectionName, SearchString, SearchLimit=None):
        collection = self.db[str(CollectionName)]
        if SearchLimit is not None:
            collected = collection.find(SearchString).limit(SearchLimit)
        else:
            collected = collection.find(SearchString)
        return collected

    
    def dropCollection(self, CollectionName):
        collection = self.db[str(CollectionName)]
        collection.drop()
        
         
         
