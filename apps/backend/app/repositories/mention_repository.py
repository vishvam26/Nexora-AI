from sqlalchemy.orm import Session
from typing import List
from app.models.mention import Mention


class MentionRepository:
    """
    Repository for handling database actions for Mentions.
    """

    @staticmethod
    def create(db: Session, mention: Mention) -> Mention:
        """
        Saves a new mention.
        """
        db.add(mention)
        db.commit()
        db.refresh(mention)
        return mention

    @staticmethod
    def get_by_comment(db: Session, comment_id: int) -> List[Mention]:
        """
        Retrieves all mentions linked to a comment.
        """
        return db.query(Mention).filter(Mention.comment_id == comment_id).all()
