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
    vector_score: float
    keyword_score: float
    final_score: float
    page_number: int
    section_title: str
    file_name: str
    created_at: str

    model_config = {"from_attributes": True}


class RetrievalRequest(BaseModel):
    query: str
    knowledge_base_id: Optional[int] = None
    document_id: Optional[int] = None
    file_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_k: int = 5
    offset: int = 0
    threshold: float = 0.0


class RetrievalResponse(BaseModel):
    query: str
    results: List[ChunkResponse]
    total: int

    model_config = {"from_attributes": True}
