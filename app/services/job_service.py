from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.db.mongo import get_database


class JobNotFoundError(Exception):
    pass


class JobService:
    """
    MongoDB-backed job store for persisted scheduling runs.
    """

    def __init__(self) -> None:
        self.collection = get_database()["jobs"]

    def create_job(self, payload: dict[str, Any]) -> str:
        job_id = str(uuid4())

        document = {
            "job_id": job_id,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **self._mongo_safe(payload),
        }

        self.collection.insert_one(document)
        return job_id

    def get_job(self, job_id: str) -> dict[str, Any]:
        job = self.collection.find_one({"job_id": job_id}, {"_id": 0})
        if not job:
            raise JobNotFoundError(f"Job '{job_id}' not found.")
        return job

    def _mongo_safe(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._mongo_safe(item) for key, item in value.items()}

        if isinstance(value, list):
            return [self._mongo_safe(item) for item in value]

        if isinstance(value, tuple):
            return [self._mongo_safe(item) for item in value]

        return value
