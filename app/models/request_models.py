from typing import List

from pydantic import BaseModel


class ParseRequest(BaseModel):
    text: str


class ScheduleRequest(BaseModel):
    constraints: List[str] = []
