from uuid import uuid4

from fastapi import APIRouter

from app import schedules_collection
from app.models.request_models import ScheduleRequest
from app.models.db_models import ScheduleDocument
from app.models.response_models import ScheduleResponse
from app.services.schedule_service import ScheduleService

router = APIRouter()


@router.post("", response_model=ScheduleResponse)
async def create_schedule(payload: ScheduleRequest) -> ScheduleResponse:
    service = ScheduleService()
    schedule = service.build_schedule(payload.constraints)
    schedule_id = str(uuid4())

    schedule_document = ScheduleDocument(
        schedule_id=schedule_id,
        job_id=str(uuid4()),
        feasible=True,
        assignments=[],
        validation_summary={"normalized": True, "strategy": payload.strategy},
        metrics={
            "node_count": len(schedule.get("nodes", [])),
            "edge_count": len(schedule.get("edges", [])),
        },
    )
    if schedules_collection is not None:
        schedules_collection.insert_one(schedule_document.model_dump(mode="json"))

    return ScheduleResponse(
        job_id=schedule_document.job_id,
        status="scheduled",
        feasible=schedule_document.feasible,
        schedule=schedule,
        validation_summary=schedule_document.validation_summary,
        warnings=[],
        metrics=schedule_document.metrics,
    )
