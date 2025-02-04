from pymongo import MongoClient
from threading import Lock
import os


class MongoDBClient:
    _instance = None  # Singleton instance
    _lock = Lock()  # Lock for thread safety

    def __new__(cls, uri=os.getenv("mongo_con", "mongodb://localhost:27017"), database="hashiras"): # TODO: fetch database name from config
        print(os.getenv("mongo_con", "mongodb://localhost:27017"), "ofnonfonfon")
        if not cls._instance:
            with cls._lock:  # Ensure thread safety
                if not cls._instance:  # Double-check locking
                    cls._instance = super().__new__(cls)
                    cls._instance._init_client(uri, database)
        return cls._instance

    def _init_client(self, uri, database):
        """Initialize MongoDB client"""
        self.client = MongoClient(uri, maxPoolSize=50, minPoolSize=5, serverSelectionTimeoutMS=5000)
        self.client = self.client[database]
    
    def get_client(self):
        """Get MongoDB client"""
        if self.client is None:
            raise Exception("MongoDB client is not initialized")
        return self.client
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()