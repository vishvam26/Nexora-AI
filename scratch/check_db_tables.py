import sqlite3

db_path = "/content/Nexora-AI/apps/backend/nexora_ai.db"
print(f"=== INSPECTING TABLES IN {db_path} ===")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for t in tables:
        print(f" - {t[0]}")
        
    # Get schema of document_chunks if it exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks';")
    exists = cursor.fetchone()
    if exists:
        print("\nSchema for 'document_chunks':")
        cursor.execute("PRAGMA table_info(document_chunks);")
        for col in cursor.fetchall():
            print(f"  Column: {col[1]} ({col[2]})")
    else:
        print("\n'document_chunks' table does NOT exist in this file!")
        
    conn.close()
except Exception as e:
    print(f"Error inspecting SQLite file: {e}")
