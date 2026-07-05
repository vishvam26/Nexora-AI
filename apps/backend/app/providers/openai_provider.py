from typing import List, Generator
from fastapi import HTTPException, status
from openai import OpenAI
from app.config import settings
from app.providers.provider_interface import AIProviderInterface


class OpenAIProvider(AIProviderInterface):
    """
    Provider implementation for OpenAI completions API.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        self.model = settings.OPENAI_MODEL

        if not self.api_key or self.api_key == "CHANGE_THIS_LATER_IN_ENV":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API Key is not configured."
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
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI error: {str(e)}"
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
                detail=f"OpenAI stream error: {str(e)}"
            )
