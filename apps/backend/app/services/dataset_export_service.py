import logging
from typing import List, Dict, Any
from app.models.message import Message

logger = logging.getLogger("app.services.dataset_export_service")


class DatasetExportService:
    """
    Module 15: Export Formats
    Formats messages into ShareGPT, OpenAI, Alpaca, ChatML, JSON, and JSONL formats.
    """

    @staticmethod
    def format_sharegpt(messages: List[Message]) -> List[Dict[str, Any]]:
        """ShareGPT style formatting."""
        conversations = []
        role_map = {"user": "human", "assistant": "gpt", "system": "system"}
        for m in messages:
            conversations.append({
                "from": role_map.get(m.role, "human"),
                "value": m.content
            })
        return [{"conversations": conversations}]

    @staticmethod
    def format_openai(messages: List[Message]) -> List[Dict[str, Any]]:
        """OpenAI chat format."""
        formatted = []
        for m in messages:
            formatted.append({
                "role": m.role,
                "content": m.content
            })
        return [{"messages": formatted}]

    @staticmethod
    def format_alpaca(messages: List[Message]) -> List[Dict[str, Any]]:
        """Alpaca instruction format."""
        dataset = []
        for i in range(len(messages) - 1):
            if messages[i].role == "user" and messages[i + 1].role == "assistant":
                dataset.append({
                    "instruction": "Respond to user prompt accurately.",
                    "input": messages[i].content,
                    "output": messages[i + 1].content
                })
        return dataset

    @staticmethod
    def format_chatml(messages: List[Message]) -> str:
        """ChatML representation: <|im_start|>user...<|im_end|>"""
        lines = []
        for m in messages:
            lines.append(f"<|im_start|>{m.role}\n{m.content}<|im_end|>")
        return "\n".join(lines)
