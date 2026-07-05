import logging
from typing import List, Generator
from fastapi import HTTPException, status
from openai import OpenAI
from app.config import settings
from app.providers.provider_interface import AIProviderInterface

logger = logging.getLogger("app.providers.huggingface_provider")


class HuggingFaceProvider(AIProviderInterface):
    """
    Provider implementation for Hugging Face Router API (using OpenAI-compatible endpoint).
    Allows running top chat models in the cloud for free without local RAM/GPU constraints.
    """

    def __init__(self):
        self.api_key = settings.HF_TOKEN
        self.model = settings.NEXORA_MODEL_ID
        self.api_base = "https://router.huggingface.co/v1"

        if not self.api_key or "hf_" not in self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Hugging Face Token (HF_TOKEN) is not configured in .env."
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
            logger.error(f"Hugging Face Router API generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Hugging Face Cloud Inference error: {str(e)}"
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
            logger.error(f"Hugging Face Router API streaming failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Hugging Face Cloud Stream error: {str(e)}"
            )

