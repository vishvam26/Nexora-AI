import sqlite3

db_path = "/content/Nexora-AI/apps/backend/nexora_ai.db"
print(f"=== INSPECTING DOCUMENTS AND CHUNKS IN SQLite ===")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Print knowledge bases
    print("\n--- Knowledge Bases ---")
    cursor.execute("SELECT id, title, created_at FROM knowledge_bases;")
    for r in cursor.fetchall():
        print(f"KB ID: {r[0]} | Title: {r[1]} | Created: {r[2]}")
        
    # Print documents
    print("\n--- Knowledge Documents ---")
    cursor.execute("SELECT id, knowledge_base_id, filename, status, created_at FROM knowledge_documents;")
    for r in cursor.fetchall():
        print(f"Doc ID: {r[0]} | KB ID: {r[1]} | Name: {r[2]} | Status: {r[3]} | Created: {r[4]}")
        
    # Print document chunk stats
    print("\n--- Document Chunks Status ---")
    cursor.execute("SELECT document_id, embedding_status, COUNT(*) FROM document_chunks GROUP BY document_id, embedding_status;")
    for r in cursor.fetchall():
        print(f"Doc ID: {r[0]} | Embedding Status: {r[1]} | Chunk Count: {r[2]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
