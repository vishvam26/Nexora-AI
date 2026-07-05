"""
Pydantic Schemas for Calendar Booking API — Step 16
"""
from pydantic import BaseModel, Field
from typing import Optional


class MeetingScheduleRequest(BaseModel):
    title: str = Field(
        ...,
        description="The subject title of the meeting",
        min_length=3,
        max_length=200,
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional detailed descriptions/notes",
    )
    start_time: str = Field(
        ...,
        description="The start time of the meeting in format YYYY-MM-DD HH:MM",
    )
    end_time: str = Field(
        ...,
        description="The end time of the meeting in format YYYY-MM-DD HH:MM",
    )
    attendees: str = Field(
        ...,
        description="Comma-separated email lists",
    )
class CalendarEventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: str
    end_time: str
    attendees: Optional[str]
