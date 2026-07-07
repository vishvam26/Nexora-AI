import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from qdrant_client import QdrantClient
from qdrant_client import models
from sentence_transformers import SentenceTransformer
from app.config import settings

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)

query = "Whose result is this?"
model = SentenceTransformer(settings.EMBEDDING_MODEL)
query_vector = model.encode(query).tolist()

print("--- TESTING MATCH ANY (any=[3]) ---")
try:
    res_obj = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        using="dense",
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="workspace_id",
                    match=models.MatchValue(value=1)
                ),
                models.FieldCondition(
                    key="knowledge_base_id",
                    match=models.MatchAny(any=[3])
                )
            ]
        ),
        limit=5
    )
    print(f"MatchAny([3]) Matches found: {len(res_obj.points)}")
    for p in res_obj.points:
        print(f"Score: {p.score:.4f} | KB ID: {p.payload.get('knowledge_base_id')}")
except Exception as e:
    print(f"MatchAny failed: {e}")

print("\n--- TESTING MATCH VALUE (value=3) ---")
try:
    res_obj = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        using="dense",
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="workspace_id",
                    match=models.MatchValue(value=1)
                ),
                models.FieldCondition(
                    key="knowledge_base_id",
                    match=models.MatchValue(value=3)
                )
            ]
        ),
        limit=5
    )
    print(f"MatchValue(3) Matches found: {len(res_obj.points)}")
    for p in res_obj.points:
        print(f"Score: {p.score:.4f} | KB ID: {p.payload.get('knowledge_base_id')}")
except Exception as e:
    print(f"MatchValue failed: {e}")
