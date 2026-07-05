from typing import Optional
from app.services.document_processing.extractors import DocumentExtractorFactory

logger = logging.getLogger("app.services.document_processing.document_processor")


class DocumentProcessor:
    """
    Delegates text extraction to modular extractors resolved via DocumentExtractorFactory.
    """

    def extract_text(self, content: bytes, mime_type: str, filename: str) -> str:
        """
        Extracts plain text using the resolved extraction strategy.
        """
        try:
            extractor = DocumentExtractorFactory.get_extractor(mime_type, filename)
            return extractor.extract(content)
        except Exception as e:
            logger.error(f"Failed to extract text from file '{filename}': {e}", exc_info=True)
            return f"[Error: Text extraction failed for {filename}. Details: {e}]"

    def compute_checksum(self, content: bytes) -> str:
        import hashlib
        return hashlib.sha256(content).hexdigest()

    def detect_language(self, text: str) -> str:
        """Naive language stub - returns 'en' for now. Replace with langdetect when installed."""
        return "en"

    def count_pages(self, text: str) -> int:
        """Estimates page count: every ~3000 chars = 1 page."""
        return max(1, len(text) // 3000)

