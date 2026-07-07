import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from app.config import settings

print("QDRANT_URL:", settings.QDRANT_URL)
print("QDRANT_COLLECTION:", settings.QDRANT_COLLECTION)

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)

# Test Search
query = "Whose result is this?"
model = SentenceTransformer(settings.EMBEDDING_MODEL)
query_vector = model.encode(query).tolist()

try:
    # Search WITHOUT filters
    if hasattr(client, "query_points"):
        res_obj = client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_vector,
            using="dense",
            limit=10
        )
        results = res_obj.points
    else:
        results = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=("dense", query_vector),
            limit=10,
            with_payload=True
        )
        
    print(f"\nUnfiltered Search results for '{query}':")
    for res in results:
        print(f"Score: {res.score:.4f} | ID: {res.id} | Payload: {res.payload}")
except Exception as e:
    print(f"Search failed: {e}")
