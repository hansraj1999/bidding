from pymongo import MongoClient
from threading import Lock
import os

class MongoDBClient:
    _instance = None  # Singleton instance
    _lock = Lock()  # Lock for thread safety

    def __new__(cls, database="hashiras"):  # NOSONAR get db name from config
        uri = os.getenv("mongo_con", "mongodb://localhost:27017")
        print(uri, "ofnonfonfon")
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
        if self.client is None: # NOSONAR
            raise Exception("MongoDB client is not initialized") # NOSONAR
        return self.client
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


class Constants:
    port = 587  
    smtp_server = os.getenv("smtp_server", "smtp.gmail.com")
    sender_email = os.getenv("sender_email", "")
    password = os.getenv("password", "")
    smtp_client = None