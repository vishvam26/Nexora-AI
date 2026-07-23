from pydantic import BaseModel
from datetime import datetime


class DocumentCommentBase(BaseModel):
    content: str


class DocumentCommentCreate(DocumentCommentBase):
    pass


class DocumentCommentResponse(DocumentCommentBase):
    id: int
    document_id: int
    user_id: int
    created_at: datetime
    user_name: str

    class Config:
        from_attributes = True
