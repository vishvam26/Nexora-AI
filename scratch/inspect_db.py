import sqlite3
import os

db_path = "/content/Nexora-AI/apps/backend/nexora_ai.db"

if not os.path.exists(db_path):
    print(f"❌ SQLite database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("==================================================")
print("📄 DOCUMENTS IN SQLITE:")
print("==================================================")
cursor.execute("SELECT id, filename, status, workspace_id, knowledge_base_id FROM documents")
docs = cursor.fetchall()
for doc in docs:
    doc_id, filename, status, ws_id, kb_id = doc
    cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = ?", (doc_id,))
    chunk_count = cursor.fetchone()[0]
    print(f"Doc ID: {doc_id} | Name: '{filename}' | Status: {status} | Chunks: {chunk_count} | Workspace: {ws_id} | KB: {kb_id}")

print("\n==================================================")
print("📄 FIRST CHUNK OF EACH DOCUMENT:")
print("==================================================")
for doc in docs:
    doc_id, filename, _, _, _ = doc
    cursor.execute("SELECT chunk_index, text FROM document_chunks WHERE document_id = ? LIMIT 1", (doc_id,))
    chunk = cursor.fetchone()
    if chunk:
        print(f"\nDocument: '{filename}' (ID: {doc_id}) | First Chunk:")
        print(chunk[1][:300])
    else:
        print(f"\nDocument: '{filename}' (ID: {doc_id}) has no chunks in SQLite!")

conn.close()
