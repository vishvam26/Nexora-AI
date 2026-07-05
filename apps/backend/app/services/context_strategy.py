import logging

logger = logging.getLogger("app.services.context_strategy")


class ContextStrategyEngine:
    """
    Module 3: Context Strategy Engine
    Maps query categories to optimized retrieval routing strategies.
    """

    @staticmethod
    def determine_strategy(category: str) -> str:
        """
        Returns retrieval strategy string:
        - History Only
        - History + Summary
        - Hybrid Retrieval
        - Knowledge Graph
        - Summary Only
        - No Retrieval
        """
        if category == "Greeting":
            return "No Retrieval"
        elif category in ["Summarization"]:
            return "Summary Only"
        elif category in ["Debugging", "Coding"]:
            return "Hybrid Retrieval"
        elif category in ["Comparison", "Knowledge Search", "Document Search"]:
            return "Knowledge Graph"
        return "History + Summary"
