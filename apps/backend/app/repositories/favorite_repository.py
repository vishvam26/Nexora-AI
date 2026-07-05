from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.favorite import Favorite


class FavoriteRepository:
    """
    Repository for handling database actions for Favorites.
    """

    @staticmethod
    def create(db: Session, favorite: Favorite) -> Favorite:
        """
        Saves a new favorite.
        """
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
        return favorite

    @staticmethod
    def get_by_user_and_conversation(db: Session, user_id: int, conversation_id: int) -> Optional[Favorite]:
        """
        Retrieves user's favorite record for a specific conversation.
        """
        return db.query(Favorite).filter(
            Favorite.user_id == user_id,
            Favorite.conversation_id == conversation_id
        ).first()

    @staticmethod
    def get_all_by_user(db: Session, user_id: int) -> List[Favorite]:
        """
        Retrieves all favorite records belonging to a user.
        """
        return db.query(Favorite).filter(Favorite.user_id == user_id).order_by(Favorite.created_at.desc()).all()

    @staticmethod
    def delete(db: Session, favorite: Favorite) -> None:
        """
        Removes favorite record from database.
        """
        db.delete(favorite)
        db.commit()
