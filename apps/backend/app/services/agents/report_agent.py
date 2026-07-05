"""
ReportAgent — Step 11 Multi-Agent Orchestration

Specialized agent that wraps ReportService.
The Manager invokes this when:
  - CEO explicitly asks for a report/document
  - The question's scope requires a persistent, exportable artifact
  - generate_report=True is set in AgentContext

After running AnalyticsAgent and MLAgent, the ReportAgent can consume their
outputs (via context.prior_results) to avoid duplicate data collection.
"""
import logging
from typing import Dict, Any

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger("app.services.agents.report_agent")


class ReportAgent(BaseAgent):
    name = "report_agent"
    description = (
        "Generates a professional AI-narrated report for a dataset. "
        "Produces exportable files: PDF, Excel, PowerPoint, PNG, or Markdown. "
        "Combines analytics statistics, ML model performance, and SHAP explanations "
        "into a boardroom-ready document. "
        "Invoke when the CEO explicitly asks for a report, document, or presentation, "
        "or when the question requires a comprehensive written output."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        if not context.doc_id or not context.file_path:
            return AgentResult.skipped(
                self.name, task,
                "No doc_id or file_path provided. Report Agent requires a document."
            )

        tool_calls = []
        output: Dict[str, Any] = {}

        try:
            from app.services.report.report_service import ReportService

            # Map context fields to report parameters
            report_type = context.report_type or "full_analytics"
            export_format = context.report_format or "pdf"

            # ReportService.generate() internally calls DataCollectorAgent —
            # it will re-collect analytics and ML data. This is acceptable
            # because the cache-first approach in AnalyticsEngine and MLService
            # means the second call is cheap (reads from disk cache).
            result = ReportService.generate(
                doc_id=context.doc_id,
                file_path=context.file_path,
                report_type=report_type,
                export_format=export_format,
                grounded=True,
                custom_instructions=f"This report was generated in response to: {context.question}",
                include_analytics=True,
                include_ml=True,
                include_shap=True,
            )
            tool_calls.append("ReportService.generate")

            output["report_id"] = result.get("report_id")
            output["export_format"] = result.get("export_format")
            output["export_path"] = result.get("export_path")
            output["shap_available"] = result.get("shap_available", False)
            output["model_trained"] = result.get("model_trained", False)
            output["narrative_preview"] = result.get("narrative", "")[:500]

            summary = (
                f"Report generated successfully. "
                f"Format: {export_format.upper()}. "
                f"Report ID: {result.get('report_id', '?')}. "
                f"Download via /reports/download/{result.get('report_id', '')}."
            )
            if result.get("shap_available"):
                summary += " SHAP explainability included."

            return AgentResult(
                agent_name=self.name,
                task=task,
                status="success",
                output=output,
                summary=summary,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(f"[ReportAgent] Report generation failed: {e}", exc_info=True)
            return AgentResult.error_result(self.name, task, str(e))

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
                            "description": "Report generation task, e.g. 'generate an executive summary PDF' or 'create an ML model card report'",
                        }
                    },
                    "required": ["task"],
                },
            },
        }
