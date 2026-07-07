import os
import sys

# Load env
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path, override=True) # Force override to use absolute SQLite DB path

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

print("=== DIAGNOSTICS FOR KB 1 (resume-old) vs KB 6 (resume-new) ===")
print("DATABASE_URL:", settings.DATABASE_URL)

query = "Whose resume is this?"
workspace_id = 1

for kb_id in [1, 6]:
    print(f"\n----------------------------------------")
    print(f"Testing KB ID {kb_id}...")
    try:
        # Run adaptive retrieval
        rag_context = AdaptiveRetrievalService.retrieve_context(
            db=db,
            user_query=query,
            workspace_id=workspace_id,
            knowledge_base_id=[kb_id],
            top_k=5,
            similarity_threshold=0.1
        )
        print(f"KB ID {kb_id} RAG: has_knowledge={rag_context.has_knowledge} | chunks={len(rag_context.chunks_used)}")
        for idx, chunk in enumerate(rag_context.chunks_used):
            print(f"   Chunk {idx+1}: Doc ID {chunk.document_id} | Score: {chunk.score:.4f}")
            # print preview
            from app.models.document_chunk import DocumentChunk
            dc = db.query(DocumentChunk).filter(DocumentChunk.id == chunk.chunk_id).first()
            if dc:
                print(f"     Text: {dc.text[:120]}...")
    except Exception as e:
        print(f"Error testing KB ID {kb_id}: {e}")

db.close()
