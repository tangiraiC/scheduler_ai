from fastapi import APIRouter

from app.api.v1.endpoints import health, jobs, parse, schedule

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(parse.router, prefix="/parse")
api_router.include_router(schedule.router, prefix="/schedule")
api_router.include_router(jobs.router, prefix="/jobs")
