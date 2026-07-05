import logging
from typing import List, Dict, Any

logger = logging.getLogger("app.services.context_service")

NO_RESULTS_MESSAGE = "No relevant knowledge found."


class ContextService:
    """
    Formats ranked RAG chunks into a structured, human-readable knowledge block
    ready to be injected into the AI prompt.
    """

    @staticmethod
    def format_context(chunks: List[Dict[str, Any]]) -> str:
        """
        Merges ranked chunks into a structured knowledge block.

        Output format:
            [Knowledge Base: My Docs]
            Document: Python Guide (Page 2)
            ---
            <chunk text>

            [Knowledge Base: Dev Notes]
            Document: FastAPI Notes
            ---
            <chunk text>

        Returns NO_RESULTS_MESSAGE if no chunks provided.
        """
        if not chunks:
            return NO_RESULTS_MESSAGE

        # Group chunks by knowledge base + document for clean formatting
        sections: Dict[str, Dict[str, List[str]]] = {}

        for chunk in chunks:
            kb_title = chunk.get("kb_title", "Knowledge Base")
            doc_filename = chunk.get("doc_filename", "Document")
            page = chunk.get("page")
            text = chunk.get("text", "").strip()

            if not text:
                continue

            if kb_title not in sections:
                sections[kb_title] = {}

            # Compose document key with optional page number
            doc_key = doc_filename
            if page:
                doc_key = f"{doc_filename} (Page {page})"

            if doc_key not in sections[kb_title]:
                sections[kb_title][doc_key] = []

            sections[kb_title][doc_key].append(text)

        if not sections:
            return NO_RESULTS_MESSAGE

        # Build formatted output
        lines: List[str] = []
        for kb_title, docs in sections.items():
            lines.append(f"[Knowledge Base: {kb_title}]")
            for doc_name, texts in docs.items():
                lines.append(f"Document: {doc_name}")
                lines.append("---")
                lines.extend(texts)
                lines.append("")  # blank line between documents

        return "\n".join(lines).strip()

    @staticmethod
    def has_results(chunks: List[Dict[str, Any]]) -> bool:
        """Returns True if there are any non-empty chunks available."""
        return bool(chunks and any(c.get("text") for c in chunks))
