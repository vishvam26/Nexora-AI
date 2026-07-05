from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserProfileResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from app.security.dependencies import get_current_user
from app.db.session import get_db
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get(
    "/me",
    response_model=UserResponse
)
def read_current_user(
    current_user: User = Depends(get_current_user),
):

    return current_user


@router.get(
    "/profile",
    response_model=UserProfileResponse
)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return UserService.get_profile(current_user)


@router.put(
    "/profile",
    response_model=UserProfileResponse
)
def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return UserService.update_profile(db, current_user, request.full_name)


@router.put(
    "/change-password"
)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    UserService.change_password(
        db,
        current_user,
        request.current_password,
        request.new_password
    )
    return {"message": "Password changed successfully"}