# app package initializer
from pymongo import MongoClient
from .core.config import settings

# Initialize MongoDB clientclie
client = MongoClient(settings.mongo_uri)
db =  client[settings.mongo_db]

#collections
jobs_collection = db['jobs']
schedules_collection = db['schedules']
