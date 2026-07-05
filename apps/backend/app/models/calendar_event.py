"""
CalendarEvent DB Model — Step 16 Calendar Agent
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.db.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    attendees = Column(Text, nullable=True) # Comma-separated emails
    created_at = Column(DateTime, default=datetime.utcnow)
