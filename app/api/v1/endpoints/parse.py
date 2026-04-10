from uuid import uuid4

from fastapi import APIRouter

from app import jobs_collection
from app.models.db_models import JobDocument, JobStatus
from app.models.request_models import ParseRequest
from app.models.response_models import ParseResponse
from app.services.extraction_service import ExtractionService

router = APIRouter()


@router.post("", response_model=ParseResponse)
async def parse_text(payload: ParseRequest) -> ParseResponse:
    extractor = ExtractionService()
    extraction_result = await extractor.extract(payload.raw_text)

    job = JobDocument(
        job_id=str(uuid4()),
        domain=payload.domain,
        raw_text=payload.raw_text,
        extracted_constraints=extraction_result["data"],
        status=JobStatus.PARSED,
        warnings=[],
    )
    if jobs_collection is not None:
        jobs_collection.insert_one(job.model_dump(mode="json"))

    return ParseResponse(
        job_id=job.job_id,
        status=job.status,
        extracted_constraints=extraction_result["data"],
        normalization_notes=[],
        warnings=[],
    )
