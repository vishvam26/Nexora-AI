from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
)
from app.services.auth_service import AuthService
from app.security.limiter import limiter


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
@limiter.limit("5/minute")
def register(
    request: Request,
    user: UserCreate,
    db: Session = Depends(get_db)
):

    AuthService.register(
        db=db,
        full_name=user.full_name,
        email=user.email,
        password=user.password
    )

    return {
        "message": "User created successfully"
    }

@router.post(
    "/login",
    response_model=Token
)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    return AuthService.login(
        db,
        form_data.username,
        form_data.password,
    )