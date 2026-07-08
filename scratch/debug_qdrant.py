# =========================================================
# QDRANT DIAGNOSTIC SCRIPT
# =========================================================
import os
import json
from qdrant_client import QdrantClient

# Load env variables from backend
backend_env_path = "/content/Nexora-AI/apps/backend/.env"
if os.path.exists(backend_env_path):
    print("Loading backend .env settings...")
    with open(backend_env_path, "r") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

qdrant_url = os.environ.get("QDRANT_URL")
qdrant_key = os.environ.get("QDRANT_API_KEY")
collection_name = os.environ.get("QDRANT_COLLECTION", "nexora_chunks")

print(f"QDRANT_URL: {qdrant_url}")
print(f"Collection Name: {collection_name}")

if not qdrant_url:
    print("❌ Error: QDRANT_URL is not set!")
    exit(1)

try:
    client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
    
    # 1. Check collection status
    status = client.get_collection(collection_name)
    print(f"\n✅ Collection status:\n  • Points count: {status.points_count}\n  • Status: {status.status}\n  • Vectors count: {status.vectors_count}")
    
    # 2. Retrieve points (up to 20)
    print("\n🔍 Inspecting points in Qdrant:")
    points, _ = client.scroll(
        collection_name=collection_name,
        limit=20,
        with_payload=True,
        with_vectors=False
    )
    
    if not points:
        print("  • No points found in collection!")
    else:
        for idx, p in enumerate(points):
            print(f"  [{idx + 1}] ID: {p.id}")
            print(f"      Payload: {json.dumps(p.payload, indent=6)}")
            
except Exception as e:
    print(f"❌ Qdrant diagnostic failed: {e}")
