from typing import List, Optional

from pydantic import BaseModel, Field


class EmployeeExtraction(BaseModel):
    name: str
    skills: List[str] = Field(default_factory=list)
    availability: List[str] = Field(default_factory=list)
    max_shifts_per_week: Optional[int] = None
    cannot_work_with: List[str] = Field(default_factory=list)


class ShiftExtraction(BaseModel):
    id: Optional[str] = None
    day: str
    time: str
    location: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    min_staff: int = 1
    max_staff: int = 1


class ExtractionEntities(BaseModel):
    employees: List[EmployeeExtraction] = Field(default_factory=list)
    shifts: List[ShiftExtraction] = Field(default_factory=list)


class ExtractionConstraintSet(BaseModel):
    hard_constraints: List[str] = Field(default_factory=list)
    soft_constraints: List[str] = Field(default_factory=list)


class ExtractedConstraints(BaseModel):
    job_type: str = "workforce_schedule"
    entities: ExtractionEntities = Field(default_factory=ExtractionEntities)
    constraints: ExtractionConstraintSet = Field(default_factory=ExtractionConstraintSet)
