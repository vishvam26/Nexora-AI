import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
)
from app.schemas.knowledge_document import (
    KnowledgeDocumentResponse,
    KnowledgeDocumentListResponse,
    DocumentStatsResponse,
    RetrievalRequest,
    RetrievalResponse,
    ChunkResponse,
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.retrieval_service import RetrievalService

logger = logging.getLogger("app.api.knowledge")

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base & RAG"])


# ──────────────────────────────────────────────────────────────
# Knowledge Base CRUD
# ──────────────────────────────────────────────────────────────

@router.post(
    "/bases",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Knowledge Base"
)
def create_knowledge_base(
    workspace_id: int = Query(..., description="Workspace this Knowledge Base belongs to"),
    schema: KnowledgeBaseCreate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new Knowledge Base inside a workspace."""
    return KnowledgeBaseService.create_knowledge_base(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        data=schema.model_dump(),
    )


@router.get(
    "/bases",
    response_model=KnowledgeBaseListResponse,
    summary="List all Knowledge Bases in a workspace"
)
def list_knowledge_bases(
    workspace_id: int = Query(..., description="Workspace ID to filter by"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all active knowledge bases belonging to the workspace."""
    kbs = KnowledgeBaseService.list_knowledge_bases(db, workspace_id)
    return KnowledgeBaseListResponse(knowledge_bases=kbs, total=len(kbs))


@router.get(
    "/bases/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="Get Knowledge Base details"
)
def get_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return KnowledgeBaseService.get_knowledge_base(db, kb_id, current_user.id)


@router.patch(
    "/bases/{kb_id}",
    response_model=KnowledgeBaseResponse,
    summary="Update a Knowledge Base"
)
def update_knowledge_base(
    kb_id: int,
    schema: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return KnowledgeBaseService.update_knowledge_base(
        db=db,
        kb_id=kb_id,
        user_id=current_user.id,
        data=schema.model_dump(),
    )


@router.delete(
    "/bases/{kb_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a Knowledge Base"
)
def delete_knowledge_base(
    kb_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    KnowledgeBaseService.delete_knowledge_base(db, kb_id, current_user.id)
    return None


# ──────────────────────────────────────────────────────────────
# Document Management
# ──────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a document into a Knowledge Base"
)
async def upload_document(
    kb_id: int = Form(..., description="Knowledge Base ID to attach document to"),
    file: UploadFile = File(..., description="Document file to upload"),
    visibility: str = Form("WORKSPACE", description="Visibility of the document (WORKSPACE, PRIVATE, COMPANY)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts a file upload, stores it locally, extracts text, chunks it,
    generates embeddings and indexes vectors. Supports: TXT, MD, HTML, CSV, JSON, code files.
    PDF/DOCX require optional libraries (placeholder response returned if missing).
    """
    file_content = await file.read()
    mime_type = file.content_type or "text/plain"

    return KnowledgeBaseService.upload_document(
        db=db,
        kb_id=kb_id,
        user_id=current_user.id,
        file_content=file_content,
        filename=file.filename or "upload",
        mime_type=mime_type,
        visibility=visibility,
    )


@router.get(
    "/documents",
    response_model=KnowledgeDocumentListResponse,
    summary="List documents in a Knowledge Base"
)
def list_documents(
    kb_id: int = Query(..., description="Knowledge Base ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    docs = KnowledgeBaseService.list_documents(db, kb_id, current_user.id)
    return KnowledgeDocumentListResponse(documents=docs, total=len(docs))


@router.get(
    "/documents/{doc_id}",
    response_model=KnowledgeDocumentResponse,
    summary="Get a single document"
)
def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return KnowledgeBaseService.get_document(db, doc_id, current_user.id)


@router.get(
    "/documents/{doc_id}/stats",
    response_model=DocumentStatsResponse,
    summary="Get document processing statistics"
)
def get_document_stats(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return KnowledgeBaseService.get_document_stats(db, doc_id, current_user.id)


@router.post(
    "/documents/{doc_id}/reprocess",
    response_model=KnowledgeDocumentResponse,
    summary="Reprocess a document — re-chunks and re-embeds from stored file"
)
def reprocess_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return KnowledgeBaseService.reprocess_document(db, doc_id, current_user.id)


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its chunks"
)
def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    KnowledgeBaseService.delete_document(db, doc_id, current_user.id)
    return None


# ──────────────────────────────────────────────────────────────
# Retrieval / RAG Query
# ──────────────────────────────────────────────────────────────

@router.post(
    "/retrieve",
    response_model=RetrievalResponse,
    summary="Retrieve relevant document chunks for a query (RAG)"
)
def retrieve_chunks(
    workspace_id: int = Query(..., description="Workspace to scope search"),
    schema: RetrievalRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Embeds the query and performs vector similarity search.
    Returns the top-K most relevant document chunk texts.
    """
    results = RetrievalService.retrieve(
        db=db,
        query=schema.query,
        workspace_id=workspace_id,
        knowledge_base_id=schema.knowledge_base_id,
        document_id=schema.document_id,
        file_type=schema.file_type,
        start_date=schema.start_date,
        end_date=schema.end_date,
        top_k=schema.top_k,
        offset=schema.offset,
        threshold=schema.threshold,
        user_id=current_user.id,
    )
    chunk_responses = [ChunkResponse(**r) for r in results]
    return RetrievalResponse(query=schema.query, results=chunk_responses, total=len(chunk_responses))
