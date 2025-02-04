import os
import sys
from config import MongoDBClient


mongo = MongoDBClient()
mongo_client = mongo.get_client()