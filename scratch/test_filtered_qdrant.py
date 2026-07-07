import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from app.services.vector_store.qdrant_vector_store import QdrantVectorStore
from app.services.embedding.embedding_service import EmbeddingService
from app.config import settings

print("=== DETAILED FILTERED SEARCH TEST ===")
_vector_store = QdrantVectorStore()
_embedder = EmbeddingService()

query = "Whose result is this?"
query_embedding = _embedder.generate_query_embedding(query)

# 1. Search with workspace_id and list of knowledge_base_ids
filters = {"workspace_id": 1, "knowledge_base_id": [2]}
print(f"\nSearching with filters: {filters}")
matches = _vector_store.search(
    query_embedding=query_embedding,
    top_k=5,
    threshold=0.1,
    filters=filters
)
print("Matches found:", len(matches))
for m in matches:
    print(m)

# 2. Search with workspace_id and single integer knowledge_base_id
filters2 = {"workspace_id": 1, "knowledge_base_id": 2}
print(f"\nSearching with filters: {filters2}")
matches2 = _vector_store.search(
    query_embedding=query_embedding,
    top_k=5,
    threshold=0.1,
    filters=filters2
)
print("Matches found:", len(matches2))
for m in matches2:
    print(m)
