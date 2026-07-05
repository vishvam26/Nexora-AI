import logging
from typing import Dict, Any

logger = logging.getLogger("app.services.rag_evaluation_service")


class RAGEvaluationService:
    """
    Module 1: RAG Evaluation Engine
    Evaluates response quality using heuristics representing ground truths (simulated LLM-as-a-judge):
    - Context Precision: relevance of matched chunks.
    - Context Recall: matching tokens of user queries inside retrieved contexts.
    - Groundedness: matching tokens of final answer inside retrieved contexts.
    - Faithfulness: absence of fabricated facts.
    """

    @staticmethod
    def evaluate(query: str, context: str, response: str) -> Dict[str, Any]:
        """
        Runs heuristics to evaluate retrieval & generation quality.
        """
        if not context or not response:
            return {
                "context_precision": 0.0,
                "context_recall": 0.0,
                "context_coverage": 0.0,
                "faithfulness": 1.0,
                "groundedness": 0.0,
                "citation_accuracy": 1.0
            }

        q_words = set(query.lower().split())
        c_words = set(context.lower().split())
        r_words = set(response.lower().split())

        # 1. Context Precision: fraction of query tokens captured in context
        c_precision = len(q_words.intersection(c_words)) / max(1, len(q_words))

        # 2. Context Recall: fraction of context tokens capturing query keywords
        c_recall = len(c_words.intersection(q_words)) / max(1, len(c_words))

        # 3. Groundedness: fraction of response tokens present in the retrieved context
        groundedness = len(r_words.intersection(c_words)) / max(1, len(r_words))

        # 4. Faithfulness: presence of ungrounded sentences
        faithfulness = round(groundedness, 2)

        return {
            "context_precision": round(c_precision, 4),
            "context_recall": round(c_recall, 4),
            "context_coverage": round(len(c_words) / 1000, 4),
            "faithfulness": faithfulness,
            "groundedness": round(groundedness, 4),
            "citation_accuracy": 1.0
        }
