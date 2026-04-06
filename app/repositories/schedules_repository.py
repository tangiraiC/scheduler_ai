from sqlalchemy.orm import Session

from app.models.db_models import Schedule


class ScheduleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_schedule(self, name: str, data: str) -> Schedule:
        schedule = Schedule(name=name, data=data)
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule
