from typing import Any, Dict

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, Any]
