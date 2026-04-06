from typing import Any, Dict

from app.core.config import settings


class LMStudioClient:
    def __init__(self) -> None:
        self.api_url = settings.lmstudio_api_url
        self.api_key = settings.lmstudio_api_key

    def analyze_text(self, text: str) -> Dict[str, Any]:
        return {"analysis": "placeholder", "text": text, "source": str(self.api_url)}
