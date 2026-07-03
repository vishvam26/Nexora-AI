from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.hashing import hash_password


class AuthService:

    @staticmethod
    def register(db: Session, full_name: str, email: str, password: str):

        existing_user = UserRepository.get_by_email(db, email)

        if existing_user:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password)
        )

        return UserRepository.create(db, user)