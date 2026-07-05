import logging
from typing import List, Dict

logger = logging.getLogger("app.services.intent_service")

# Synonym dictionary for Query Expansion
_SYNONYM_MAP: Dict[str, List[str]] = {
    "jwt": ["json web token", "bearer token", "oauth"],
    "auth": ["authentication", "authorization", "oauth", "security"],
    "db": ["database", "postgres", "sql", "orm", "sqlalchemy"],
    "docker": ["container", "dockerfile", "networking", "compose"],
}


class IntentService:
    """
    Module 6 & 7: Query Intent Detection & Query Expansion
    """

    @staticmethod
    def detect_intent(query: str) -> str:
        """
        Detects query intent: debug, code, summarize, compare, translate, or general search.
        """
        q = query.lower()
        if any(w in q for w in ["error", "bug", "traceback", "exception", "debug", "fail"]):
            return "Debug"
        if any(w in q for w in ["code", "write", "function", "class", "syntax", "implementation"]):
            return "Code"
        if any(w in q for w in ["summarize", "summary", "tl;dr", "outline"]):
            return "Summarize"
        if any(w in q for w in ["compare", "vs", "difference", "better"]):
            return "Compare"
        if any(w in q for w in ["translate", "language", "convert"]):
            return "Translate"
        return "Search Documentation"

    @staticmethod
    def expand_query(query: str) -> List[str]:
        """
        Expands the user query using synonyms and related abbreviations.
        """
        words = query.lower().split()
        expanded = set(words)

        for word in words:
            if word in _SYNONYM_MAP:
                expanded.update(_SYNONYM_MAP[word])

        return list(expanded)
