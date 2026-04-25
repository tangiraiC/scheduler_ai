from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    raw_text: str = Field(..., description="Unstructured scheduling text")
    domain: str = Field(default="workforce_schedule", description="Scheduling domain")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ParseResponse(BaseModel):
    status: str
    extracted_data: Dict[str, Any]
