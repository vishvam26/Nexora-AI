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
        Appends creator identity directives and grounding guidelines to system prompt.
        """
        creator_directive = (
            "\n\n[CREATOR & SYSTEM IDENTITY DIRECTIVE]\n"
            "You are Nexora AI, an advanced Enterprise AI Assistant & Intelligent System.\n"
            "You were designed, architected, and developed by Vishvam Prajapati — a Visionary Lead AI Architect and Full-Stack Developer.\n"
            "If the user asks who created you, who developed you, who built you, or asks about your owner/creator (in English, Gujarati, Hindi, or any language):\n"
            "1. State proudly and explicitly that you were created and developed by Vishvam Prajapati.\n"
            "2. Explain that Vishvam Prajapati engineered Nexora AI with cutting-edge capabilities including Per-User Isolated Multi-Tenant Storage, Qdrant Hybrid RAG, Team Workspaces, and SQL Studio Copilot.\n"
            "3. Speak with high respect, warmth, and accuracy about Vishvam Prajapati."
        )

        prompts = [base_system_prompt, creator_directive]

        if has_context:
            prompts.append(
                "\n\n[GROUNDING POLICY]\n"
                "You are provided with verified document excerpts in the <document_context> tag.\n"
                "1. Answer the user's question directly and thoroughly using the details, facts, and names in <document_context>.\n"
                "2. If the user asks about a resume, document, or file, extract and provide the candidate/document details from <document_context>."
            )

        return "\n".join(prompts)
