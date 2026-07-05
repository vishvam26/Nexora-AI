"""
CalendarAgent — Step 16 Meeting Planner & Scheduler

Queries local scheduled calendar events, checks booking conflicts,
inserts new slots, and compiles standard iCalendar (.ics) export files.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult
from app.models.calendar_event import CalendarEvent
from app.db.session import SessionLocal

logger = logging.getLogger("app.services.agents.calendar_agent")

CALENDAR_DIR = os.path.join("storage", "reports")
os.makedirs(CALENDAR_DIR, exist_ok=True)


class CalendarAgent(BaseAgent):
    name = "calendar_agent"
    description = (
        "Schedules meetings and checks calendar slot availability. "
        "Allows creating calendar events in a local database and exporting standard "
        "iCalendar (.ics) files for Outlook/Google Calendar. "
        "Invoke when the CEO's question requests booking a meeting, scheduling a sync, "
        "or planning calendar events."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []

        db = SessionLocal()
        try:
            # Parse parameters from task description string
            import re
            
            # 1. Parse Title
            title = "Business Alignment Sync"
            t_match = re.search(r"title:\s*(.*?)(?:\n|$)", task, re.IGNORECASE)
            if t_match:
                title = t_match.group(1).strip()

            # 2. Parse Start Time
            # Default: tomorrow at 10:00 AM
            start_dt = datetime.now() + timedelta(days=1)
            start_dt = start_dt.replace(hour=10, minute=0, second=0, microsecond=0)
            
            start_match = re.search(r"start:\s*([\d-]+\s+[\d:]+)", task, re.IGNORECASE)
            if start_match:
                try:
                    start_dt = datetime.strptime(start_match.group(1).strip(), "%Y-%m-%d %H:%M")
                except ValueError:
                    pass

            # 3. Parse End Time
            # Default: 30 minutes after start
            end_dt = start_dt + timedelta(minutes=30)
            end_match = re.search(r"end:\s*([\d-]+\s+[\d:]+)", task, re.IGNORECASE)
            if end_match:
                try:
                    end_dt = datetime.strptime(end_match.group(1).strip(), "%Y-%m-%d %H:%M")
                except ValueError:
                    pass

            # 4. Parse Description
            desc = "Meeting scheduled by Nexora AI Planner"
            d_match = re.search(r"description:\s*(.*?)(?:\n|$)", task, re.IGNORECASE)
            if d_match:
                desc = d_match.group(1).strip()

            # 5. Parse Attendees
            attendees = "cfo@company.com"
            a_match = re.search(r"attendees:\s*(.*?)(?:\n|$)", task, re.IGNORECASE)
            if a_match:
                attendees = a_match.group(1).strip()

            # ──────────────────────────────────────────────────────────
            # Availability checking: search for overlaps in local DB
            # ──────────────────────────────────────────────────────────
            conflict = db.query(CalendarEvent).filter(
                CalendarEvent.start_time < end_dt,
                CalendarEvent.end_time > start_dt
            ).first()
            tool_calls.append("db.query.CalendarEvent")

            if conflict:
                return AgentResult.error_result(
                    self.name, task,
                    f"Booking Conflict: Slot is occupied by meeting '{conflict.title}' "
                    f"({conflict.start_time.strftime('%H:%M')} - {conflict.end_time.strftime('%H:%M')})."
                )

            # ──────────────────────────────────────────────────────────
            # Book meeting and compile ICS file
            # ──────────────────────────────────────────────────────────
            event = CalendarEvent(
                title=title,
                description=desc,
                start_time=start_dt,
                end_time=end_dt,
                attendees=attendees
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            tool_calls.append("db.add.CalendarEvent")

            # Generate iCalendar compliant payload
            ics_filename = f"event_{event.id}.ics"
            ics_path = os.path.join(CALENDAR_DIR, ics_filename)
            
            # ICS Date format helper (e.g. 20260706T100000Z)
            def ics_date(dt: datetime) -> str:
                return dt.strftime("%Y%m%dT%H%M%SZ")

            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Nexora AI//Calendar Agent//EN
BEGIN:VEVENT
UID:event_{event.id}@nexora.ai
DTSTAMP:{ics_date(datetime.utcnow())}
DTSTART:{ics_date(start_dt)}
DTEND:{ics_date(end_dt)}
SUMMARY:{title}
DESCRIPTION:{desc}
ATTENDEE;CN=Recipient:mailto:{attendees}
END:VEVENT
END:VCALENDAR"""

            with open(ics_path, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(ics_content)

            output["event_id"] = event.id
            output["title"] = event.title
            output["start_time"] = event.start_time.strftime("%Y-%m-%d %H:%M")
            output["end_time"] = event.end_time.strftime("%Y-%m-%d %H:%M")
            output["ics_path"] = f"/reports/{ics_filename}"
            output["ics_filename"] = ics_filename

            summaries.append(
                f"Successfully booked meeting '{title}' "
                f"({output['start_time']} - {output['end_time']}). "
                f"iCalendar file generated as {ics_filename}."
            )

        except Exception as e:
            logger.error(f"[CalendarAgent] Scheduling failed: {e}")
            db.rollback()
            return AgentResult.error_result(self.name, task, str(e))
        finally:
            db.close()

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
                            "description": "Email booking details containing: 'title: sync', 'start: YYYY-MM-DD HH:MM', 'end: YYYY-MM-DD HH:MM', 'attendees: email@co.com'."
                        }
                    },
                    "required": ["task"]
                }
            }
        }
