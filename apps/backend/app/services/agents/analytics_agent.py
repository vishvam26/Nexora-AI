"""
AnalyticsAgent — Step 11 Multi-Agent Orchestration

Specialized agent that wraps AnalyticsEngine and AIInsightEngine.
The Manager invokes this when the CEO's question involves:
  - Dataset statistics, distributions, trends
  - EDA, outlier detection, missing values
  - KPI identification
  - Correlation analysis

Tools available to Manager:
  - run_dataset_profile   → full EDA + column stats + outliers + missing values
  - detect_outliers       → just the outlier analysis
  - get_kpis              → auto-generated KPIs from the profile
  - get_ai_insights       → LLM-generated business insights from the analytics engine
"""
import logging
from typing import Dict, Any

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger("app.services.agents.analytics_agent")


class AnalyticsAgent(BaseAgent):
    name = "analytics_agent"
    description = (
        "Analyzes tabular datasets (CSV/Excel). "
        "Provides: descriptive statistics, EDA, outlier detection, correlation matrix, "
        "auto-generated KPIs, and AI-powered business insights. "
        "Invoke when the question involves dataset quality, distributions, trends, or statistical patterns."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        if not context.doc_id or not context.file_path:
            return AgentResult.skipped(
                self.name, task,
                "No doc_id or file_path provided. Analytics requires a tabular dataset."
            )

        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []

        # ── Tool 1: Full Dataset Profile ─────────────────────────────
        try:
            from app.services.analytics.analytics_engine import AnalyticsEngine
            profile = AnalyticsEngine.get_profile(context.doc_id, context.file_path)
            if "error" not in profile:
                output["profile"] = profile
                tool_calls.append("AnalyticsEngine.get_profile")
                rows = profile.get("row_count", "?")
                cols = profile.get("column_count", "?")
                summaries.append(f"Dataset: {rows} rows × {cols} columns.")

                # Outlier summary
                outliers = profile.get("outliers", {})
                outlier_cols = [c for c, v in outliers.items() if v.get("count", 0) > 0]
                if outlier_cols:
                    summaries.append(f"Outliers detected in: {', '.join(outlier_cols)}.")

                # Missing value summary
                missing = profile.get("missing_values", {})
                miss_cols = [(c, v) for c, v in missing.items() if v > 0]
                if miss_cols:
                    miss_str = ", ".join(f"{c}={v}" for c, v in miss_cols[:5])
                    summaries.append(f"Missing values: {miss_str}.")

                # Top correlated columns
                correlations = profile.get("correlations", {})
                if correlations:
                    output["correlations"] = correlations
                    tool_calls.append("AnalyticsEngine.correlations")
        except Exception as e:
            logger.warning(f"[AnalyticsAgent] Profile failed: {e}")
            summaries.append(f"Dataset profile unavailable: {e}")

        # ── Tool 2: AI Insights (LLM-generated business observations) ─
        try:
            from app.services.analytics.insight_engine import AIInsightEngine
            if output.get("profile"):
                insights = AIInsightEngine.generate_insights(
                    output["profile"], focus_query=task
                )
                output["ai_insights"] = insights
                tool_calls.append("AIInsightEngine.generate_insights")
                # Take first 2 insight sentences for summary
                if insights:
                    summaries.append(insights[:300])
        except Exception as e:
            logger.warning(f"[AnalyticsAgent] AI insights failed: {e}")

        if not output:
            return AgentResult.error_result(self.name, task, "All analytics tools failed.")

        return AgentResult(
            agent_name=self.name,
            task=task,
            status="success",
            output=output,
            summary=" ".join(summaries) or "Analytics profile generated.",
            tool_calls=tool_calls,
        )

    def get_tool_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Specific analytics task, e.g. 'analyze churn distribution' or 'find outliers in income column'",
                        }
                    },
                    "required": ["task"],
                },
            },
        }
