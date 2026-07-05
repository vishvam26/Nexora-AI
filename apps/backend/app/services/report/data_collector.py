"""
DataCollectorAgent — Step 10 AI Report Generator

Aggregates data from all platform modules before handing off to LLM:
  - Analytics Engine (statistical profile, EDA, outliers, correlations)
  - ML Studio (session metadata, SHAP explanation, model comparison)
  - RAG Retrieval (top knowledge-base context for narrative grounding)

Designed as a pure data-fetch layer. No LLM calls happen here.
ReportService owns orchestration; DataCollectorAgent is a read-only helper.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("app.services.report.data_collector")


class DataCollectorAgent:
    """
    Gathers structured data from analytics, ML, and RAG modules.
    Each method is independently callable so future AI Agents can
    compose their own collection pipelines without touching ReportService.
    """

    @classmethod
    def collect_analytics(cls, doc_id: int, file_path: str) -> Dict[str, Any]:
        """
        Pulls the full analytics profile for a document.
        Returns stats, EDA, outliers, correlations, and missing-value report.
        Gracefully returns empty dict on import failure.
        """
        try:
            from app.services.analytics.analytics_engine import AnalyticsEngine
            profile = AnalyticsEngine.get_profile(doc_id, file_path)
            if "error" in profile:
                logger.warning(f"Analytics profile error for doc {doc_id}: {profile['error']}")
                return {}
            return profile
        except Exception as e:
            logger.warning(f"DataCollectorAgent.collect_analytics failed: {e}")
            return {}

    @classmethod
    def collect_ml_session(cls, doc_id: int) -> Dict[str, Any]:
        """
        Pulls the full ML session metadata including:
        - Active model (algorithm, task_type, metrics, feature_columns)
        - SHAP explanation summary
        - Model comparison across all trained algorithms
        """
        try:
            from app.services.ml.ml_service import MLService
            return MLService.get_session_metadata(doc_id)
        except Exception as e:
            logger.warning(f"DataCollectorAgent.collect_ml_session failed: {e}")
            return {"model_trained": False}

    @classmethod
    def collect_shap(cls, doc_id: int) -> Dict[str, Any]:
        """
        Pulls cached SHAP feature attribution data.
        Returns {"available": False} if shap not installed or model not trained.
        """
        try:
            from app.services.ml.ml_service import MLService
            return MLService.get_shap_explanation(doc_id)
        except Exception as e:
            logger.warning(f"DataCollectorAgent.collect_shap failed: {e}")
            return {"available": False, "reason": str(e)}

    @classmethod
    def collect_model_comparison(cls, doc_id: int) -> Dict[str, Any]:
        """
        Retrieves ranked algorithm comparison from the Model Registry.
        """
        try:
            from app.services.ml.ml_service import MLService
            return MLService.get_model_comparison(doc_id)
        except Exception as e:
            logger.warning(f"DataCollectorAgent.collect_model_comparison failed: {e}")
            return {"runs": [], "best_algorithm": None}

    @classmethod
    def collect_all(
        cls,
        doc_id: int,
        file_path: str,
        include_analytics: bool = True,
        include_ml: bool = True,
        include_shap: bool = True,
    ) -> Dict[str, Any]:
        """
        Master collection method — aggregates all available data sources.
        ReportService calls this single method to prepare the report payload.

        Returns a structured dict:
        {
            "doc_id": int,
            "analytics": {...},          # from AnalyticsEngine
            "ml_session": {...},         # from MLService.get_session_metadata()
            "shap": {...},               # from MLService.get_shap_explanation()
            "model_comparison": {...},   # from MLService.get_model_comparison()
        }
        """
        collected: Dict[str, Any] = {"doc_id": doc_id}

        if include_analytics:
            logger.info(f"[DataCollectorAgent] Fetching analytics for doc {doc_id}")
            collected["analytics"] = cls.collect_analytics(doc_id, file_path)

        if include_ml:
            logger.info(f"[DataCollectorAgent] Fetching ML session for doc {doc_id}")
            collected["ml_session"] = cls.collect_ml_session(doc_id)
            collected["model_comparison"] = cls.collect_model_comparison(doc_id)

        if include_shap:
            logger.info(f"[DataCollectorAgent] Fetching SHAP data for doc {doc_id}")
            collected["shap"] = cls.collect_shap(doc_id)

        return collected
