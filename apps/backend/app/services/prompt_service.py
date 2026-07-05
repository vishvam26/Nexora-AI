import os
from typing import List, Optional
from app.config import settings
from app.models.message import Message
from app.services.context_builder import ContextBuilder


from app.services.prompt.prompt_builder import PromptBuilder


class PromptService:
    """
    Service layer responsible for loading external prompts and assembling the complete system prompts
    and final messages payload for the AI model.
    """

    @staticmethod
    def _read_prompt_file(filepath: str, default: str = "") -> str:
        """
        Helper method to read a text file safely.
        """
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                return default
        return default

    @classmethod
    def get_system_prompt(cls) -> str:
        """
        Loads the system prompt from the configured path.
        """
        path = getattr(settings, "SYSTEM_PROMPT_PATH", None)
        return cls._read_prompt_file(
            path,
            default="You are a helpful AI assistant."
        )

    @classmethod
    def get_developer_prompt(cls) -> str:
        """
        Loads the developer prompt from the configured path.
        """
        path = getattr(settings, "DEVELOPER_PROMPT_PATH", None)
        return cls._read_prompt_file(
            path,
            default=""
        )

    @classmethod
    def build_prompt(
        cls,
        history: List[Message],
        summary: Optional[str] = None,
        current_user_message: str = "",
        retrieved_knowledge: str = "",
        graph_knowledge: str = "",
        grounded: bool = False,
    ) -> List[dict]:
        """
        Constructs the final prompt payload using ContextBuilder.
        """
        system_content = cls.get_system_prompt()
        dev_content = cls.get_developer_prompt()

        if grounded:
            has_context = bool(retrieved_knowledge and retrieved_knowledge.strip())
            
            if has_context:
                # Sanitize and enclose context with injection protection
                sanitized_knowledge = PromptBuilder.sanitize_chunk(retrieved_knowledge)
                enclosed_knowledge = PromptBuilder.enclose_context(sanitized_knowledge)
                
                # Build system grounding prompt
                system_content = PromptBuilder.build_system_prompt(system_content, has_context=True)
                retrieved_knowledge = enclosed_knowledge
            else:
                # Direct strict anti-hallucination fallback prompt
                system_content = PromptBuilder.build_system_prompt(system_content, has_context=False)
                retrieved_knowledge = "No relevant information found in the selected Knowledge Base."

        # Format history as a list of dicts with role and content keys
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in history]

        # Use ContextBuilder to assemble prompt with consistent ordering
        messages = ContextBuilder.build(
            user_message=current_user_message,
            system_prompt=system_content,
            developer_prompt=dev_content,
            workspace_memory="",  # Injected here if workspace memory is active
            conversation_summary=summary or "",
            retrieved_knowledge=retrieved_knowledge,
            graph_knowledge=graph_knowledge,
            recent_messages=history_dicts,
        )

        return messages
