import logging
from typing import Dict, Any

logger = logging.getLogger("app.services.cost_service")

# Approximate pricing per 1K tokens (mocked USD)
PRICING = {
    "prompt": 0.0015,
    "completion": 0.0020,
    "embedding": 0.0001
}


class CostService:
    """
    Module 11: Cost Tracking
    Tracks token usages and calculates estimated API costs.
    """

    @staticmethod
    def calculate_cost(prompt_tokens: int, completion_tokens: int, embedding_tokens: int = 0) -> Dict[str, Any]:
        """
        Calculates cost based on token counts.
        """
        p_cost = (prompt_tokens / 1000.0) * PRICING["prompt"]
        c_cost = (completion_tokens / 1000.0) * PRICING["completion"]
        e_cost = (embedding_tokens / 1000.0) * PRICING["embedding"]

        total = p_cost + c_cost + e_cost

        return {
            "prompt_cost": round(p_cost, 6),
            "completion_cost": round(c_cost, 6),
            "embedding_cost": round(e_cost, 6),
            "total_cost": round(total, 6),
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "embedding": embedding_tokens,
                "total": prompt_tokens + completion_tokens + embedding_tokens
            }
        }
