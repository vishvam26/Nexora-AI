import os
import sys

# Load env
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

sys.path.append(backend_dir)

# Import models
import app.db.base

from app.db.session import SessionLocal
from app.services.vector_store.qdrant_vector_store import QdrantVectorStore
from app.services.embedding.embedding_service import EmbeddingService
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.keyword_service import KeywordService
from app.services.hybrid_search_service import HybridSearchService
from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
from app.config import settings

db = SessionLocal()
_vector_store = QdrantVectorStore()
_embedder = EmbeddingService()

query = "Whose result is this?"
workspace_id = 1
kb_id = 3

print("=== STEP-BY-STEP RETRIEVAL DEBUG ===")
print("Database URL:", settings.DATABASE_URL)

# Step 1: Vector Search matches
print("\n--- Step 1: Raw Vector Store Search ---")
query_embedding = _embedder.generate_query_embedding(query)
filters = {"workspace_id": workspace_id, "knowledge_base_id": [kb_id]}
vector_matches = _vector_store.search(
    query_embedding=query_embedding,
    top_k=20,
    threshold=0.1,
    filters=filters
)
print(f"vector_matches count: {len(vector_matches)}")
for m in vector_matches:
    print(f"Match ID: {m['chunk_id']} | Score: {m['score']:.4f}")

# Step 2: Fetch Chunks from DB
print("\n--- Step 2: Fetch Chunks from DB ---")
vector_results = []
for m in vector_matches:
    chunk_id = m["chunk_id"]
    chunk = DocumentChunkRepository.get_by_id(db, chunk_id)
    if chunk:
        print(f"Found Chunk ID: {chunk.id} in DB ✅ | Doc ID: {chunk.document_id} | Text: {chunk.text[:50]}...")
        vector_results.append(chunk)
    else:
        print(f"Chunk ID: {chunk_id} NOT found in DB ❌")

# Step 3: Hybrid Search results
print("\n--- Step 3: HybridSearchService.search ---")
try:
    hybrid_results = HybridSearchService.search(
        db=db,
        query=query,
        workspace_id=workspace_id,
        knowledge_base_id=[kb_id],
        vector_weight=0.7,
        keyword_weight=0.3,
        top_k=10,
        threshold=0.1
    )
    print(f"hybrid_results count: {len(hybrid_results)}")
    for r in hybrid_results:
        print(f"Chunk ID: {r['chunk_id']} | Merged Score: {r['score']:.4f} | Text: {r['text'][:50]}...")
except Exception as e:
    print(f"Hybrid search failed: {e}")

# Step 4: Adaptive Retrieval Context
print("\n--- Step 4: AdaptiveRetrievalService.retrieve_context ---")
try:
    rag_context = AdaptiveRetrievalService.retrieve_context(
        db=db,
        user_query=query,
        workspace_id=workspace_id,
        knowledge_base_id=[kb_id]
    )
    print(f"rag_context.has_knowledge: {rag_context.has_knowledge}")
    print(f"rag_context.chunks_used count: {len(rag_context.chunks_used)}")
except Exception as e:
    print(f"Adaptive context failed: {e}")

db.close()
