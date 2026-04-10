from .core.config import settings

try:
    from pymongo import MongoClient
except ModuleNotFoundError:
    MongoClient = None


client = MongoClient(settings.mongo_uri) if MongoClient else None
db = client[settings.mongo_db_name] if client else None

jobs_collection = db["jobs"] if db is not None else None
schedules_collection = db["schedules"] if db is not None else None
