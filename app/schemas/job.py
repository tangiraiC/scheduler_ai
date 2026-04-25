from typing import Any, Dict

from pydantic import BaseModel


class JobResponse(BaseModel):
    status: str
    job_id: str
    job: Dict[str, Any]
