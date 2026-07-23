import time
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.embedding.embedding_service import EmbeddingService
from app.services.vector_store.qdrant_vector_store import QdrantVectorStore
from app.models.retrieval_log import RetrievalLog

logger = logging.getLogger("app.services.retrieval_service")

_embedder = EmbeddingService()
_vector_store = QdrantVectorStore()


class RetrievalService:
    """
    Performs similarity search against document chunks for a given query using Qdrant.
    Records latency metrics and outputs hybrid-ready scoring payloads.
    """

    @staticmethod
    def retrieve(
        db: Session,
        query: str,
        workspace_id: int,
        knowledge_base_id: Optional[int] = None,
        document_id: Optional[int] = None,
        file_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        top_k: int = 5,
        offset: int = 0,
        threshold: float = 0.0,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        1. Embeds the query.
        2. Translates filters and queries Qdrant with offset.
        3. Enriches returned points with SQL database chunk text.
        4. Calculates vector/keyword/final scores.
        5. Saves query latency and results to RetrievalLog.
        """
        start_time = time.perf_counter()

        # Resolve company_id and manager status
        company_id = 1
        is_manager = False
        if user_id:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                if user.company_id:
                    company_id = user.company_id
                if user.company_role in ["OWNER", "ADMIN"]:
                    is_manager = True
                else:
                    from app.models.workspace_member import WorkspaceMember
                    member = db.query(WorkspaceMember).filter(
                        WorkspaceMember.workspace_id == workspace_id,
                        WorkspaceMember.user_id == user_id,
                        WorkspaceMember.is_active == True
                    ).first()
                    if member and member.workspace_role == "MANAGER":
                        is_manager = True

        # 1. Embed query
        query_embedding = _embedder.generate_query_embedding(query)

        # 2. Build metadata filters
        filters: Dict[str, Any] = {
            "workspace_id": workspace_id,
            "company_id": company_id,
            "user_id": user_id,
            "is_manager": is_manager,
        }
        if knowledge_base_id:
            filters["knowledge_base_id"] = knowledge_base_id
        if document_id:
            filters["document_id"] = document_id
        if file_type:
            filters["file_type"] = file_type
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date

        # 3. Search Qdrant
        matches = _vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=threshold,
            filters=filters,
            offset=offset
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if not matches:
            # Write empty log
            try:
                log = RetrievalLog(
                    workspace_id=workspace_id,
                    query=query,
                    intent="Search",
                    latency_ms=float(latency_ms),
                    confidence_score=0.0,
                    chunks_retrieved=0,
                    chunks_accepted=0,
                    chunks_rejected=0,
                )
                db.add(log)
                db.commit()
            except Exception as log_err:
                logger.warning(f"Failed to save retrieval log: {log_err}")
            return []

        # 4. Enrich chunks and calculate scores
        results = []
        matched_doc_ids = set()

        for match in matches:
            chunk = DocumentChunkRepository.get_by_id(db, match["chunk_id"])
            if chunk:
                matched_doc_ids.add(chunk.document_id)
                score = round(match["score"], 4)
                
                # Retrieve filename from document relationship if available
                filename = match["metadata"].get("file_name", "document")
                created_at = match["metadata"].get("created_at", "")

                results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    # Hybrid-ready score payload
                    "vector_score": score,
                    "keyword_score": 0.0,
                    "final_score": score,
                    "page_number": chunk.page or 1,
                    "section_title": chunk.section or "",
                    "file_name": filename,
                    "created_at": created_at,
                })

        # 5. Persist Retrieval Log
        try:
            log = RetrievalLog(
                workspace_id=workspace_id,
                query=query,
                intent="Search",
                latency_ms=float(latency_ms),
                confidence_score=1.0,
                chunks_retrieved=len(matches),
                chunks_accepted=len(matches),
                chunks_rejected=0,
            )
            db.add(log)
            db.commit()
            logger.info(f"Saved retrieval log id={log.id} | query='{query}' | latency={latency_ms}ms")
        except Exception as log_err:
            logger.warning(f"Failed to save retrieval log: {log_err}")

        return results
