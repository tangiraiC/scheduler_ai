from typing import Any, Dict, List

from pydantic import BaseModel


class ParseResponse(BaseModel):
    input_text: str
    extracted_data: Dict[str, Any]


class ScheduleResponse(BaseModel):
    schedule: Dict[str, Any]


class JobModel(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobModel] = []
