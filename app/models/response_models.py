from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.models.db_models import JobDocument


class ParseResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status, e.g. parsed, failed")
    extracted_constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw extracted constraints from the language model"
    )
    normalization_notes: List[str] = Field(
        default_factory=list,
        description="Notes produced during normalization"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal issues detected during parsing"
    )


class ScheduleResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status, e.g. scheduled, failed")
    feasible: bool = Field(..., description="Whether a feasible schedule was found")
    schedule: Dict[str, Any] = Field(
        default_factory=dict,
        description="Final schedule assignments"
    )
    validation_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of constraint validation results"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal issues detected during scheduling"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime, node count, edge count, etc."
    )


class ErrorResponse(BaseModel):
    job_id: str | None = None
    status: str = "failed"
    error_message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class JobListResponse(BaseModel):
    jobs: List[JobDocument] = Field(default_factory=list)
