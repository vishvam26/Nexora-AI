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
