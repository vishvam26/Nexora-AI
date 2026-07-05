import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.message import Message


class DatasetExporterService:
    """
    Module 9: Continuous Learning Dataset Builder
    Exports conversation threads into popular training dataset formats (ShareGPT, OpenAI, Alpaca).
    """

    @staticmethod
    def export_sharegpt(messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Formats list of messages into ShareGPT representation:
        { "conversations": [ { "from": "human", "value": "..." } ] }
        """
        conversations = []
        for msg in messages:
            role_map = {"user": "human", "assistant": "gpt", "system": "system"}
            conversations.append({
                "from": role_map.get(msg.role, "human"),
                "value": msg.content
            })
        return [{"conversations": conversations}]

    @staticmethod
    def export_openai(messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Formats list of messages into OpenAI chat messages format:
        { "messages": [ { "role": "user", "content": "..." } ] }
        """
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        return [{"messages": formatted}]

    @staticmethod
    def export_alpaca(messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Formats list of messages into Alpaca instruction-following format:
        { "instruction": "...", "input": "...", "output": "..." }
        """
        dataset = []
        # Group adjacent pairs of User and Assistant messages
        for i in range(len(messages) - 1):
            if messages[i].role == "user" and messages[i + 1].role == "assistant":
                dataset.append({
                    "instruction": "Respond to user prompt accurately.",
                    "input": messages[i].content,
                    "output": messages[i + 1].content
                })
        return dataset
