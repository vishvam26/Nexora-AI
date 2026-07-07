import sqlite3

db_path = "d:\\Nexora-AI\\apps\\backend\\nexora_ai.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Knowledge Bases ===")
cursor.execute("SELECT id, title, workspace_id FROM knowledge_bases")
for row in cursor.fetchall():
    print(row)

print("\n=== Knowledge Documents ===")
cursor.execute("SELECT id, knowledge_base_id, filename, mime_type, status, storage_path FROM knowledge_documents")
for row in cursor.fetchall():
    print(row)

print("\n=== Document Chunks ===")
cursor.execute("SELECT id, document_id, chunk_index, token_count, page, section, embedding_status FROM document_chunks")
chunks = cursor.fetchall()
print(f"Total chunks in DB: {len(chunks)}")
for row in chunks[:10]:
    print(row)

conn.close()
