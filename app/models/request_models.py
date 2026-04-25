from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    raw_text: str = Field(..., description="Unstructured scheduling instructions from the user")
    domain: str = Field(default="workforce", description="Scheduling domain, e.g. workforce, exam")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScheduleRequest(BaseModel):
    raw_text: Optional[str] = Field(
        default=None,
        description="Unstructured scheduling input text",
    )
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured scheduling constraints",
    )
    strategy: str = Field(
        default="largest_first",
        description="Coloring / scheduling strategy, e.g. largest_first, saturation_largest_first"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    validate_only: bool = Field(
        default=False,
        description="If true, only validate constraints without generating a final schedule"
    )


class JobQueryRequest(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the scheduling job")
