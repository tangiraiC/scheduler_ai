from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.mongo import close_mongo_connection, connect_to_mongo

configure_logging()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Hybrid small language model + graph coloring scheduling API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def startup_event() -> None:
    connect_to_mongo()


@app.on_event("shutdown")
def shutdown_event() -> None:
    close_mongo_connection()


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running"}
