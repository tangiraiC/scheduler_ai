from fastapi import APIRouter

from app import jobs_collection
from app.models.db_models import JobDocument
from app.models.response_models import JobListResponse
from app.repositories.jobs_repository import JobRepository

router = APIRouter()


@router.get("", response_model=JobListResponse)
async def list_jobs() -> JobListResponse:
    repo = JobRepository(jobs_collection)
    jobs = repo.list_jobs()
    return JobListResponse(jobs=jobs)
