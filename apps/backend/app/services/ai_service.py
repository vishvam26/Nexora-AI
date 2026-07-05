from typing import List, Generator
from app.providers.provider_factory import ProviderFactory


from app.config import settings

class AIService:
    """
    Service layer abstracting interactions with various LLM providers using Provider Architecture.
    """

    @staticmethod
    def generate_response(messages: List[dict]) -> str:
        """
        Instantiates the configured provider and generates a completion response.
        """
        if settings.AI_PROVIDER.lower().strip() == "mock":
            # Return high-quality RAG/Analytical mock answer
            last_prompt = messages[-1].get("content", "")
            if "JSON" in last_prompt:
                return '{"score": 0.85, "faithfulness": 0.90, "answer_relevance": 0.85, "confidence_score": 0.88, "root_cause": "None", "domain_tag": "Finance"}'
            return "Based on the retrieved business metrics, the company performance registers a positive trend with a growth of 12% quarter-on-quarter. The profit margins are sustained at 24%."

        provider = ProviderFactory.get_provider()
        return provider.generate_response(messages)

    @staticmethod
    def generate_stream_response(messages: List[dict]) -> Generator[str, None, None]:
        """
        Instantiates the configured provider and yields token completions dynamically.
        """
        if settings.AI_PROVIDER.lower().strip() == "mock":
            # Stream token response
            tokens = ["Based ", "on ", "retrieved ", "metrics, ", "the ", "revenue ", "registered ", "a ", "12% ", "growth. ", "Profit ", "margin ", "is ", "at ", "24%."]
            for t in tokens:
                yield t
            return

        provider = ProviderFactory.get_provider()
        return provider.generate_stream_response(messages)




