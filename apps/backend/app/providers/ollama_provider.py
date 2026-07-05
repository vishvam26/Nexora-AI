from typing import List, Generator
from fastapi import HTTPException, status
from openai import OpenAI
from app.config import settings
from app.providers.provider_interface import AIProviderInterface


class OllamaProvider(AIProviderInterface):
    """
    Provider implementation for local Ollama API (using OpenAI-compatible endpoint).
    """

    def __init__(self):
        self.api_base = f"{settings.OLLAMA_URL.rstrip('/')}/v1"
        self.model = settings.OLLAMA_MODEL

        # Ollama local doesn't require a key
        self.client = OpenAI(api_key="ollama", base_url=self.api_base)

    def generate_response(self, messages: List[dict]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama error: {str(e)}"
            )

    def generate_stream_response(self, messages: List[dict]) -> Generator[str, None, None]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ollama stream error: {str(e)}"
            )
