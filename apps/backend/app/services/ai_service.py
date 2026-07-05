from typing import List, Generator
from app.providers.provider_factory import ProviderFactory


class AIService:
    """
    Service layer abstracting interactions with various LLM providers using Provider Architecture.
    """

    @staticmethod
    def generate_response(messages: List[dict]) -> str:
        """
        Instantiates the configured provider and generates a completion response.
        """
        provider = ProviderFactory.get_provider()
        return provider.generate_response(messages)

    @staticmethod
    def generate_stream_response(messages: List[dict]) -> Generator[str, None, None]:
        """
        Instantiates the configured provider and yields token completions dynamically.
        """
        provider = ProviderFactory.get_provider()
        return provider.generate_stream_response(messages)



