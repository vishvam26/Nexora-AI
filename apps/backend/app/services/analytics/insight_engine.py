import logging
from typing import Dict, Any, Optional

from app.services.ai_service import AIService

logger = logging.getLogger("app.services.analytics.insight_engine")


class AIInsightEngine:
    """
    AI Insight Engine.
    Stateless LLM explainer that consumes dataset profiles from the AnalyticsEngine
    and writes statistical summaries, correlation callouts, and recommendations.
    """

    @classmethod
    def generate_insights(cls, profile: Dict[str, Any], focus_query: Optional[str] = None) -> str:
        """
        Sends the dataset profile stats to the LLM to get business insights.
        """
        if "error" in profile:
            return f"Cannot generate insights: {profile['error']}"

        # 1. Format metadata for LLM
        rows = profile.get("rows_count", 0)
        cols = profile.get("columns_count", 0)
        col_names = [c["name"] for c in profile.get("columns", [])]
        
        # Select numeric stats summary
        numeric_summary = {}
        for col, stats in profile.get("descriptive_stats", {}).items():
            numeric_summary[col] = {
                "mean": stats.get("mean"),
                "median": stats.get("median"),
                "std_dev": stats.get("std_dev")
            }

        # Select correlation summary
        corr_summary = {}
        for col, pairings in profile.get("correlation_matrix", {}).items():
            # Filter high correlations to prevent token bloating
            corr_summary[col] = {k: round(v, 2) for k, v in pairings.items() if abs(v) > 0.4 and k != col}

        quality = profile.get("quality_report", {})
        outliers = {col: rep.get("count") for col, rep in profile.get("outlier_reports", {}).items()}

        # 2. Build system directives
        system_instructions = (
            "You are a Principal Business Data Analyst. Your goal is to analyze the provided dataset summary "
            "statistics and generate 3 key, highly specific business insights.\n"
            "Guidelines:\n"
            "1. Ground your answers strictly on the provided column statistics, rows, and correlations.\n"
            "2. Highlight concrete numbers (e.g. average, outliers count, or correlations) in each insight.\n"
            "3. Format each insight as a bullet point with a bold title (e.g., '1. **Strong Correlation between X and Y**').\n"
            "4. Keep it concise, professional, and actionable. Do not hallucinate or speculate on fields not present."
        )

        user_prompt = (
            f"Here is the dataset profile for the analytics review:\n"
            f"- Total Rows: {rows:,} | Total Columns: {cols}\n"
            f"- Column Names: {', '.join(col_names)}\n"
            f"- Summary Statistics: {json_dumps_safe(numeric_summary)}\n"
            f"- Significant Correlations (Pearson): {json_dumps_safe(corr_summary)}\n"
            f"- Outlier Counts: {json_dumps_safe(outliers)}\n"
            f"- Data Quality Warnings: {quality.get('warnings', [])}\n\n"
        )

        if focus_query:
            user_prompt += f"The user is particularly interested in this focus area: '{focus_query}'\n"

        user_prompt += "Generate the 3 key statistical insights now:"

        prompt_messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": user_prompt}
        ]

        try:
            logger.info("Invoking LLM for dataset insights generation...")
            insights = AIService.generate_response(prompt_messages)
            return insights
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            return "Failed to generate AI insights due to LLM provider timeout."


def json_dumps_safe(data: Any) -> str:
    import json
    try:
        return json.dumps(data)
    except Exception:
        return str(data)
