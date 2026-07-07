import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

print("=== DIAGNOSTIC START ===")

# 1. Check Env
print(f"QDRANT_URL in env: {os.environ.get('QDRANT_URL')}")
print(f"QDRANT_API_KEY in env: {'Set (starts with ' + os.environ.get('QDRANT_API_KEY')[:10] + ')' if os.environ.get('QDRANT_API_KEY') else 'Not Set'}")

# 2. Check imports
try:
    from pypdf import PdfReader
    print("pypdf import: SUCCESS ✅")
except ImportError as e:
    print(f"pypdf import: FAILED ❌ ({e})")

try:
    from qdrant_client import QdrantClient
    print("qdrant-client import: SUCCESS ✅")
except ImportError as e:
    print(f"qdrant-client import: FAILED ❌ ({e})")

# 3. Check settings loading
try:
    from app.config import settings
    print("Settings loading: SUCCESS ✅")
    print(f"Settings.QDRANT_URL: {settings.QDRANT_URL}")
    print(f"Settings.QDRANT_API_KEY: {'Set' if settings.QDRANT_API_KEY else 'Not Set'}")
except Exception as e:
    print(f"Settings loading: FAILED ❌ ({e})")

# 4. Check Qdrant Connection
if os.environ.get("QDRANT_URL"):
    try:
        client = QdrantClient(
            url=os.environ.get("QDRANT_URL"),
            api_key=os.environ.get("QDRANT_API_KEY")
        )
        collections = client.get_collections().collections
        print("Qdrant connection: SUCCESS ✅")
        print(f"Collections found: {[c.name for c in collections]}")
    except Exception as e:
        print(f"Qdrant connection: FAILED ❌ ({e})")

print("=== DIAGNOSTIC END ===")
