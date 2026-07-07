import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from qdrant_client import QdrantClient
from qdrant_client import models
from app.config import settings

print("Connecting to Qdrant Cloud Cluster to create payload indexes...")
print("QDRANT_URL:", settings.QDRANT_URL)
print("QDRANT_COLLECTION:", settings.QDRANT_COLLECTION)

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY
)

for field in ["workspace_id", "knowledge_base_id"]:
    try:
        print(f"Creating payload index for '{field}'...")
        client.create_payload_index(
            collection_name=settings.QDRANT_COLLECTION,
            field_name=field,
            field_schema=models.PayloadSchemaType.INTEGER
        )
        print(f"Success ✅ for '{field}'")
    except Exception as e:
        print(f"Failed or already exists ❌ for '{field}': {e}")

print("\nRunning a quick test search with filters...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(settings.EMBEDDING_MODEL)
query_vector = model.encode("Whose result is this?").tolist()

try:
    # Query with filter
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
                    match=models.MatchValue(value=2)
                )
            ]
        ),
        limit=5
    )
    print(f"Search Success ✅. Matches found: {len(res_obj.points)}")
    for p in res_obj.points:
        print(f"Score: {p.score:.4f} | Payload: {p.payload}")
except Exception as e:
    print(f"Search failed with filter ❌: {e}")
