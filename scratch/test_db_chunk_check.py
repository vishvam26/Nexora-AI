import os
import sys

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend")))

from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.config import settings

print("=== DB INTEGRITY CHECK ===")
print("settings.DATABASE_URL:", settings.DATABASE_URL)

db = SessionLocal()

# Try to query chunk ID 15
print("\nQuerying DocumentChunk ID 15 using SessionLocal...")
try:
    chunk = db.query(DocumentChunk).filter(DocumentChunk.id == 15).first()
    if chunk:
        print("Chunk 15 found! ✅")
        print(f"Text preview: {chunk.text[:150]}")
        print(f"Doc ID: {chunk.document_id}")
    else:
        print("Chunk 15 NOT found! ❌ (Returns None)")
except Exception as e:
    print(f"Query failed with error ❌: {e}")

# Try to query chunk ID 10
print("\nQuerying DocumentChunk ID 10 using SessionLocal...")
try:
    chunk2 = db.query(DocumentChunk).filter(DocumentChunk.id == 10).first()
    if chunk2:
        print("Chunk 10 found! ✅")
        print(f"Text preview: {chunk2.text[:150]}")
        print(f"Doc ID: {chunk2.document_id}")
    else:
        print("Chunk 10 NOT found! ❌ (Returns None)")
except Exception as e:
    print(f"Query failed with error ❌: {e}")

db.close()
