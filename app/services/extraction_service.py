from app.services.lmstudio_client import LMStudioClient


class ExtractionService:
    def __init__(self) -> None:
        self.client = LMStudioClient()

    def extract(self, text: str) -> dict[str, str]:
        result = self.client.analyze_text(text)
        return {"summary": result["analysis"], "text": text}
