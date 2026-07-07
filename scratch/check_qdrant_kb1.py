import os
import sys

# Load env
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

sys.path.append(backend_dir)

from app.services.vector_store.qdrant_vector_store import QdrantVectorStore
from app.config import settings

print("=== QDRANT CONTENT CHECK ===")
print("QDRANT_URL:", settings.QDRANT_URL)
print("QDRANT_COLLECTION:", settings.QDRANT_COLLECTION)

_vector_store = QdrantVectorStore()

# Retrieve all points in nexora_chunks collection (up to 100)
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    
    # Scroll through points
    records, next_page = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        limit=100,
        with_payload=True,
        with_vectors=False
    )
    
    print(f"\nTotal points found in Qdrant collection: {len(records)}")
    
    kb_counts = {}
    doc_counts = {}
    for r in records:
        payload = r.payload or {}
        kb_id = payload.get("knowledge_base_id")
        doc_id = payload.get("document_id")
        kb_counts[kb_id] = kb_counts.get(kb_id, 0) + 1
        doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
        
    print("\nPoints grouped by Knowledge Base ID:")
    for kb_id, count in kb_counts.items():
        print(f" - KB ID: {kb_id} | Chunks count: {count}")
        
    print("\nPoints grouped by Document ID:")
    for doc_id, count in doc_counts.items():
        print(f" - Doc ID: {doc_id} | Chunks count: {count}")
        
except Exception as e:
    print(f"Failed to scroll Qdrant: {e}")
