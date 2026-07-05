import logging
import re

logger = logging.getLogger("app.services.dataset_cleaning_service")


class DatasetCleaningService:
    """
    Module 4: Automatic Cleaning Pipeline
    Prunes dataset strings: removes empty messages, strips emojis/broken UTF, and filters out spam or short content.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans whitespaces and strips invalid formatting.
        """
        if not text:
            return ""
        # Collapse spacing
        cleaned = re.sub(r"\s+", " ", text).strip()
        # Remove raw non-printable control characters
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)
        return cleaned

    @staticmethod
    def is_spam_or_invalid(text: str) -> bool:
        """
        Returns True if the content is too short, is solely symbols/emojis, or constitutes spam.
        """
        if not text or len(text.strip()) < 3:
            return True

        # Check if text is only punctuation/emojis (no alphanumeric characters)
        if not any(char.isalnum() for char in text):
            return True

        return False
