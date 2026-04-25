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
        timeout: int = 300,
    ) -> None:
        self.base_url = (base_url or settings.lmstudio_api_url).rstrip("/")
        self.api_url = self.base_url if self.base_url.endswith("/v1") else f"{self.base_url}/v1"
        self.model_name = model_name or settings.lmstudio_model_name
        self.timeout = timeout
        self.chat_url = f"{self.api_url}/chat/completions"
        self.models_url = f"{self.api_url}/models"

    def health_check(self) -> Dict[str, Any]:
        try:
            response = requests.get(self.models_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise LMStudioClientError(f"LM Studio health check failed: {exc}") from exc

    def list_models(self) -> list[str]:
        try:
            response = requests.get(self.models_url, timeout=10)
            response.raise_for_status()
            payload = response.json()
            return [item["id"] for item in payload.get("data", [])]
        except requests.RequestException as exc:
            raise LMStudioClientError(f"LM Studio models request failed: {exc}") from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise LMStudioClientError("LM Studio returned invalid models response") from exc

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.01,
        max_tokens: int = 8000,
    ) -> str:
        payload = {
            "model": self.model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"System instructions:\n{system_prompt}\n\n"
                        f"User request:\n{user_prompt}"
                    ),
                },
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
        max_tokens: int = 8000,
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
