from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.security.limiter import limiter

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
@limiter.limit("30/minute")
def chat(
    request_obj: Request,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a prompt to the AI, persist user and assistant messages, and return the completion.
    """
    return ChatService.handle_chat(db, current_user.id, request)


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK
)
@limiter.limit("30/minute")
def chat_stream(
    request_obj: Request,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a prompt to the AI, persist user message immediately, stream the AI response
    token-by-token, and save the full assistant response to the database once completed.
    """
    generator = ChatService.handle_chat_stream(db, current_user.id, request)
    return StreamingResponse(generator, media_type="text/event-stream")


