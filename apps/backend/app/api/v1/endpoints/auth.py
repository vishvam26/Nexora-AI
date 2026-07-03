from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


from app.schemas.user import (
    UserCreate,
    UserLogin,
    Token,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
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
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):

    return AuthService.login(
        db,
        user.email,
        user.password,
    )