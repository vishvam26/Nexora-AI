from typing import List, Generator
from fastapi import HTTPException, status
from openai import OpenAI
from app.config import settings
from app.providers.provider_interface import AIProviderInterface


class GeminiProvider(AIProviderInterface):
    """
    Provider implementation for Google Gemini API (using OpenAI-compatible endpoint).
    """

    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.api_base = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.model = settings.GEMINI_MODEL

        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google API Key (for Gemini) is not configured."
            )

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)

    def generate_response(self, messages: List[dict]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_524_A_TIMEOUT_OR_CONNECTION_ERROR if "timeout" in str(e).lower() else status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini error: {str(e)}"
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
                detail=f"Gemini stream error: {str(e)}"
            )
