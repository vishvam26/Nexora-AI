import sqlite3
import os

db_path = "d:\\Nexora-AI\\apps\\backend\\nexora_ai.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get documents
cursor.execute("SELECT id, filename, status, pages, storage_path FROM knowledge_documents")
docs = cursor.fetchall()

output = []
output.append("=== DOCUMENTS ===")
for doc in docs:
    output.append(str(doc))

# Get chunks of document
output.append("\n=== CHUNKS ===")
cursor.execute("SELECT id, document_id, chunk_index, text, token_count FROM document_chunks")
chunks = cursor.fetchall()
output.append(f"Total Chunks: {len(chunks)}")
for chunk in chunks:
    # Print chunk index, doc id and first 100 characters of text
    text_preview = chunk[3][:150].replace('\n', ' ')
    output.append(f"Chunk ID: {chunk[0]} | Doc ID: {chunk[1]} | Index: {chunk[2]} | Tokens: {chunk[4]} | Text: {text_preview}")

# Save to output file
scratch_dir = "d:\\Nexora-AI\\scratch"
os.makedirs(scratch_dir, exist_ok=True)
output_path = os.path.join(scratch_dir, "db_rag_report.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print(f"Report saved to {output_path}")
conn.close()
