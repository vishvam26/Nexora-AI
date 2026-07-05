import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger("app.services.pii_masking_service")

# Regex rules for personal identifiable information (PII)
PII_PATTERNS = {
    "email": re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "aadhar": re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"),
    "api_key": re.compile(r"\b(?:sk|pk|api|key|secret|token)[-_]?[\w]{20,60}\b", re.IGNORECASE),
}


class PIIMaskingService:
    """
    Module 5: PII Detection & Masking
    Identifies sensitive patterns (emails, phone numbers, API keys, credentials) and replaces them with masked tokens.
    """

    @staticmethod
    def mask_pii(text: str) -> str:
        """
        Scans and replaces PII occurrences inside text with placeholder tokens.
        """
        if not text:
            return ""

        masked_text = text
        for pii_type, regex in PII_PATTERNS.items():
            masked_text = regex.sub(f"[[MASKED_{pii_type.upper()}]]", masked_text)

        return masked_text
