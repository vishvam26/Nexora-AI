"""
EmailAgent — Step 15 Email Notification & Report Sender

Composes multipart MIME messages and dispatches them via SMTP connection.
Allows attaching files dynamically (e.g. PDF/Excel reports).
"""
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.config import settings

logger = logging.getLogger("app.services.agents.email_agent")


class EmailAgent(BaseAgent):
    name = "email_agent"
    description = (
        "Composes and sends email notifications. "
        "Allows sending HTML email narratives to clients and attaching documents "
        "(such as exported PDF or Excel reports). "
        "Invoke when the CEO's question explicitly requests emailing a report, "
        "sending an alert, or sharing analytics via email."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []

        # Parse recipient parameters from task or default values
        import re
        to_email = "recipient@example.com"
        to_match = re.search(r"to:\s*([\w\.-]+@[\w\.-]+\.\w+)", task, re.IGNORECASE)
        if to_match:
            to_email = to_match.group(1)
        
        subject = "Nexora AI business notification"
        sub_match = re.search(r"subject:\s*(.*?)(?:\n|$)", task, re.IGNORECASE)
        if sub_match:
            subject = sub_match.group(1).strip()

        # Build email envelope
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject

        # Extract body block if explicitly separated
        body_text = task
        body_match = re.search(r"body:\s*(.*)", task, re.DOTALL | re.IGNORECASE)
        if body_match:
            body_text = body_match.group(1).strip()

        # Determine if body contains HTML tags
        has_html = bool(re.search(r"<\/?[a-z][\s\S]*>", body_text, re.IGNORECASE))
        if has_html:
            body_html = body_text
        else:
            # Replace newlines with HTML breaks and wrap in a clean sans-serif font
            formatted_text = body_text.replace("\n", "<br/>")
            body_html = f'<div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #1f2937;">{formatted_text}</div>'

        # Ingest memory or RAG final answer if present in prior results
        if context.prior_results:
            for agent, result in context.prior_results.items():
                if agent == "report_agent" and "export_path" in result:
                    report_path = result["export_path"]
                    if os.path.exists(report_path):
                        try:
                            with open(report_path, "rb") as f:
                                part = MIMEApplication(f.read(), Name=os.path.basename(report_path))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(report_path)}"'
                            msg.attach(part)
                            summaries.append(f"Attached report file: {os.path.basename(report_path)}.")
                        except Exception as ae:
                            logger.error(f"[EmailAgent] Attachment fail: {ae}")

        # Attach html body
        msg.attach(MIMEText(body_html, "html"))

        # SMTP Connection runner
        try:
            # We wrap connection inside try/except block to allow graceful execution
            # even if mock/no SMTP credentials are set in development environment
            if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                logger.warning("[EmailAgent] SMTP credentials missing — running in mock loop mode.")
                output["mock_mode"] = True
                output["to"] = to_email
                output["subject"] = subject
                output["body"] = body_html
                summaries.append(f"Mock email dispatched successfully to {to_email} (SMTP credentials not configured).")
            else:
                # Dispatch SMTP envelope
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                tool_calls.append("smtplib.SMTP")
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
                server.quit()
                summaries.append(f"Email dispatched successfully to {to_email} via SMTP.")

            output["success"] = True
            output["to"] = to_email

        except Exception as e:
            logger.error(f"[EmailAgent] SMTP connection failed: {e}")
            return AgentResult.error_result(self.name, task, f"SMTP dispatch failed: {str(e)}")

        return AgentResult(
            agent_name=self.name,
            task=task,
            status="success",
            output=output,
            summary=" ".join(summaries),
            tool_calls=tool_calls
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
                            "description": "Email specification details containing 'to: target@email.com', 'subject: title', and 'body: html text' lines."
                        }
                    },
                    "required": ["task"]
                }
            }
        }
