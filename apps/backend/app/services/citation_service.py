import logging
from typing import List, Dict, Any

logger = logging.getLogger("app.services.citation_service")


class CitationEngine:
    """
    Module 9: Citation Engine
    Tracks sources and compiles citation markers (e.g. Doc A, Page 4, Chunk 18, Score 0.92)
    to append references transparently at the end of generated context.
    """

    @staticmethod
    def generate_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Creates clean citation objects for matched document blocks.
        """
        citations = []
        for index, chunk in enumerate(chunks):
            filename = chunk.get("doc_filename") or chunk.get("filename") or "Unknown Document"
            kb_title = chunk.get("kb_title") or "Workspace Knowledge Base"
            page = chunk.get("page")
            score = chunk.get("score") or chunk.get("composite_score") or 0.0

            citations.append({
                "source_index": index + 1,
                "document_name": filename,
                "knowledge_base": kb_title,
                "page": page,
                "similarity_score": round(score, 4),
            })
        return citations

    @staticmethod
    def format_citations_block(citations: List[Dict[str, Any]]) -> str:
        """
        Formats compiled citations into a text bibliography string.
        """
        if not citations:
            return ""
        lines = ["\n[Citations & Sources]:"]
        for cit in citations:
            loc = f" (Page {cit['page']})" if cit["page"] else ""
            lines.append(
                f"[{cit['source_index']}] {cit['document_name']}{loc} - "
                f"KB: {cit['knowledge_base']} (Match: {cit['similarity_score']})"
            )
        return "\n".join(lines)
