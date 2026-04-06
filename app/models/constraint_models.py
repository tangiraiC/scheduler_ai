from enum import Enum

from pydantic import BaseModel


class ConstraintType(str, Enum):
    time = "time"
    location = "location"
    resource = "resource"


class Constraint(BaseModel):
    type: ConstraintType
    value: str
