from fastapi import APIRouter
from app.core.database import db
router = APIRouter()

@router.get("/testdb")
def test_db():
    try:
        db.command('ping')
        return {"message": "Database connection successful!"}
    except Exception as e:
        return {"message": f"Database connection failed: {str(e)}"}