from abc import ABC, abstractmethod
from typing import List, Generator


class AIProviderInterface(ABC):
    """
    Interface defining standard contract for AI LLM providers.
    """

    @abstractmethod
    def generate_response(self, messages: List[dict]) -> str:
        """
        Sends the messages payload to the LLM provider and returns the model response string.
        """
        pass

    @abstractmethod
    def generate_stream_response(self, messages: List[dict]) -> Generator[str, None, None]:
        """
        Sends the messages payload and yields tokens incrementally.
        """
        pass
