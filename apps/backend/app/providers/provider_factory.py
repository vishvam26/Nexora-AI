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

    Resilient chain: HF primary -> Gemini fallback -> mock last resort.
    Use `resilient_chain()` to get the ordered list of *configured*
    providers, so a single provider outage never becomes a 502 to the UI.
    """

    _registry = {
        "gemini": GeminiProvider,
        "huggingface": HuggingFaceProvider,
        "hf": HuggingFaceProvider,
        # disabled for free tier: "openai", "openrouter", "ollama", "nexora"
    }

    # Canonical name for aliases (hf -> huggingface, for chain dedup)
    _canonical = {
        "hf": "huggingface",
        "huggingface": "huggingface",
        "gemini": "gemini",
        "mock": "mock",
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

    @classmethod
    def is_configured(cls, provider_name: str) -> bool:
        """True if the provider has the credentials needed to run."""
        name = (provider_name or "").lower().strip()
        if name == "mock":
            return True
        if name in ("huggingface", "hf"):
            token = getattr(settings, "HF_TOKEN", "") or ""
            return bool(token) and "hf_" in token
        if name == "gemini":
            return bool(getattr(settings, "GOOGLE_API_KEY", ""))
        return name in cls._registry

    @classmethod
    def resilient_chain(cls, provider_override: str = None) -> list:
        """
        Ordered provider chain: [primary, ...fallbacks, mock].

        Default: HF primary -> Gemini fallback -> mock last resort.
        A provider_override becomes the primary; the other configured
        provider is the automatic fallback. Mock is always last so the
        API returns 200 with a graceful message instead of a 502.
        """
        primary = (provider_override or settings.AI_PROVIDER or "mock").lower().strip()
        primary_canon = cls._canonical.get(primary, primary)

        chain = []
        if primary_canon == "mock":
            return ["mock"]
        chain.append(primary_canon)

        # Preferred fallback order: gemini <-> huggingface
        for fallback in ("huggingface", "gemini"):
            if fallback != primary_canon and cls.is_configured(fallback):
                chain.append(fallback)

        chain.append("mock")
        return chain
