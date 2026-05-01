from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


def _coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


class EmployeeExtraction(BaseModel):
    name: str
    skills: List[str] = Field(default_factory=list)
    availability: List[str] = Field(default_factory=list)
    max_shifts_per_week: Optional[int] = None
    cannot_work_with: List[str] = Field(default_factory=list)

    @field_validator("skills", "availability", "cannot_work_with", mode="before")
    @classmethod
    def coerce_list_fields(cls, value: Any) -> list[Any]:
        return _coerce_list(value)


class ShiftExtraction(BaseModel):
    id: Optional[str] = None
    day: str
    time: str
    location: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    min_staff: int = 1
    max_staff: int = 1

    @field_validator("required_skills", mode="before")
    @classmethod
    def coerce_list_fields(cls, value: Any) -> list[Any]:
        return _coerce_list(value)


class ExtractionEntities(BaseModel):
    employees: List[EmployeeExtraction] = Field(default_factory=list)
    shifts: List[ShiftExtraction] = Field(default_factory=list)


class ExtractionConstraintSet(BaseModel):
    hard_constraints: List[str] = Field(default_factory=list)
    soft_constraints: List[str] = Field(default_factory=list)
    cannot_work_with_pairs: List[List[str]] = Field(default_factory=list)

    @field_validator("hard_constraints", "soft_constraints", "cannot_work_with_pairs", mode="before")
    @classmethod
    def coerce_list_fields(cls, value: Any) -> list[Any]:
        return _coerce_list(value)


class ExtractionEdge(BaseModel):
    source: str
    target: str
    type: str = "cannot_work_with"


class ExtractedConstraints(BaseModel):
    job_type: str = "workforce_schedule"
    entities: ExtractionEntities = Field(default_factory=ExtractionEntities)
    constraints: ExtractionConstraintSet = Field(default_factory=ExtractionConstraintSet)
    edges: List[ExtractionEdge] = Field(default_factory=list)


ExtractedConstraints.model_rebuild()
