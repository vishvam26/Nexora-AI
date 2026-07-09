# =========================================================
# NEXORA.AI — SQLite Chunks Inspector
# =========================================================
import os
import sqlite3

db_path = "/content/Nexora-AI/apps/backend/nexora_ai.db"

if not os.path.exists(db_path):
    print(f"❌ SQLite database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("==================================================")
print("📄 CHUNKS FOR 'vishva resume .pdf' (Doc ID: 2):")
print("==================================================")
cursor.execute("""
    SELECT chunk_index, token_count, text 
    FROM document_chunks 
    WHERE document_id = 2 
    ORDER BY chunk_index ASC
""")
rows = cursor.fetchall()
if not rows:
    print("No chunks found in database for Doc ID 2!")
for chunk_index, token_count, text in rows:
    print(f"\n--- Chunk #{chunk_index} ({token_count} tokens) ---")
    print(text)

conn.close()
