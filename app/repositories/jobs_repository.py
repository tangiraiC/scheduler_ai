from typing import Any

from app.models.db_models import JobDocument


class JobRepository:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    def list_jobs(self) -> list[JobDocument]:
        if self.collection is None:
            return []

        jobs: list[JobDocument] = []
        for item in self.collection.find({}, {"_id": 0}):
            jobs.append(JobDocument.model_validate(item))
        return jobs
