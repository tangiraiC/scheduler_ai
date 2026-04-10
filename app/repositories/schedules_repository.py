from typing import Any

from app.models.db_models import ScheduleDocument


class ScheduleRepository:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    def create_schedule(self, schedule: ScheduleDocument) -> ScheduleDocument:
        if self.collection is not None:
            self.collection.insert_one(schedule.model_dump(mode="json"))
        return schedule
