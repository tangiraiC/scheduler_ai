import json
from typing import Any, Dict

from pydantic import ValidationError

from app.models.extraction import ExtractedConstraints
from app.services.lmstudio_client import LMStudioClient
from app.utils.json_utils import build_extraction_prompt


class ExtractionServiceError(Exception):
    pass


class ExtractionService:
    def __init__(self, max_retries: int = 3):
        self.client = LMStudioClient()
        self.max_retries = max_retries

    async def extract(self, raw_text: str) -> Dict[str, Any]:
        """
        Input: raw text
        Output: structured constraints JSON
        Retry: if JSON invalid
        """
        prompt = build_extraction_prompt(raw_text)

        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                raw_response = self.client.generate(
                    system_prompt="You extract scheduling constraints. Return only JSON.",
                    user_prompt=prompt,
                )

                cleaned = self._clean_output(raw_response)

                parsed = json.loads(cleaned)

                validated = ExtractedConstraints.model_validate(parsed)

                return {
                    "success": True,
                    "attempt": attempt,
                    "data": validated.model_dump()
                }

            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                continue

            except Exception as e:
                raise ExtractionServiceError(f"Unexpected error: {str(e)}")

        raise ExtractionServiceError(
            f"Failed after {self.max_retries} attempts. Last error: {str(last_error)}"
        )

    def _clean_output(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        elif text.startswith("```"):
            text = text[len("```"):].strip()

        if text.endswith("```"):
            text = text[:-3].strip()

        return text