from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.parse import router as parse_router
from app.api.v1.endpoints.schedule import router as schedule_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(parse_router, prefix="/parse", tags=["parse"])
api_router.include_router(schedule_router, prefix="/schedule", tags=["schedule"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
