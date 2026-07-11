"""
ReportService — Step 10 AI Report Generator (Orchestrator)

Responsibilities:
  1. Coordinate DataCollectorAgent to gather analytics + ML session + SHAP data
  2. Build a structured LLM prompt via PromptBuilder (context-compressed, injection-safe)
  3. Call LLM Provider to generate the narrative
  4. Delegate file export to ReportAssembler
  5. Persist report metadata for future download/listing

Anti-hallucination: if no analytics or ML data found, narrative section returns:
  "No relevant data found for this report section."

Grounded ON/OFF: when grounded=False, LLM runs without retrieved context
(useful for executive summary reports that rely only on structured stats).
"""
import os
import json
import logging
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger("app.services.report.report_service")

REPORT_DIR = os.path.join("storage", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# Token budget for LLM context (characters — approx 4 chars/token)
MAX_CONTEXT_CHARS = 32_000


class PromptBuilder:
    """
    Builds structured prompts for report generation.
    Keeps ChatService, RetrievalService, and LLM completely decoupled.
    Each report_type gets a dedicated system prompt.
    """

    REPORT_TYPES = {
        "executive_summary": "executive summary for senior leadership",
        "ml_model_card": "ML model card with performance details and feature explanations",
        "statistical_breakdown": "detailed statistical analysis report",
        "full_analytics": "comprehensive analytics report with all sections",
    }

    @classmethod
    def build(
        cls,
        report_type: str,
        collected: Dict[str, Any],
        grounded: bool = True,
        custom_instructions: str = "",
    ) -> Dict[str, str]:
        """
        Returns {"system": ..., "user": ...} ready for any OpenAI-compatible provider.
        """
        report_label = cls.REPORT_TYPES.get(report_type, "general data report")
        doc_id = collected.get("doc_id", "unknown")

        # ── System Prompt ───────────────────────────────────────────────
        system_prompt = (
            f"You are Nexora AI Report Generator — an expert data analyst and business writer.\n"
            f"Generate a professional {report_label}.\n\n"
            "RULES:\n"
            "1. Use only the structured data provided. Never fabricate numbers.\n"
            "2. If a section has no data, write exactly: 'No relevant data found for this section.'\n"
            "3. Format output as structured markdown with clear headings.\n"
            "4. Be concise for executive summaries; be thorough for statistical reports.\n"
            "5. Cite every metric with its exact value from the provided data.\n"
        )
        if grounded:
            system_prompt += "6. Ground every insight in the provided dataset context.\n"

        if custom_instructions:
            system_prompt += f"\nAdditional instructions: {custom_instructions}\n"

        # ── User Prompt ─────────────────────────────────────────────────
        context_sections: List[str] = []

        # Analytics context
        analytics = collected.get("analytics", {})
        if analytics and not analytics.get("error"):
            stats_text = cls._compress_analytics(analytics)
            context_sections.append(f"## Dataset Analytics\n{stats_text}")

        # ML session context
        ml = collected.get("ml_session", {})
        if ml.get("model_trained"):
            ml_text = cls._compress_ml_session(ml)
            context_sections.append(f"## Machine Learning Model\n{ml_text}")

        # SHAP context
        shap = collected.get("shap", {})
        if shap.get("available") and shap.get("summary"):
            shap_lines = "\n".join(
                f"- {item['feature']}: {item['mean_abs_shap']:.4f}"
                for item in shap["summary"][:10]
            )
            context_sections.append(f"## SHAP Feature Attributions (Mean |SHAP|)\n{shap_lines}")

        # Model comparison context
        comparison = collected.get("model_comparison", {})
        if comparison.get("runs"):
            comp_text = cls._compress_comparison(comparison)
            context_sections.append(f"## Model Comparison\n{comp_text}")

        if not context_sections:
            context_sections.append(
                "⚠ No analytics or ML data available for this document. "
                "Please run analytics and/or train a model first."
            )

        full_context = "\n\n".join(context_sections)

        # Context compression — truncate to token budget
        if len(full_context) > MAX_CONTEXT_CHARS:
            full_context = full_context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated for length]"

        user_prompt = (
            f"Document ID: {doc_id}\n"
            f"Report Type: {report_label}\n\n"
            f"=== PROVIDED DATA ===\n{full_context}\n\n"
            f"=== TASK ===\n"
            f"Generate a complete {report_label}. Use the data above. "
            f"Return clean, professional markdown."
        )

        return {"system": system_prompt, "user": user_prompt}

    @classmethod
    def _compress_analytics(cls, analytics: Dict[str, Any]) -> str:
        """Extracts key stats from analytics profile into a compact text block."""
        lines = []
        rows = analytics.get("row_count", "?")
        cols = analytics.get("column_count", "?")
        lines.append(f"Dataset: {rows} rows × {cols} columns")

        col_stats = analytics.get("column_stats", {})
        for col, stats in list(col_stats.items())[:15]:  # cap at 15 columns
            dtype = stats.get("dtype", "?")
            if dtype in ("int64", "float64"):
                mean = stats.get("mean", "?")
                std = stats.get("std", "?")
                lines.append(f"- {col} ({dtype}): mean={mean}, std={std}")
            else:
                top = stats.get("top", "?")
                freq = stats.get("freq", "?")
                lines.append(f"- {col} ({dtype}): top='{top}' ({freq} occurrences)")

        outliers = analytics.get("outliers", {})
        if outliers:
            out_cols = [c for c, v in outliers.items() if v.get("count", 0) > 0]
            if out_cols:
                lines.append(f"Outlier columns: {', '.join(out_cols)}")

        missing = analytics.get("missing_values", {})
        if missing:
            miss_cols = [(c, v) for c, v in missing.items() if v > 0]
            if miss_cols:
                miss_str = ", ".join(f"{c}={v}" for c, v in miss_cols[:5])
                lines.append(f"Missing values: {miss_str}")

        return "\n".join(lines)

    @classmethod
    def _compress_ml_session(cls, ml: Dict[str, Any]) -> str:
        """Extracts key ML session info into compact text."""
        lines = [
            f"Task Type: {ml.get('task_type', '?')}",
            f"Algorithm: {ml.get('algorithm', '?')}",
            f"Target Column: {ml.get('target_column', '?')}",
        ]
        metrics = ml.get("metrics", {})
        if metrics:
            metric_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
            lines.append(f"Metrics: {metric_str}")

        fi = ml.get("feature_importance", [])[:5]
        if fi:
            fi_str = ", ".join(f"{f['feature']}={f['importance']}" for f in fi)
            lines.append(f"Top Features: {fi_str}")

        return "\n".join(lines)

    @classmethod
    def _compress_comparison(cls, comparison: Dict[str, Any]) -> str:
        """Formats model comparison runs into a markdown table."""
        runs = comparison.get("runs", [])
        best = comparison.get("best_algorithm", "?")
        lines = [f"Best Algorithm: **{best}**\n"]
        lines.append("| Algorithm | Primary Metric | Value |")
        lines.append("|-----------|----------------|-------|")
        for run in runs[:5]:
            lines.append(
                f"| {run.get('algorithm','?')} "
                f"| {run.get('primary_metric','?')} "
                f"| {run.get('primary_value','?')} |"
            )
        return "\n".join(lines)


class ReportService:
    """
    Step 10 Report Generation Orchestrator.

    Flow: collect → prompt → LLM → assemble → persist
    """

    @classmethod
    def generate(
        cls,
        doc_id: int,
        file_path: str,
        report_type: str,
        export_format: str,
        grounded: bool = True,
        custom_instructions: str = "",
        include_analytics: bool = True,
        include_ml: bool = True,
        include_shap: bool = True,
    ) -> Dict[str, Any]:
        """
        Full report generation pipeline.

        Args:
            doc_id: Knowledge document ID
            file_path: Path to the original dataset file
            report_type: One of executive_summary | ml_model_card | statistical_breakdown | full_analytics
            export_format: One of pdf | excel | pptx | png | markdown
            grounded: If True, system prompt instructs LLM to cite all data
            custom_instructions: Optional user override instructions
            include_analytics: Collect analytics profile
            include_ml: Collect ML session + comparison
            include_shap: Collect SHAP explanation

        Returns:
            {
                "report_id": str,
                "narrative": str,       # LLM-generated markdown
                "export_path": str,     # Absolute path to exported file
                "export_format": str,
                "shap_available": bool,
                "model_trained": bool,
                "generated_at": str,
            }
        """
        t0 = time.time()
        report_id = f"report_{doc_id}_{int(t0)}"
        logger.info(f"[ReportService] Starting generation: {report_id} | type={report_type} | format={export_format}")

        # ── 1. Data Collection ────────────────────────────────────────
        from app.services.report.data_collector import DataCollectorAgent
        collected = DataCollectorAgent.collect_all(
            doc_id=doc_id,
            file_path=file_path,
            include_analytics=include_analytics,
            include_ml=include_ml,
            include_shap=include_shap,
        )

        # ── 2. Prompt Construction ────────────────────────────────────
        prompt = PromptBuilder.build(
            report_type=report_type,
            collected=collected,
            grounded=grounded,
            custom_instructions=custom_instructions,
        )

        # ── 3. LLM Call ───────────────────────────────────────────────
        narrative = cls._call_llm(prompt["system"], prompt["user"])

        # ── 4. Export Assembly ────────────────────────────────────────
        from app.services.report.report_assembler import ReportAssembler
        export_path = ReportAssembler.export(
            report_id=report_id,
            narrative=narrative,
            report_type=report_type,
            export_format=export_format,
            collected=collected,
        )

        latency = round(time.time() - t0, 2)
        logger.info(f"[ReportService] Done in {latency}s → {export_path}")

        # ── 5. Persist Metadata ───────────────────────────────────────
        meta = {
            "report_id": report_id,
            "doc_id": doc_id,
            "report_type": report_type,
            "export_format": export_format,
            "export_path": export_path,
            "narrative": narrative,
            "shap_available": collected.get("shap", {}).get("available", False),
            "model_trained": collected.get("ml_session", {}).get("model_trained", False),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "latency_seconds": latency,
        }
        cls._persist_meta(doc_id, report_id, meta)

        return meta

    @classmethod
    def _call_llm(cls, system_prompt: str, user_prompt: str) -> str:
        """
        LLM call wrapper — uses OpenAI provider (same pattern as ChatService).
        Falls back to local fine-tuned Qwen model (NexoraProvider) if active,
        and falls back to structured summary if both are unavailable.
        """
        from app.config import settings
        if settings.AI_PROVIDER.lower().strip() == "nexora":
            try:
                logger.info("[ReportService] Routing report generation to local fine-tuned model via NexoraProvider...")
                from app.providers.nexora_provider import NexoraProvider
                provider = NexoraProvider()
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                response = provider.generate_response(messages)
                if response:
                    return cls.clean_model_output(response)
            except Exception as nexora_err:
                logger.warning(f"[ReportService] Local Nexora model call failed: {nexora_err}")

        try:
            import openai
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=4096,
                temperature=0.3,
            )
            return cls.clean_model_output(response.choices[0].message.content or "No narrative generated.")
        except Exception as e:
            logger.warning(f"[ReportService] LLM call failed, using fallback: {e}")
            return (
                "# Auto Generated Report\n\n"
                "> ⚠ LLM narrative unavailable (API key not set or provider error).\n\n"
                "The structured data below was collected successfully and exported.\n"
                "Configure `OPENAI_API_KEY` to enable AI-generated narrative sections."
            )

    @classmethod
    def _persist_meta(cls, doc_id: int, report_id: str, meta: Dict[str, Any]) -> None:
        """Saves report metadata to per-document JSON registry."""
        registry_path = os.path.join(REPORT_DIR, f"registry_{doc_id}.json")
        reports: List[Dict[str, Any]] = []
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    reports = json.load(f)
            except Exception:
                reports = []

        # Store without narrative for list view (keeps file small)
        summary = {k: v for k, v in meta.items() if k != "narrative"}
        reports.insert(0, summary)
        reports = reports[:50]  # keep last 50 reports

        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2)

    @classmethod
    def list_reports(cls, doc_id: int) -> List[Dict[str, Any]]:
        """Returns list of generated reports for a document (newest first)."""
        registry_path = os.path.join(REPORT_DIR, f"registry_{doc_id}.json")
        if not os.path.exists(registry_path):
            return []
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def clean_model_output(cls, text: str) -> str:
        """
        Cleans raw LLM outputs to remove thinking processes, chain-of-thought blocks,
        and markdown wrapper blocks.
        """
        if not text:
            return ""
        import re
        # Strip xml thought tags if present
        text = re.sub(r'<thought>.*?</thought>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Strip "Thinking Process:" section
        text = re.sub(r'^(?:Thinking Process|Thinking|Thought):\s*.*?\n\n', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Strip general "Thinking Process:" headings
        text = re.sub(r'^(?:Thinking Process|Thinking|Thought):\s*.*?$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        # Strip triple backticks enclosing markdown syntax if the model wrapped the entire output
        text = text.strip()
        if text.startswith("```markdown") and text.endswith("```"):
            text = text[11:-3].strip()
        elif text.startswith("```") and text.endswith("```"):
            text = text[3:-3].strip()
        return text
