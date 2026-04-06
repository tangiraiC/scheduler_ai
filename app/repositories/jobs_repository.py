from sqlalchemy.orm import Session

from app.models.db_models import Job


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_jobs(self) -> list[Job]:
        return self.db.query(Job).all()

    def create_job(self, title: str, description: str) -> Job:
        job = Job(title=title, description=description)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
