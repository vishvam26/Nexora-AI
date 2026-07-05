"""
Pydantic Schemas for Email Execution API — Step 15
"""
from pydantic import BaseModel, Field
from typing import Optional


class EmailSendRequest(BaseModel):
    to_email: str = Field(
        ...,
        description="The recipient email address",
    )
    subject: str = Field(
        ...,
        description="The subject line of the email",
        min_length=3,
        max_length=200,
    )
    body: str = Field(
        ...,
        description="The HTML/text body message contents",
        min_length=5,
        max_length=5000,
    )
    report_id: Optional[str] = Field(
        default=None,
        description="Optional report ID to attach (PDF/Excel files)",
    )
