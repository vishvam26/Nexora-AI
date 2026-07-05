"""
Calendar Sandbox endpoints — Step 16 Calendar Agent

Exposes routes to:
  - Fetch all registered calendar events from local DB
  - Book a slot securely validating scheduling overlaps
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.models.calendar_event import CalendarEvent
from app.services.agents.calendar_agent import CalendarAgent
from app.services.agents.base_agent import AgentContext
from app.schemas.calendar_agent import MeetingScheduleRequest, CalendarEventResponse

router = APIRouter(
    prefix="/calendar",
    tags=["Calendar Sandbox"],
)


@router.get(
    "/events",
    response_model=List[CalendarEventResponse],
    summary="Get all scheduled calendar events from the local database",
)
def get_calendar_events(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns lists of all locally booked appointments sorted by start time.
    """
    events = db.query(CalendarEvent).order_by(CalendarEvent.start_time.asc()).all()
    res = []
    for ev in events:
        res.append(CalendarEventResponse(
            id=ev.id,
            title=ev.title,
            description=ev.description,
            start_time=ev.start_time.strftime("%Y-%m-%d %H:%M"),
            end_time=ev.end_time.strftime("%Y-%m-%d %H:%M"),
            attendees=ev.attendees
        ))
    return res


@router.post(
    "/schedule",
    response_model=Dict[str, Any],
    summary="Schedule a meeting slot dynamically checking overlaps",
)
def schedule_calendar_event(
    payload: MeetingScheduleRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Validates slot overlaps and books the appointment in the local database.
    Generates and returns the static relative path to the iCalendar ICS file.
    """
    agent = CalendarAgent()
    context = AgentContext(
        question="Manual Meeting Schedule Request"
    )

    # Format CalendarAgent task booking syntax
    task = f"title: {payload.title}\nstart: {payload.start_time}\nend: {payload.end_time}\ndescription: {payload.description or ''}\nattendees: {payload.attendees}"
    res = agent.run(task, context)

    if res.status == "error":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=res.error or "Scheduling failed."
        )
    return res.output
