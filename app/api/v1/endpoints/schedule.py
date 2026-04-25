from __future__ import annotations

import inspect

from fastapi import APIRouter, HTTPException

from app.schemas.schedule import ScheduleRequest, ScheduleResponse
from app.services.job_service import JobService
from app.services.schedule_service import ScheduleService, ScheduleServiceError

router = APIRouter()
schedule_service = ScheduleService()
job_service = JobService()


@router.post("", response_model=ScheduleResponse)
async def create_schedule(payload: ScheduleRequest) -> dict:
    try:
        if payload.raw_text:
            result = schedule_service.run(
                raw_text=payload.raw_text,
                strategy=payload.strategy,
                metadata=payload.metadata or {},
            )
            if inspect.isawaitable(result):
                result = await result
        elif payload.constraints:
            result = schedule_service.run_from_constraints(
                constraints=payload.constraints,
                strategy=payload.strategy,
                metadata=payload.metadata or {},
            )
        else:
            raise ScheduleServiceError("Either raw_text or constraints is required.")

        job_id = job_service.create_job(result)
        result["job_id"] = job_id
        return result
    except ScheduleServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected scheduling failure: {exc}",
        ) from exc
