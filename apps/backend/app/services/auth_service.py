from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.hashing import hash_password, verify_password
from app.security.jwt import create_access_token
from app.config import settings


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

    @staticmethod
    def login(db: Session, email: str, password: str):
        admin_email = getattr(settings, "ADMIN_EMAIL", "p.vishu2685@gmail.com").strip().lower()
        admin_pass = getattr(settings, "ADMIN_PASSWORD", "p.vishvam@2685")
        input_email = email.strip().lower()

        # Handle Master Admin login auto-creation / verification
        if input_email == admin_email:
            user = UserRepository.get_by_email(db, input_email)
            if not user:
                # Auto-create Master Admin user
                user = User(
                    full_name="Vishvam Prajapati (Master Admin)",
                    email=admin_email,
                    password_hash=hash_password(admin_pass)
                )
                user = UserRepository.create(db, user)

            # Check if password matches master password or user password
            if password == admin_pass or verify_password(password, user.password_hash):
                token = create_access_token({"sub": str(user.id), "email": user.email})
                return {"access_token": token, "token_type": "bearer"}
            else:
                raise HTTPException(status_code=401, detail="Invalid Master Admin credentials")

        user = UserRepository.get_by_email(db, input_email)

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not verify_password(
            password,
            user.password_hash
        ):

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer"
        }