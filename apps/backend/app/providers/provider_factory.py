from fastapi import HTTPException, status
from app.config import settings
from app.providers.provider_interface import AIProviderInterface
from app.providers.openai_provider import OpenAIProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.nexora_provider import NexoraProvider
from app.providers.huggingface_provider import HuggingFaceProvider


class ProviderFactory:
    """
    Factory for instantiating selected LLM providers dynamically based on configuration.
    """

    _registry = {
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
        "nexora": NexoraProvider,
        "huggingface": HuggingFaceProvider,
        "hf": HuggingFaceProvider
    }

    @classmethod
    def get_provider(cls) -> AIProviderInterface:
        provider_name = settings.AI_PROVIDER.lower().strip()

        if provider_name not in cls._registry:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Configured AI provider '{provider_name}' is not registered."
            )

        provider_class = cls._registry[provider_name]
        return provider_class()
