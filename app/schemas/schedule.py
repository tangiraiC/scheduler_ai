from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ScheduleRequest(BaseModel):
    raw_text: Optional[str] = Field(
        default=None,
        description="Unstructured scheduling text",
    )
    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured scheduling constraints",
    )
    strategy: str = Field(default="largest_first", description="Coloring strategy")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ScheduleResponse(BaseModel):
    status: str
    job_id: Optional[str] = None
    input: Dict[str, Any]
    extracted_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    graph_summary: Dict[str, Any]
    schedule_result: Dict[str, Any]
    validation: Dict[str, Any]
    final_schedule: Dict[str, Any]
    is_valid: bool
