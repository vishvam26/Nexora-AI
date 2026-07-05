import logging
from typing import Dict, Any
from app.services.dataset_cleaning_service import DatasetCleaningService

logger = logging.getLogger("app.services.dataset_quality_service")


class DatasetQualityService:
    """
    Module 6: Dataset Quality Score
    Calculates sample rating scores (0-100) based on lengths, structure, and text cleaning validations.
    """

    @staticmethod
    def calculate_score(text: str, role: str) -> float:
        """
        Gives a baseline quality rating score.
        """
        if not text or DatasetCleaningService.is_spam_or_invalid(text):
            return 0.0

        score = 50.0  # Base score

        # Length boosting
        length = len(text.strip())
        if length > 50:
            score += 15.0
        if length > 200:
            score += 15.0

        # Heuristic quality boosts
        if role == "assistant":
            # Assistant answers containing bullet points or markdown tables are structured
            if any(marker in text for marker in ["- ", "* ", "|", "```"]):
                score += 20.0

        return min(100.0, score)
