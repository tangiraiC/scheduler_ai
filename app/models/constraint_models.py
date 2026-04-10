from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


VALID_DAYS = {
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
}


class WorkerConstraint(BaseModel):
    worker_id: str = Field(..., description="Unique worker identifier")
    name: str = Field(..., description="Worker display name")
    certifications: List[str] = Field(
        default_factory=list,
        description="List of certifications held by the worker"
    )
    unavailable_days: List[str] = Field(
        default_factory=list,
        description="Days the worker cannot work"
    )
    can_work_weekends: bool = Field(
        default=True,
        description="Whether the worker can be scheduled on Saturday/Sunday"
    )
    max_hours_per_window: int = Field(
        default=40,
        ge=0,
        description="Maximum allowed hours in the planning window"
    )
    max_shifts_per_window: int = Field(
        default=5,
        ge=0,
        description="Maximum allowed shifts in the planning window"
    )

    @field_validator("unavailable_days")
    @classmethod
    def validate_unavailable_days(cls, value: List[str]) -> List[str]:
        cleaned = []
        for day in value:
            day_clean = day.strip().lower()
            if day_clean not in VALID_DAYS:
                raise ValueError(f"Invalid unavailable day: {day}")
            cleaned.append(day_clean)
        return cleaned


class LocationConstraint(BaseModel):
    location_id: str = Field(..., description="Unique location identifier")
    name: str = Field(..., description="Location display name")
    required_certifications: List[str] = Field(
        default_factory=list,
        description="Certifications required to work at this location"
    )


class ShiftDefinition(BaseModel):
    shift_id: str = Field(..., description="Unique shift identifier")
    label: str = Field(..., description="Shift label, e.g. morning")
    start_time: str = Field(..., description="Shift start time, e.g. 08:00")
    end_time: str = Field(..., description="Shift end time, e.g. 16:00")
    duration_hours: int = Field(
        default=8,
        ge=1,
        description="Shift duration in hours"
    )


class DemandConstraint(BaseModel):
    demand_id: str = Field(..., description="Unique demand identifier")
    day: str = Field(..., description="Day for this demand")
    location_id: str = Field(..., description="Location that needs coverage")
    shift_id: str = Field(..., description="Shift that needs coverage")
    required_workers: int = Field(
        default=1,
        ge=1,
        description="Number of workers required for this shift"
    )

    @field_validator("day")
    @classmethod
    def validate_day(cls, value: str) -> str:
        day_clean = value.strip().lower()
        if day_clean not in VALID_DAYS:
            raise ValueError(f"Invalid day: {value}")
        return day_clean


class HardConstraintSet(BaseModel):
    max_hours_per_7_days: int = Field(default=40, ge=0)
    max_shift_length_hours: int = Field(default=8, ge=1)
    no_overlapping_assignments: bool = True
    enforce_certifications: bool = True
    enforce_availability: bool = True
    enforce_weekend_rules: bool = True


class SoftConstraintSet(BaseModel):
    balance_hours_evenly: bool = True
    minimize_weekend_assignments: bool = True
    prefer_same_location_continuity: bool = False


class SchedulingConstraints(BaseModel):
    planning_horizon_days: int = Field(default=7, ge=1)
    workers: List[WorkerConstraint] = Field(default_factory=list)
    locations: List[LocationConstraint] = Field(default_factory=list)
    shifts: List[ShiftDefinition] = Field(default_factory=list)
    demands: List[DemandConstraint] = Field(default_factory=list)
    hard_constraints: HardConstraintSet = Field(default_factory=HardConstraintSet)
    soft_constraints: Optional[SoftConstraintSet] = Field(default_factory=SoftConstraintSet)