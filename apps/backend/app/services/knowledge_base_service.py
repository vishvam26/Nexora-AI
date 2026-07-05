import logging
import uuid
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.models.knowledge_document import KnowledgeDocument
from app.models.document_chunk import DocumentChunk
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.document_processing.document_processor import DocumentProcessor
from app.services.document_processing.chunking_engine import ChunkingEngine
from app.services.embedding.embedding_service import EmbeddingService
from app.services.vector_store.qdrant_vector_store import QdrantVectorStore
from app.services.storage.local_storage import LocalStorage

logger = logging.getLogger("app.services.knowledge_base_service")

# Singleton instances (swappable via DI in future)
_storage = LocalStorage(base_upload_dir="uploads/knowledge")
_processor = DocumentProcessor()
_chunker = ChunkingEngine()
_embedder = EmbeddingService()
_vector_store = QdrantVectorStore()


class KnowledgeBaseService:
    """
    Core service for Knowledge Base CRUD and Document processing pipeline.
    """

    # ---- Knowledge Base CRUD ----

    @staticmethod
    def create_knowledge_base(db: Session, user_id: int, workspace_id: int, data: dict) -> KnowledgeBase:
        return KnowledgeBaseRepository.create(
            db=db,
            workspace_id=workspace_id,
            created_by=user_id,
            uuid=str(uuid.uuid4()),
            **data
        )

    @staticmethod
    def get_knowledge_base(db: Session, kb_id: int, user_id: int) -> KnowledgeBase:
        kb = KnowledgeBaseRepository.get_by_id(db, kb_id)
        if not kb:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")
        return kb

    @staticmethod
    def list_knowledge_bases(db: Session, workspace_id: int) -> List[KnowledgeBase]:
        return KnowledgeBaseRepository.list_by_workspace(db, workspace_id)

    @staticmethod
    def update_knowledge_base(db: Session, kb_id: int, user_id: int, data: dict) -> KnowledgeBase:
        kb = KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        return KnowledgeBaseRepository.update(db, kb, **{k: v for k, v in data.items() if v is not None})

    @staticmethod
    def delete_knowledge_base(db: Session, kb_id: int, user_id: int) -> None:
        kb = KnowledgeBaseService.get_knowledge_base(db, kb_id, user_id)
        KnowledgeBaseRepository.soft_delete(db, kb)

    # ---- Document Upload & Processing ----

    @staticmethod
    def upload_document(
        db: Session,
        kb_id: int,
        user_id: int,
        file_content: bytes,
        filename: str,
        mime_type: str,
    ) -> KnowledgeDocument:
        """
        Persists the uploaded file, triggers text extraction, chunking, and embedding.
        """
        # Verify KB exists
        kb = KnowledgeBaseRepository.get_by_id(db, kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found.")

        # Save file to storage
        safe_filename = f"{uuid.uuid4().hex}_{filename}"
        storage_path = _storage.save_file(file_content, safe_filename, subfolder=str(kb_id))
        checksum = _processor.compute_checksum(file_content)

        # Create document record
        doc = KnowledgeDocumentRepository.create(
            db=db,
            knowledge_base_id=kb_id,
            uploaded_by=user_id,
            filename=filename,
            mime_type=mime_type,
            size=len(file_content),
            status="Processing",
            storage_path=storage_path,
            checksum=checksum,
        )

        try:
            # Extract text
            raw_text = _processor.extract_text(file_content, mime_type, filename)
            language = _processor.detect_language(raw_text)
            pages = _processor.count_pages(raw_text)

            # Chunk text
            chunk_dicts = _chunker.chunk(raw_text, mime_type=mime_type)

            # Build chunk models
            chunk_models = [
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=c["chunk_index"],
                    text=c["text"],
                    token_count=c["token_count"],
                    page=c.get("page"),
                    section=c.get("section"),
                    chunk_metadata=c.get("metadata"),
                    embedding_status="Pending",
                )
                for c in chunk_dicts
            ]
            saved_chunks = DocumentChunkRepository.create_batch(db, chunk_models)

            # Generate and store embeddings
            texts = [c.text for c in saved_chunks]
            embeddings = _embedder.embed_batch(texts)

            for chunk, emb in zip(saved_chunks, embeddings):
                DocumentChunkRepository.update_embedding(db, chunk, emb)
                _vector_store.add(
                    chunk_id=chunk.id,
                    embedding=emb,
                    metadata={
                        "workspace_id": kb.workspace_id,
                        "knowledge_base_id": kb_id,
                        "document_id": doc.id,
                        "page_number": chunk.page or 1,
                        "section_title": chunk.section or "",
                        "token_count": chunk.token_count,
                        "file_name": doc.filename,
                        "mime_type": doc.mime_type,
                        "created_at": doc.created_at.isoformat(),
                    }
                )

            # Mark document as completed
            KnowledgeDocumentRepository.update(
                db, doc,
                status="Completed",
                language=language,
                pages=pages,
            )

            # Extract entities and build Graph connections automatically (Module 5)
            try:
                from app.services.knowledge_graph_service import KnowledgeGraphService
                KnowledgeGraphService.extract_entities_from_text(
                    db=db,
                    workspace_id=kb.workspace_id,
                    document_id=doc.id,
                    text=raw_text,
                )
            except Exception as graph_err:
                logger.error(f"Failed to build graph nodes for doc_id={doc.id}: {graph_err}")

        except Exception as e:
            logger.error(f"Document processing failed for doc_id={doc.id}: {e}")
            KnowledgeDocumentRepository.update_status(db, doc, "Failed")
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

        db.refresh(doc)
        return doc

    @staticmethod
    def reprocess_document(db: Session, doc_id: int, user_id: int) -> KnowledgeDocument:
        """Re-runs the processing pipeline for an existing document."""
        doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")

        # Load file bytes from storage
        file_content = _storage.read_file(doc.storage_path)

        # Delete old chunks from Qdrant and SQL DB
        if hasattr(_vector_store, "delete_by_document"):
            _vector_store.delete_by_document(doc_id)
        DocumentChunkRepository.delete_by_document(db, doc_id)

        # Re-run pipeline (reuse upload logic)
        return KnowledgeBaseService.upload_document(
            db=db,
            kb_id=doc.knowledge_base_id,
            user_id=user_id,
            file_content=file_content,
            filename=doc.filename,
            mime_type=doc.mime_type,
        )

    @staticmethod
    def delete_document(db: Session, doc_id: int, user_id: int) -> None:
        doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        if hasattr(_vector_store, "delete_by_document"):
            _vector_store.delete_by_document(doc_id)
        DocumentChunkRepository.delete_by_document(db, doc_id)
        try:
            _storage.delete_file(doc.storage_path)
        except FileNotFoundError:
            logger.warning(f"Storage file not found during delete: {doc.storage_path}")
        KnowledgeDocumentRepository.soft_delete(db, doc)

    @staticmethod
    def list_documents(db: Session, kb_id: int) -> List[KnowledgeDocument]:
        return KnowledgeDocumentRepository.list_by_knowledge_base(db, kb_id)

    @staticmethod
    def get_document(db: Session, doc_id: int) -> KnowledgeDocument:
        doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        return doc

    @staticmethod
    def get_document_stats(db: Session, doc_id: int) -> Dict[str, Any]:
        doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        chunks = DocumentChunkRepository.list_by_document(db, doc_id)
        total_words = sum(len(c.text.split()) for c in chunks)
        total_chars = sum(len(c.text) for c in chunks)
        completed = sum(1 for c in chunks if c.embedding_status == "Completed")
        return {
            "document_id": doc_id,
            "filename": doc.filename,
            "status": doc.status,
            "pages": doc.pages or 0,
            "total_chunks": len(chunks),
            "embedded_chunks": completed,
            "total_words": total_words,
            "total_characters": total_chars,
            "language": doc.language or "unknown",
        }
