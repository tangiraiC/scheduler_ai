from fastapi import APIRouter

from app.models.request_models import ScheduleRequest
from app.models.response_models import ScheduleResponse
from app.services.schedule_service import ScheduleService

router = APIRouter()


@router.post("", response_model=ScheduleResponse)
async def create_schedule(payload: ScheduleRequest) -> ScheduleResponse:
    service = ScheduleService()
    schedule = service.build_schedule(payload.constraints)
    return ScheduleResponse(schedule=schedule)
