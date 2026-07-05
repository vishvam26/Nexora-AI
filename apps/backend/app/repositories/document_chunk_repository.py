from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document_chunk import DocumentChunk


class DocumentChunkRepository:

    @staticmethod
    def create_batch(db: Session, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        db.add_all(chunks)
        db.commit()
        for c in chunks:
            db.refresh(c)
        return chunks

    @staticmethod
    def get_by_id(db: Session, chunk_id: int) -> Optional[DocumentChunk]:
        return db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()

    @staticmethod
    def list_by_document(db: Session, document_id: int) -> List[DocumentChunk]:
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()

    @staticmethod
    def list_by_document_ids(db: Session, document_ids: List[int]) -> List[DocumentChunk]:
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id.in_(document_ids),
            DocumentChunk.embedding_status == "Completed"
        ).all()

    @staticmethod
    def update_embedding(db: Session, chunk: DocumentChunk, embedding: List[float]) -> DocumentChunk:
        chunk.embedding = embedding
        chunk.embedding_status = "Completed"
        db.commit()
        db.refresh(chunk)
        return chunk

    @staticmethod
    def delete_by_document(db: Session, document_id: int) -> None:
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        db.commit()
