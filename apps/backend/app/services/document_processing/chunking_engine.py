import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("app.services.document_processing.chunking_engine")


class ChunkingEngine:
    """
    Splits document text into smaller chunks for embedding and vector indexing.
    Supports Fixed, Recursive, Markdown-aware, and Code-aware strategies.
    """

    DEFAULT_CHUNK_SIZE = 512
    DEFAULT_OVERLAP = 64

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        strategy: str = "recursive",
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy

    def chunk(self, text: str, mime_type: str = "text/plain") -> List[Dict[str, Any]]:
        """
        Entry point: Dispatches to the right chunking strategy.
        Returns list of dicts with keys: text, chunk_index, token_count, page, section.
        """
        if self.strategy == "fixed":
            raw_chunks = self._fixed_chunks(text)
        elif self.strategy == "markdown" or mime_type in ("text/markdown",):
            raw_chunks = self._markdown_chunks(text)
        elif self.strategy == "code" or mime_type in ("text/x-python", "application/javascript", "application/typescript"):
            raw_chunks = self._code_chunks(text)
        else:
            # Default: recursive character splitting
            raw_chunks = self._recursive_chunks(text)

        return [
            {
                "chunk_index": i,
                "text": chunk.strip(),
                "token_count": self._estimate_tokens(chunk),
                "page": self._estimate_page(text, chunk),
                "section": None,
                "metadata": {"strategy": self.strategy},
            }
            for i, chunk in enumerate(raw_chunks)
            if chunk.strip()
        ]

    # ---- Strategies ----

    def _fixed_chunks(self, text: str) -> List[str]:
        """Splits by fixed character count with overlap."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.overlap
        return chunks

    def _recursive_chunks(self, text: str) -> List[str]:
        """
        Hierarchical split: paragraph → sentence → word.
        Tries to preserve semantic boundaries.
        """
        separators = ["\n\n", "\n", ". ", "! ", "? ", " "]
        return self._split_recursive(text, separators)

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        if not separators or len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        sep = separators[0]
        parts = text.split(sep)
        chunks = []
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # If the part itself is too large, recurse with next separator
                if len(part) > self.chunk_size:
                    chunks.extend(self._split_recursive(part, separators[1:]))
                    current = ""
                else:
                    current = part

        if current:
            chunks.append(current)

        # Apply overlap stitching between consecutive chunks
        return self._apply_overlap(chunks)

    def _markdown_chunks(self, text: str) -> List[str]:
        """Splits at Markdown headers first, then recursively splits large sections."""
        sections = re.split(r"(?=^#{1,3} )", text, flags=re.MULTILINE)
        chunks = []
        for section in sections:
            if len(section) <= self.chunk_size:
                if section.strip():
                    chunks.append(section)
            else:
                chunks.extend(self._recursive_chunks(section))
        return chunks

    def _code_chunks(self, text: str) -> List[str]:
        """Splits at function/class definitions for code files."""
        # Split at Python/JS function and class boundaries
        pattern = r"(?=\n(?:def |class |function |const |let |var |async def ))"
        parts = re.split(pattern, text)
        chunks = []
        current = ""
        for part in parts:
            if len(current) + len(part) <= self.chunk_size:
                current += part
            else:
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)
        return self._apply_overlap(chunks)

    # ---- Helpers ----

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """Stitches overlap text between consecutive chunks."""
        if self.overlap <= 0 or len(chunks) <= 1:
            return chunks
        result = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-self.overlap:]
            result.append(tail + chunks[i])
        return result

    def _estimate_tokens(self, text: str) -> int:
        """Estimates token count: ~4 chars per token (GPT-style rough estimate)."""
        return max(1, len(text) // 4)

    def _estimate_page(self, full_text: str, chunk: str) -> int:
        """Estimates 1-indexed page number for a chunk within the full document."""
        pos = full_text.find(chunk[:50])
        if pos == -1:
            return 1
        chars_per_page = 3000
        return max(1, pos // chars_per_page + 1)
