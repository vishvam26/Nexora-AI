from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    @staticmethod
    def get_by_email(db: Session, email: str):

        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, user: User):

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update(db: Session, user: User, **kwargs):
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user: User, new_password_hash: str):
        user.password_hash = new_password_hash
        db.commit()
        db.refresh(user)
        return user