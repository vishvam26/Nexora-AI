import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("app.services.context_builder")


class ContextBuilder:
    """
    Assembles the final prompt payload for AI inference.

    Injection order (per PRD Volume 2 Part 3):
        ① System Prompt
        ② Developer Prompt
        ③ Workspace Memory
        ④ Conversation Summary
        ⑤ Retrieved Context (Hybrid Search)
        ⑥ Knowledge Graph Context
        ⑦ Recent History
        ⑧ User Message
    """

    @staticmethod
    def build(
        user_message: str,
        system_prompt: str = "",
        developer_prompt: str = "",
        workspace_memory: str = "",
        conversation_summary: str = "",
        retrieved_knowledge: str = "",
        graph_knowledge: str = "",
        recent_messages: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Returns a messages list compatible with OpenAI-compatible chat completion APIs.
        """
        messages: List[Dict[str, str]] = []
        system_parts: List[str] = []

        # ① System Prompt
        if system_prompt:
            system_parts.append(system_prompt)

        # ② Developer Prompt
        if developer_prompt:
            system_parts.append(f"\n\n[Developer Instructions]\n{developer_prompt}")

        # ③ Workspace Memory
        if workspace_memory:
            system_parts.append(f"\n\n[Workspace Memory]\n{workspace_memory}")

        # ④ Conversation Summary
        if conversation_summary:
            system_parts.append(f"\n\n[Conversation Summary]\n{conversation_summary}")

        # ⑤ Retrieved Context
        if retrieved_knowledge and retrieved_knowledge.strip() and retrieved_knowledge != "No relevant knowledge found.":
            system_parts.append(
                f"\n\n[Retrieved Context]\n"
                f"Use the following search matches to answer:\n\n{retrieved_knowledge}"
            )

        # ⑥ Knowledge Graph Context
        if graph_knowledge and graph_knowledge.strip():
            system_parts.append(
                f"\n\n[Knowledge Graph Connections]\n"
                f"Related context concepts found in knowledge base:\n{graph_knowledge}"
            )

        if system_parts:
            messages.append({"role": "system", "content": "\n".join(system_parts)})

        # ⑦ Recent Conversation History
        if recent_messages:
            messages.extend(recent_messages)

        # ⑧ Current User Message
        messages.append({"role": "user", "content": user_message})

        return messages
