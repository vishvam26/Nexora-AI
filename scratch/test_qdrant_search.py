import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Initialize settings
from app.config import settings

print("QDRANT_URL:", settings.QDRANT_URL)
print("QDRANT_COLLECTION:", settings.QDRANT_COLLECTION)

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)

# 1. Print collection info
try:
    info = client.get_collection(settings.QDRANT_COLLECTION)
    print(f"\nCollection {settings.QDRANT_COLLECTION} Info:")
    print(f"Points count: {info.points_count}")
except Exception as e:
    print(f"Failed to get collection: {e}")

# 2. Get first 5 points
try:
    points, _ = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        limit=5,
        with_payload=True,
        with_vectors=False
    )
    print("\nFirst 5 points in collection:")
    for p in points:
        print(f"Point ID: {p.id}")
        print(f"Payload: {p.payload}")
except Exception as e:
    print(f"Failed to scroll points: {e}")

# 3. Test Search
query = "Whose resume is this?"
model = SentenceTransformer(settings.EMBEDDING_MODEL)
query_vector = model.encode(query).tolist()

try:
    from qdrant_client import models
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=("dense", query_vector),
        limit=5,
        with_payload=True
    )
    print(f"\nSearch results for '{query}':")
    for res in results:
        print(f"Score: {res.score} | Payload: {res.payload}")
except Exception as e:
    print(f"Search failed: {e}")
