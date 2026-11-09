from abc import ABC, abstractmethod
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Generate text completion from LLM."""
        pass

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Generate structured JSON response."""
        pass


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "options": {
                "temperature": temperature
            },
            "stream": False
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation failed ({self.model}): {e}")
            raise RuntimeError(f"Ollama inference error: {e}")

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt + "\nYou MUST return valid JSON only. Do not wrap in markdown or backticks."},
                {"role": "user", "content": user_prompt}
            ],
            "options": {
                "temperature": 0.1
            },
            "stream": False
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                raw_text = data.get("message", {}).get("content", "").strip()
                # Clean up if markdown fences still exist
                if raw_text.startswith("```"):
                    raw_text = raw_text.strip("`").replace("json\n", "", 1).strip()
                return json.loads(raw_text)
        except Exception as e:
            logger.error(f"Ollama JSON generation failed: {e}")
            raise RuntimeError(f"Ollama JSON extraction error: {e}")


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured.")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured.")
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return json.loads(data["choices"][0]["message"]["content"])


def get_llm_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
    ptype = (provider_type or settings.DEFAULT_LLM_PROVIDER).lower()
    if ptype == "ollama":
        return OllamaProvider()
    elif ptype == "openai":
        return OpenAIProvider()
    else:
        logger.warning(f"Unknown provider '{ptype}', defaulting to Ollama.")
        return OllamaProvider()
