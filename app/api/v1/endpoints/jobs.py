from fastapi import APIRouter, HTTPException

from app.schemas.job import JobResponse
from app.services.job_service import JobNotFoundError, JobService

router = APIRouter()
job_service = JobService()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    try:
        job = job_service.get_job(job_id)
        return JobResponse(
            status="success",
            job_id=job_id,
            job=job,
        )
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected job lookup failure: {exc}",
        ) from exc
