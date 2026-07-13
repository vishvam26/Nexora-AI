import re
import logging
from typing import List, Set

logger = logging.getLogger("app.services.query_service")

# Common English stop words — safe minimal list for query cleaning
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "up", "about", "into", "through", "during", "it", "its", "this",
    "that", "these", "those", "i", "me", "my", "we", "our", "you", "your",
    "he", "she", "they", "their", "what", "which", "who", "how", "when",
    "where", "why", "and", "but", "or", "so", "if", "then", "than", "just",
}


class QueryService:
    """
    Processes and normalises user queries before embedding generation.
    Produces cleaner, more discriminative search terms.
    """

    @staticmethod
    def process_query(raw_query: str) -> str:
        """
        Full query cleaning pipeline:
        1. Lowercase
        2. Remove special characters / punctuation
        3. Collapse whitespace
        4. Remove stop words
        5. Return normalised query string
        """
        if not raw_query or not raw_query.strip():
            return ""

        # Step 1: Lowercase
        text = raw_query.lower()

        # Step 2: Remove punctuation (keep alphanumeric and spaces)
        text = re.sub(r"[^\w\s]", " ", text)

        # Step 3: Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Step 4: Remove stop words — keep only meaningful terms
        tokens = text.split()
        meaningful = [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]

        if not meaningful:
            # If all words were stop words, fall back to original cleaned text
            return text

        return " ".join(meaningful)

    @staticmethod
    def extract_keywords(raw_query: str) -> List[str]:
        """Returns list of meaningful keyword tokens from the query."""
        processed = QueryService.process_query(raw_query)
        return processed.split() if processed else []

    @staticmethod
    def classify(query: str) -> dict:
        """
        Classifies incoming query string.
        Returns a dict containing 'category' (str) and 'confidence' (float).
        """
        q = query.lower().strip()
        if not q:
            return {"category": "Greeting", "confidence": 1.0}

        # Greetings - check as whole words for short greetings to avoid matching substrings like "this"
        words = q.split()
        greeting_words = {"hi", "hello", "hey"}
        if any(w in greeting_words for w in words) or any(phrase in q for phrase in ["good morning", "good afternoon"]):
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

