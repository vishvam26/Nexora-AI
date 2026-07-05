import re
import csv
import json
import html
import logging
import hashlib
from io import StringIO
from typing import Optional

logger = logging.getLogger("app.services.document_processing.document_processor")

# Supported MIME types mapped to extraction strategies
TEXT_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/html",
    "text/csv",
    "application/json",
    "application/javascript",
    "text/x-python",
    "application/x-python-code",
    "text/x-java-source",
    "application/typescript",
}


class DocumentProcessor:
    """
    Extracts, normalises and sanitises raw text content from uploaded files.
    Supports TXT, Markdown, HTML, CSV, JSON, and code file formats.
    PDF/DOCX extraction returns a placeholder stub pending optional library installation.
    """

    def extract_text(self, content: bytes, mime_type: str, filename: str) -> str:
        """
        Dispatches to the correct text-extraction strategy based on MIME type.
        Returns cleaned, normalised plain text.
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # Plain text variants
        if mime_type in ("text/plain", "text/markdown") or ext in ("txt", "md", "rst"):
            return self._extract_plain(content)

        # HTML
        if mime_type == "text/html" or ext == "html":
            return self._extract_html(content)

        # CSV
        if mime_type == "text/csv" or ext == "csv":
            return self._extract_csv(content)

        # JSON
        if mime_type == "application/json" or ext == "json":
            return self._extract_json(content)

        # Source code files
        if mime_type in TEXT_MIME_TYPES or ext in ("py", "js", "ts", "java", "cpp", "c", "cs", "rb", "go", "rs"):
            return self._extract_plain(content)

        # PDF placeholder
        if mime_type == "application/pdf" or ext == "pdf":
            logger.warning("PDF extraction requires pdfminer/pypdf2 - returning placeholder.")
            return "[PDF content - install pdfminer.six for full extraction]"

        # DOCX placeholder
        if ext == "docx" or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            logger.warning("DOCX extraction requires python-docx - returning placeholder.")
            return "[DOCX content - install python-docx for full extraction]"

        # Excel placeholder
        if ext in ("xlsx", "xls") or "spreadsheetml" in mime_type:
            logger.warning("Excel extraction requires openpyxl - returning placeholder.")
            return "[Excel content - install openpyxl for full extraction]"

        # Fallback: try raw UTF-8 decode
        try:
            return self._extract_plain(content)
        except Exception:
            return "[Binary file - text extraction not supported]"

    def compute_checksum(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def detect_language(self, text: str) -> str:
        """Naive language stub - returns 'en' for now. Replace with langdetect when installed."""
        return "en"

    def count_pages(self, text: str) -> int:
        """Estimates page count: every ~3000 chars = 1 page."""
        return max(1, len(text) // 3000)

    # ---- Private extraction methods ----

    def _extract_plain(self, content: bytes) -> str:
        text = content.decode("utf-8", errors="replace")
        return self._clean(text)

    def _extract_html(self, content: bytes) -> str:
        text = content.decode("utf-8", errors="replace")
        # Strip tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        return self._clean(text)

    def _extract_csv(self, content: bytes) -> str:
        text = content.decode("utf-8", errors="replace")
        reader = csv.reader(StringIO(text))
        rows = [" | ".join(row) for row in reader]
        return self._clean("\n".join(rows))

    def _extract_json(self, content: bytes) -> str:
        text = content.decode("utf-8", errors="replace")
        try:
            obj = json.loads(text)
            # Pretty print for readability
            return self._clean(json.dumps(obj, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            return self._clean(text)

    def _clean(self, text: str) -> str:
        """Normalises whitespace, removes null bytes, and deduplicates blank lines."""
        text = text.replace("\x00", "")
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
