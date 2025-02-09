import os
import sys
from config import MongoDBClient, Constants


mongo = MongoDBClient()
mongo_client = mongo.get_client()
constants = Constants()
