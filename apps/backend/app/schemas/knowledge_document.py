from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class KnowledgeDocumentResponse(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    mime_type: str
    size: int
    status: str
    pages: Optional[int]
    language: Optional[str]
    checksum: Optional[str]
    storage_path: str
    doc_metadata: Optional[Dict[str, Any]]
    uploaded_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocumentListResponse(BaseModel):
    documents: List[KnowledgeDocumentResponse]
    total: int

    model_config = {"from_attributes": True}


class DocumentStatsResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    pages: int
    total_chunks: int
    embedded_chunks: int
    total_words: int
    total_characters: int
    language: str

    model_config = {"from_attributes": True}


class ChunkResponse(BaseModel):
    chunk_id: int
    document_id: int
    text: str
    score: float
    page: Optional[int]
    section: Optional[str]
    token_count: int

    model_config = {"from_attributes": True}


class RetrievalRequest(BaseModel):
    query: str
    knowledge_base_id: Optional[int] = None
    top_k: int = 5
    threshold: float = 0.0


class RetrievalResponse(BaseModel):
    query: str
    results: List[ChunkResponse]
    total: int

    model_config = {"from_attributes": True}
