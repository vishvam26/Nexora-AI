import logging
import requests
from typing import List, Generator
from fastapi import HTTPException, status
from openai import OpenAI
from app.config import settings
from app.providers.provider_interface import AIProviderInterface

logger = logging.getLogger("app.providers.huggingface_provider")


class HuggingFaceProvider(AIProviderInterface):
    """
    Provider implementation for Hugging Face Inference API & Router API.
    Supports both custom fine-tuned user repos (via direct Inference API) 
    and open-source models via Router API.
    """

    def __init__(self):
        self.api_key = settings.HF_TOKEN
        self.model = settings.NEXORA_MODEL_ID or "vishvam26/nexora-qwen3.5-4b-merged"
        self.router_url = "https://router.huggingface.co/v1"
        self.direct_url = f"https://api-inference.huggingface.co/models/{self.model}"

        if not self.api_key or "hf_" not in self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Hugging Face Token (HF_TOKEN) is missing or invalid in environment."
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.client = OpenAI(api_key=self.api_key, base_url=self.router_url)

    def _call_direct_api(self, prompt: str) -> str:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": settings.NEXORA_MAX_NEW_TOKENS,
                "temperature": settings.NEXORA_TEMPERATURE,
                "return_full_text": False
            }
        }
        resp = requests.post(self.direct_url, headers=self.headers, json=payload, timeout=30)
        if resp.status_code == 200:
            res = resp.json()
            if isinstance(res, list) and len(res) > 0 and "generated_text" in res[0]:
                return res[0]["generated_text"]
            elif isinstance(res, dict) and "generated_text" in res:
                return res["generated_text"]
            return str(res)
        elif resp.status_code == 503:
            logger.info("Model warming up on Hugging Face Inference API...")
            raise Exception("Model warming up on Hugging Face")
        else:
            raise Exception(f"Direct API HTTP {resp.status_code}: {resp.text}")

    def generate_response(self, messages: List[dict]) -> str:
        prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                prompt = m.get("content", "")
                break

        # Try direct Hugging Face Inference API for custom user model
        try:
            return self._call_direct_api(prompt)
        except Exception as e:
            logger.warning(f"Direct HF Inference API for {self.model} failed: {e}. Trying HF Router fallback.")
            # Fallback to Hugging Face Router API using Qwen 2.5 Coder
            try:
                fallback_model = "Qwen/Qwen2.5-Coder-32B-Instruct"
                response = self.client.chat.completions.create(
                    model=fallback_model,
                    messages=messages
                )
                return response.choices[0].message.content
            except Exception as router_err:
                logger.error(f"HF Router fallback failed: {router_err}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Hugging Face Inference error: {str(e)}"
                )

    def generate_stream_response(self, messages: List[dict]) -> Generator[str, None, None]:
        prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                prompt = m.get("content", "")
                break

        # Try direct API first
        try:
            full_text = self._call_direct_api(prompt)
            words = full_text.split(" ")
            for i, w in enumerate(words):
                yield w + (" " if i < len(words) - 1 else "")
            return
        except Exception as e:
            logger.warning(f"Direct HF Stream API failed: {e}. Switching to HF Router fallback.")
            try:
                fallback_model = "Qwen/Qwen2.5-Coder-32B-Instruct"
                response = self.client.chat.completions.create(
                    model=fallback_model,
                    messages=messages,
                    stream=True
                )
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as router_err:
                logger.error(f"HF Stream fallback failed: {router_err}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Hugging Face Stream error: {str(e)}"
                )

