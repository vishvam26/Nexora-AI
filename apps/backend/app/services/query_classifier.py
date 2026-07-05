import logging
from typing import Dict, Any

logger = logging.getLogger("app.services.query_classifier")


class QueryClassifier:
    """
    Module 2: Query Classification
    Detects semantic category of search queries to determine retrieval route.
    """

    @staticmethod
    def classify(query: str) -> Dict[str, Any]:
        """
        Classifies incoming query string.
        Returns a dict containing 'category' (str) and 'confidence' (float).
        """
        q = query.lower().strip()
        if not q:
            return {"category": "Greeting", "confidence": 1.0}

        # Greetings
        if any(w in q for w in ["hi", "hello", "hey", "good morning", "good afternoon"]):
            return {"category": "Greeting", "confidence": 0.95}

        # Debugging
        if any(w in q for w in ["error", "bug", "traceback", "exception", "debug", "failed", "crash"]):
            return {"category": "Debugging", "confidence": 0.90}

        # Coding
        if any(w in q for w in ["code", "write", "function", "class", "syntax", "implementation", "python", "javascript"]):
            return {"category": "Coding", "confidence": 0.85}

        # Summarization
        if any(w in q for w in ["summarize", "summary", "tl;dr", "outline", "brief"]):
            return {"category": "Summarization", "confidence": 0.90}

        # Comparison
        if any(w in q for w in ["compare", "vs", "difference", "better", "alternative"]):
            return {"category": "Comparison", "confidence": 0.80}

        # Document / Knowledge Search queries
        if any(w in q for w in ["search", "find", "document", "retrieve", "docs"]):
            return {"category": "Document Search", "confidence": 0.85}

        # Default classification
        return {"category": "Knowledge Search", "confidence": 0.75}
