import os
import sys

# Load env variables from apps/backend/.env explicitly if running from root
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    print(f"Loading env from: {env_path}")
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Add app to path
sys.path.append(backend_dir)

# IMPORTANT: Register all models to avoid SQLAlchemy mapper lookup failures
import app.db.base

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
from app.config import settings

db = SessionLocal()

print("=== RETRIEVAL DIAGNOSTICS FOR QUERY ===")
print("settings.DATABASE_URL:", settings.DATABASE_URL)

query = "Whose result is this?"
workspace_id = 1
kb_id = 3  # The 'result' knowledge base ID

print(f"Query: '{query}'")
print(f"Workspace: {workspace_id}, Knowledge Base: {kb_id}")

try:
    # 1. Run RAG retrieval
    rag_context = AdaptiveRetrievalService.retrieve_context(
        db=db,
        user_query=query,
        workspace_id=workspace_id,
        knowledge_base_id=[kb_id],
        top_k=settings.RAG_TOP_K,
        similarity_threshold=settings.SIMILARITY_THRESHOLD,
        max_context_tokens=settings.MAX_CONTEXT_TOKENS,
        enable_reranking=settings.ENABLE_RERANKING,
    )
    
    print("\n--- RAG RETRIEVAL RESULT ---")
    print(f"has_knowledge: {rag_context.has_knowledge}")
    print(f"Number of chunks retrieved: {len(rag_context.chunks_used)}")
    for i, chunk in enumerate(rag_context.chunks_used):
        print(f"Chunk {i+1}: Doc ID {chunk.document_id} | Page {chunk.page} | Score {chunk.score:.4f}")
        # Fetch chunk text from DB
        from app.models.document_chunk import DocumentChunk
        dc = db.query(DocumentChunk).filter(DocumentChunk.id == chunk.chunk_id).first()
        if dc:
            print(f"Text Preview: {dc.text[:200]}...")
            
    # 2. Print formatted context
    print("\n--- FORMATTED CONTEXT ---")
    print(rag_context.formatted_context)
    
except Exception as e:
    print(f"Retrieval diagnostics failed: {e}")
    import traceback
    traceback.print_exc()

db.close()
