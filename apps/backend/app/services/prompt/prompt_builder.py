import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("app.services.prompt.prompt_builder")


class PromptBuilder:
    """
    Enterprise-ready Prompt Builder.
    Mitigates Prompt Injection in retrieved document chunks, formats secure system contexts,
    and enforces strict anti-hallucination guardrails.
    """

    INJECTION_KEYWORDS = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"override\s+(?:all\s+)?instructions",
        r"you\s+must\s+now",
        r"system\s+prompt",
        r"act\s+as\s+a",
        r"bypass\s+the\s+safety",
        r"delete\s+all\s+files",
        r"forget\s+what\s+I\s+said",
    ]

    @classmethod
    def sanitize_chunk(cls, text: str) -> str:
        """
        Scans document chunk for malicious prompt injection phrases and neutralizes them.
        """
        sanitized = text
        for pattern in cls.INJECTION_KEYWORDS:
            # Case-insensitive replacement with warning message
            sanitized = re.sub(
                pattern, 
                "[Neutralized Potential Instruction Injection Attempt]", 
                sanitized, 
                flags=re.IGNORECASE
            )
        return sanitized

    @classmethod
    def enclose_context(cls, formatted_chunks: str) -> str:
        """
        Encloses context chunks inside clean document context tags.
        """
        if not formatted_chunks or not formatted_chunks.strip():
            return ""

        return (
            "\n\n--- RETRIEVED DOCUMENT CONTEXT ---\n"
            "<document_context>\n"
            f"{formatted_chunks}\n"
            "</document_context>\n"
            "--- END RETRIEVED DOCUMENT CONTEXT ---"
        )

    @classmethod
    def build_system_prompt(cls, base_system_prompt: str, has_context: bool) -> str:
        """
        Appends strict grounding guidelines to the base system prompt.
        """
        prompts = [base_system_prompt]

        if has_context:
            prompts.append(
                "\n\n[GROUNDING POLICY]\n"
                "You are provided with verified document excerpts in the <document_context> tag.\n"
                "1. Answer the user's question directly and thoroughly using the details, facts, and names in <document_context>.\n"
                "2. If the user asks about a resume, document, or file, extract and provide the candidate/document details from <document_context>."
            )

        return "\n".join(prompts)
