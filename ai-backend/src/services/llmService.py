import os
import httpx
from fastapi import HTTPException

class LLMService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    async def generate_response(self, prompt: str, model: str | None = None) -> str:
        selected_model = model or self.default_model
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Ollama error: {response.text}"
                    )

                data = response.json()
                return data.get("response", "")

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is running."
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Ollama request timed out."
            )
