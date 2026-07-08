# =========================================================
# NEXORA.AI — SQLite Log Inspector
# =========================================================
import os
import sqlite3
import json

db_path = "/content/Nexora-AI/apps/backend/nexora_ai.db"

if not os.path.exists(db_path):
    print(f"❌ SQLite database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("==================================================")
print("📚 KNOWLEDGE BASES:")
print("==================================================")
cursor.execute("SELECT id, title, workspace_id FROM knowledge_bases")
for row in cursor.fetchall():
    print(f"KB ID: {row[0]} | Title: {row[1]} | Workspace ID: {row[2]}")

print("\n==================================================")
print("📄 DOCUMENTS:")
print("==================================================")
cursor.execute("SELECT id, filename, knowledge_base_id, status FROM knowledge_documents")
for row in cursor.fetchall():
    print(f"Doc ID: {row[0]} | Filename: {row[1]} | KB ID: {row[2]} | Status: {row[3]}")

print("\n==================================================")
print("💬 RECENT MESSAGES:")
print("==================================================")
cursor.execute("SELECT id, role, content FROM messages ORDER BY id DESC LIMIT 5")
for row in cursor.fetchall():
    print(f"Message ID: {row[0]} | Role: {row[1]} | Content: {row[2].strip()}")

print("\n==================================================")
print("🔍 RETRIEVAL LOGS:")
print("==================================================")
cursor.execute("SELECT id, query, latency_ms, top_k, returned_document_ids, created_at FROM retrieval_logs ORDER BY id DESC LIMIT 5")
logs = cursor.fetchall()
if not logs:
    print("No retrieval logs found!")
for row in logs:
    print(f"Log ID: {row[0]} | Query: {row[1]} | Latency: {row[2]}ms | Top K: {row[3]} | Doc IDs: {row[4]} | Created: {row[5]}")

conn.close()
