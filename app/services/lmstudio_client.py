import json
from typing import Any, Dict, Optional

import requests

from app.core.config import settings


class LMStudioClientError(Exception):
    pass


class LMStudioClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.base_url = (base_url or settings.lmstudio_api_url).rstrip("/")
        self.model_name = model_name or settings.lmstudio_model_name
        self.timeout = timeout
        self.chat_url = f"{self.base_url}/v1/chat/completions"
        self.models_url = f"{self.base_url}/v1/models"

    def health_check(self) -> Dict[str, Any]:
        try:
            response = requests.get(self.models_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise LMStudioClientError(f"LM Studio health check failed: {exc}") from exc

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1200,
    ) -> str:
        payload = {
            "model": self.model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            response = requests.post(
                self.chat_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise LMStudioClientError(f"LM Studio request failed: {exc}") from exc
        except ValueError as exc:
            raise LMStudioClientError("LM Studio returned invalid HTTP JSON response") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LMStudioClientError(f"Unexpected LM Studio response shape: {data}") from exc

        if not isinstance(content, str):
            raise LMStudioClientError(f"Model content is not a string: {content}")

        return content.strip()

    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1200,
    ) -> Dict[str, Any]:
        content = self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise LMStudioClientError(f"Model returned non-JSON content: {content}") from exc