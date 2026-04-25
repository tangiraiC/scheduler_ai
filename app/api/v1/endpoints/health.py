from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.db.mongo import ping_mongo
from app.services.lmstudio_client import LMStudioClient

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    services = {
        "api": {"status": "healthy"},
        "mongodb": {"status": "unknown"},
        "lmstudio": {"status": "unknown"},
    }

    try:
        mongo_info = ping_mongo()
        services["mongodb"] = {
            "status": "healthy",
            **mongo_info,
        }
    except Exception as exc:
        services["mongodb"] = {
            "status": "unhealthy",
            "error": str(exc),
        }

    try:
        models = LMStudioClient().list_models()
        services["lmstudio"] = {
            "status": "healthy",
            "models": models,
        }
    except Exception as exc:
        services["lmstudio"] = {
            "status": "unhealthy",
            "error": str(exc),
        }

    overall_status = "healthy"
    if any(service.get("status") != "healthy" for service in services.values()):
        overall_status = "degraded"

    return HealthResponse(status=overall_status, services=services)
