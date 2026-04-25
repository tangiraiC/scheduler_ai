from app.db.mongo import get_database

db = get_database()
jobs_collection = db["jobs"]
schedules_collection = db["schedules"]
