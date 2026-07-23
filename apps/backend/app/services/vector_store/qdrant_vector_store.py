import logging
from typing import List, Dict, Any, Optional

from app.config import settings
from app.services.vector_store.vector_interface import VectorStoreInterface

logger = logging.getLogger("app.services.vector_store.qdrant_vector_store")

_qdrant_available = False
try:
    from qdrant_client import QdrantClient
    from qdrant_client import models
    _qdrant_available = True
except ImportError:
    QdrantClient = None
    models = None


class QdrantVectorStore(VectorStoreInterface):
    """
    Production-ready Qdrant Vector Database Integration.
    Supports persistent disk storage in Colab, metadata filtering, transactional document deletions,
    and named vectors designed for future Hybrid (Dense + Sparse) search capabilities.
    """

    def __init__(self, dimensions: int = 384):
        self.collection_name = settings.QDRANT_COLLECTION
        self.dimensions = dimensions
        self.client = None
        self._init_client()

    def _init_client(self):
        if not _qdrant_available:
            logger.warning("qdrant-client not installed. Qdrant is offline.")
            return

        try:
            # Zero-Config Setup: Connect to local folder storage if URL is not defined
            if settings.QDRANT_URL:
                logger.info(f"Connecting to Qdrant Cloud Cluster: {settings.QDRANT_URL}")
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY or None
                )
            else:
                logger.info("QDRANT_URL not defined. Connecting to persistent SQLite folder store 'qdrant_db'")
                self.client = QdrantClient(path="qdrant_db")

            # Ensure collection exists
            self._ensure_collection()
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            self.client = None

    def _ensure_collection(self):
        if not self.client:
            return

        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                logger.info(f"Creating Qdrant collection: '{self.collection_name}' with dimensions: {self.dimensions}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        # Dense named vector setup. Allows adding a "sparse" named vector configuration 
                        # in the future for Hybrid search without tearing down the collection.
                        "dense": models.VectorParams(
                            size=self.dimensions,
                            distance=models.Distance.COSINE
                        )
                    }
                )

            # Ensure payload indexes exist for filtering fields (workspace_id, knowledge_base_id, company_id)
            # This is required by Qdrant Cloud cluster settings when index requirements are enforced.
            for field in ["workspace_id", "knowledge_base_id", "company_id"]:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.INTEGER
                    )
                    logger.info(f"Ensured payload index for field '{field}'")
                except Exception as index_err:
                    logger.debug(f"Payload index creation bypassed/failed for field '{field}': {index_err}")
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")


    def add(self, chunk_id: int, embedding: List[float], metadata: Dict[str, Any]) -> None:
        if not self.client:
            logger.warning("Qdrant client not initialized. Vector not added.")
            return

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=chunk_id,
                        # Vector mapped to the dense namespace
                        vector={"dense": embedding},
                        payload=metadata
                    )
                ]
            )
            logger.debug(f"Successfully upserted point chunk_id={chunk_id} to Qdrant")
        except Exception as e:
            logger.error(f"Failed to upsert point to Qdrant: {e}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        if not self.client:
            logger.warning("Qdrant client not initialized. Search offline.")
            return []

        try:
            query_filter = None
            if filters:
                conditions = []
                
                # Tenancy and visibility locks
                company_id = filters.get("company_id")
                user_id = filters.get("user_id")
                
                if company_id is not None:
                    conditions.append(
                        models.FieldCondition(
                            key="company_id",
                            match=models.MatchValue(value=company_id)
                        )
                    )
                
                if user_id is not None:
                    # (visibility == "WORKSPACE") OR (visibility == "COMPANY") OR (created_by == user_id)
                    conditions.append(
                        models.Filter(
                            should=[
                                models.FieldCondition(key="visibility", match=models.MatchValue(value="WORKSPACE")),
                                models.FieldCondition(key="visibility", match=models.MatchValue(value="COMPANY")),
                                models.FieldCondition(key="created_by", match=models.MatchValue(value=user_id)),
                            ]
                        )
                    )

                for k, v in filters.items():
                    if k in ["company_id", "user_id"] or v is None:
                        continue
                    if k == "start_date":
                        conditions.append(
                            models.FieldCondition(
                                key="created_at",
                                range=models.Range(gte=v)
                            )
                        )
                    elif k == "end_date":
                        conditions.append(
                            models.FieldCondition(
                                key="created_at",
                                range=models.Range(lte=v)
                            )
                        )
                    elif k == "file_type":
                        # Support checking for mime_type
                        conditions.append(
                            models.FieldCondition(
                                key="mime_type",
                                match=models.MatchValue(value=v)
                            )
                        )
                    else:
                        if isinstance(v, list):
                            conditions.append(
                                models.FieldCondition(
                                    key=k,
                                    match=models.MatchAny(any=v)
                                )
                            )
                        else:
                            conditions.append(
                                models.FieldCondition(
                                    key=k,
                                    match=models.MatchValue(value=v)
                                )
                            )
                if conditions:
                    query_filter = models.Filter(must=conditions)

            # Query the dense named vector space using query_points (newer versions) or search (older versions)
            if hasattr(self.client, "query_points"):
                search_response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    using="dense",
                    query_filter=query_filter,
                    limit=top_k,
                    offset=offset,
                    score_threshold=threshold if threshold > 0.0 else None
                )
                search_results = search_response.points
            else:
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=("dense", query_embedding),
                    query_filter=query_filter,
                    limit=top_k,
                    offset=offset,
                    score_threshold=threshold if threshold > 0.0 else None
                )

            # Map results to match original memory vector interface
            return [
                {
                    "chunk_id": res.id,
                    "score": res.score,
                    "metadata": res.payload
                }
                for res in search_results
            ]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []


    def delete(self, chunk_id: int) -> None:
        if not self.client:
            return

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[chunk_id])
            )
            logger.debug(f"Deleted point chunk_id={chunk_id} from Qdrant")
        except Exception as e:
            logger.error(f"Failed to delete point from Qdrant: {e}")

    def delete_by_document(self, doc_id: int) -> None:
        """
        Transactional deletion helper.
        Safely wipes all vector chunks associated with a document.
        """
        if not self.client:
            return

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=doc_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Successfully deleted all vectors in Qdrant matching document_id={doc_id}")
        except Exception as e:
            logger.error(f"Failed to batch delete document vectors from Qdrant: {e}")
