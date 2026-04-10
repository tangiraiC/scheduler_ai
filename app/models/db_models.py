from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobStatus:
    RECEIVED = "received"
    PARSED = "parsed"
    NORMALIZED = "normalized"
    GRAPH_BUILT = "graph_built"
    SCHEDULED = "scheduled"
    VALIDATED = "validated"
    FAILED = "failed"


class JobDocument(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    domain: str = Field(default="workforce", description="Scheduling domain")
    raw_text: Optional[str] = Field(default=None, description="Original user input")
    extracted_constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw extracted constraints from the language model"
    )
    normalized_constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Normalized constraints used by downstream services"
    )
    graph_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Graph metadata such as node count, edge count, density"
    )
    status: str = Field(default=JobStatus.RECEIVED, description="Current job status")
    error_message: Optional[str] = Field(default=None, description="Failure reason if job failed")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal issues")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AssignmentRecord(BaseModel):
    assignment_id: str = Field(..., description="Unique assignment identifier")
    worker_id: str = Field(..., description="Assigned worker ID")
    worker_name: str = Field(..., description="Assigned worker name")
    location_id: str = Field(..., description="Assigned location ID")
    location_name: str = Field(..., description="Assigned location name")
    day: str = Field(..., description="Assigned day")
    shift_id: str = Field(..., description="Assigned shift ID")
    shift_label: str = Field(..., description="Assigned shift label")
    start_time: str = Field(..., description="Shift start time")
    end_time: str = Field(..., description="Shift end time")
    duration_hours: int = Field(..., ge=1, description="Shift duration in hours")


class ScheduleDocument(BaseModel):
    schedule_id: str = Field(..., description="Unique schedule identifier")
    job_id: str = Field(..., description="Related job identifier")
    feasible: bool = Field(..., description="Whether the schedule is feasible")
    assignments: List[AssignmentRecord] = Field(
        default_factory=list,
        description="Final schedule assignments"
    )
    unfilled_demands: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Demands that could not be assigned"
    )
    validation_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from constraint validation"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime and graph/schedule metrics"
    )
    created_at: datetime = Field(default_factory=utc_now)