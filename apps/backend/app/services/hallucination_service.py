import logging
from app.services.rag_evaluation_service import RAGEvaluationService

logger = logging.getLogger("app.services.hallucination_service")


class HallucinationService:
    """
    Module 2: Automatic Hallucination Detection
    Checks groundedness metrics and flags responses that reference ungrounded facts.
    """

    @staticmethod
    def detect_hallucination(query: str, context: str, response: str, threshold: float = 0.40) -> dict:
        """
        Runs evaluation and flags potential hallucination if groundedness is below threshold.
        """
        metrics = RAGEvaluationService.evaluate(query, context, response)
        groundedness = metrics["groundedness"]

        is_hallucinating = groundedness < threshold if context else False

        return {
            "is_hallucinating": is_hallucinating,
            "groundedness_score": groundedness,
            "threshold": threshold,
            "confidence": round(groundedness * 0.8 + 0.2, 4)
        }
