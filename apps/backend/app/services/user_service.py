from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.hashing import hash_password, verify_password

class UserService:
    @staticmethod
    def get_profile(user: User):
        return user

    @staticmethod
    def update_profile(db: Session, user: User, full_name: str):
        return UserRepository.update(db, user, full_name=full_name)

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str):
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        new_password_hash = hash_password(new_password)
        return UserRepository.change_password(db, user, new_password_hash)
