from fastapi import HTTPException, status
from app.config import settings
from app.providers.provider_interface import AIProviderInterface
from app.providers.gemini_provider import GeminiProvider
from app.providers.huggingface_provider import HuggingFaceProvider


class ProviderFactory:
    """
    Factory — Option 1: only 2 active providers (HF for chat, Gemini for copilot)
    Legacy providers kept as files but unregistered for Render free 512MB.
    To re-enable: add import + registry entry.
    """

    _registry = {
        "gemini": GeminiProvider,
        "huggingface": HuggingFaceProvider,
        "hf": HuggingFaceProvider,
        # disabled for free tier: "openai", "openrouter", "ollama", "nexora"
    }

    @classmethod
    def get_provider(cls, provider_override: str = None) -> AIProviderInterface:
        provider_name = (provider_override or settings.AI_PROVIDER).lower().strip()

        if provider_name not in cls._registry:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Configured AI provider '{provider_name}' is not registered."
            )

        provider_class = cls._registry[provider_name]
        return provider_class()
