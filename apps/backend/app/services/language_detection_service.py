import logging

logger = logging.getLogger("app.services.language_detection_service")


class LanguageDetectionService:
    """
    Module 7: Auto Language Detection
    Detects conversation language using simple vocabulary scanning heuristic rules.
    """

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Simple heuristic word checker mapping language tags.
        """
        if not text:
            return "English"

        t = text.lower()

        # Simple vocabulary pings
        if any(w in t for w in ["hallo", "ist", "und", "nicht"]):
            return "German"
        if any(w in t for w in ["bonjour", "est", "avec", "pour"]):
            return "French"
        if any(w in t for w in ["aur", "hai", "kya", "tum"]):
            return "Hindi"
        if any(w in t for w in ["ane", "chhe", "su", "tame"]):
            return "Gujarati"
        if any(w in t for w in ["hola", "como", "con", "para"]):
            return "Spanish"

        return "English"
