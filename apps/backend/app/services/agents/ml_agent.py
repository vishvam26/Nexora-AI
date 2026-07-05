"""
MLAgent — Step 11 Multi-Agent Orchestration

Specialized agent that wraps MLService's three architecture hooks:
  - ML Session Metadata   (what model was trained, metrics)
  - SHAP Explainability   (which features drove the model's decisions)
  - Model Comparison      (which algorithm performed best)

The Manager invokes this when the CEO's question involves:
  - Model performance, accuracy, predictions
  - Feature importance ("what drives churn?")
  - Algorithm comparison
  - Running a prediction on new inputs
"""
import logging
from typing import Dict, Any

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger("app.services.agents.ml_agent")


class MLAgent(BaseAgent):
    name = "ml_agent"
    description = (
        "Accesses the trained Machine Learning model for a dataset. "
        "Provides: model performance metrics (accuracy, R², MAE), "
        "SHAP feature attributions (what features drive predictions), "
        "model comparison across algorithms, and live inference/prediction. "
        "Invoke when the question involves model performance, feature importance, "
        "predictions, or algorithm comparisons."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        if not context.doc_id:
            return AgentResult.skipped(
                self.name, task,
                "No doc_id provided. ML Agent requires a document with a trained model."
            )

        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []

        # ── Tool 1: ML Session (model metadata + metrics) ────────────
        try:
            from app.services.ml.ml_service import MLService
            session = MLService.get_session_metadata(context.doc_id)
            output["ml_session"] = session
            tool_calls.append("MLService.get_session_metadata")

            if session.get("model_trained"):
                algo = session.get("algorithm", "unknown")
                task_type = session.get("task_type", "?")
                metrics = session.get("metrics", {})
                metric_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
                summaries.append(
                    f"Trained model: {algo} ({task_type}). Metrics: {metric_str}."
                )
            else:
                summaries.append("No trained model found for this document.")
        except Exception as e:
            logger.warning(f"[MLAgent] Session metadata failed: {e}")
            summaries.append(f"Model session unavailable: {e}")

        # ── Tool 2: SHAP Explanation ──────────────────────────────────
        try:
            from app.services.ml.ml_service import MLService
            shap_data = MLService.get_shap_explanation(context.doc_id)
            output["shap"] = shap_data
            tool_calls.append("MLService.get_shap_explanation")

            if shap_data.get("available") and shap_data.get("summary"):
                top_features = [
                    f"{item['feature']} ({item['mean_abs_shap']:.4f})"
                    for item in shap_data["summary"][:3]
                ]
                summaries.append(
                    f"Top SHAP features: {', '.join(top_features)}."
                )
            else:
                summaries.append(
                    "SHAP not available — train model with RandomForest or install shap library."
                )
        except Exception as e:
            logger.warning(f"[MLAgent] SHAP failed: {e}")

        # ── Tool 3: Model Comparison ──────────────────────────────────
        try:
            from app.services.ml.ml_service import MLService
            comparison = MLService.get_model_comparison(context.doc_id)
            output["model_comparison"] = comparison
            tool_calls.append("MLService.get_model_comparison")

            if comparison.get("runs"):
                best = comparison.get("best_algorithm", "?")
                total = comparison.get("total_runs", 0)
                summaries.append(
                    f"Model comparison: {total} algorithm(s) trained. Best: {best}."
                )
        except Exception as e:
            logger.warning(f"[MLAgent] Model comparison failed: {e}")

        if not output:
            return AgentResult.error_result(self.name, task, "All ML tools failed.")

        return AgentResult(
            agent_name=self.name,
            task=task,
            status="success",
            output=output,
            summary=" ".join(summaries) or "ML model analysis complete.",
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
                            "description": "Specific ML task, e.g. 'explain which features drive churn' or 'compare model algorithms'",
                        }
                    },
                    "required": ["task"],
                },
            },
        }
