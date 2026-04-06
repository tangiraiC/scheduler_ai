from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.models.response_models import JobListResponse
from app.repositories.jobs_repository import JobRepository

router = APIRouter()


@router.get("", response_model=JobListResponse)
async def list_jobs(db: Session = Depends(get_db_session)) -> JobListResponse:
    repo = JobRepository(db)
    jobs = repo.list_jobs()
    return JobListResponse(jobs=jobs)
