# =========================================================
# NEXORA.AI — RAG / Qdrant Database Restore Utility
# =========================================================
import os
import json
import sqlite3
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Load env variables from backend
backend_env_path = "/content/Nexora-AI/apps/backend/.env"
if os.path.exists(backend_env_path):
    print("Loading backend .env settings...")
    with open(backend_env_path, "r") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

db_path = "/content/Nexora-AI/apps/backend/nexora_ai.db"
qdrant_url = os.environ.get("QDRANT_URL")
qdrant_key = os.environ.get("QDRANT_API_KEY")
collection_name = os.environ.get("QDRANT_COLLECTION", "nexora_chunks")

if not os.path.exists(db_path):
    print(f"❌ SQLite database not found at: {db_path}")
    exit(1)

if not qdrant_url:
    print("❌ QDRANT_URL is not set!")
    exit(1)

print(f"Connecting to Qdrant: {qdrant_url}")
print(f"Connecting to SQLite: {db_path}")

try:
    # Initialize clients
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
    print("Loading SentenceTransformer model...")
    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Fetch all documents
    cursor.execute("""
        SELECT d.id, d.filename, d.mime_type, d.created_at, d.knowledge_base_id, kb.workspace_id
        FROM knowledge_documents d
        JOIN knowledge_bases kb ON d.knowledge_base_id = kb.id
        WHERE d.deleted_at IS NULL
    """)
    documents = cursor.fetchall()
    print(f"\nFound {len(documents)} documents to restore:")
    
    total_restored = 0
    for doc_id, filename, mime_type, created_at, kb_id, workspace_id in documents:
        print(f"\n📄 Document ID {doc_id}: '{filename}' (KB: {kb_id}, Workspace: {workspace_id})")
        
        # Fetch chunks for this document
        cursor.execute("""
            SELECT id, chunk_index, text, page, section, token_count
            FROM document_chunks
            WHERE document_id = ?
        """, (doc_id,))
        chunks = cursor.fetchall()
        
        if not chunks:
            print("  ⚠️ No chunks found in SQLite database for this document.")
            continue
            
        print(f"  • Found {len(chunks)} chunks in SQLite database. Embedding and uploading...")
        
        points = []
        for chunk_id, chunk_index, text, page, section, token_count in chunks:
            # Generate embedding
            emb = embedder.encode(text).tolist()
            
            # Prepare metadata payload
            payload = {
                "workspace_id": int(workspace_id),
                "knowledge_base_id": int(kb_id),
                "document_id": int(doc_id),
                "page_number": int(page) if page else 1,
                "section_title": str(section) if section else "",
                "token_count": int(token_count),
                "file_name": str(filename),
                "mime_type": str(mime_type),
                "created_at": str(created_at)
            }
            
            # Add to upsert list
            points.append(
                models.PointStruct(
                    id=int(chunk_id),
                    vector={"dense": emb},
                    payload=payload
                )
            )
            
            # Save embedding JSON to SQLite for local copy
            emb_json = json.dumps(emb)
            cursor.execute("""
                UPDATE document_chunks
                SET embedding = ?, embedding_status = 'Completed'
                WHERE id = ?
            """, (emb_json, chunk_id))
            
        # Upsert batch to Qdrant
        if points:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"  ✅ Successfully uploaded {len(points)} chunks to Qdrant!")
            
            # Mark document status as Completed in SQLite
            cursor.execute("""
                UPDATE knowledge_documents
                SET status = 'Completed'
                WHERE id = ?
            """, (doc_id,))
            total_restored += len(points)
            
    conn.commit()
    conn.close()
    print(f"\n🎉 SUCCESS! Restored {total_restored} total chunks to Qdrant collection '{collection_name}'!")
    
except Exception as e:
    print(f"❌ Restoration failed: {e}")
