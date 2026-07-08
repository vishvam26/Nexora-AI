# =========================================================
# NEXORA.AI — Consolidated One-Cell Setup & Run Script
# =========================================================
import os
import sys
import time
import secrets
import sqlite3
import subprocess

REPO_DIR = "/content/Nexora-AI"
BACKEND_DIR = os.path.join(REPO_DIR, "apps", "backend")

# Helper function to safely read Colab Secrets without throwing exceptions on missing keys
def get_colab_secret(key):
    try:
        from google.colab import userdata
        return userdata.get(key)
    except Exception:
        return None

# Clean up stale Hugging Face lock files to prevent caching hangs
print("🧹 Cleaning up stale Hugging Face cache locks...", flush=True)
hf_cache = os.path.expanduser("~/.cache/huggingface")
if os.path.exists(hf_cache):
    for root, dirs, files in os.walk(hf_cache):
        for file in files:
            if file.endswith(".lock"):
                lock_file = os.path.join(root, file)
                try:
                    os.remove(lock_file)
                    print(f"  Removed stale lock file: {lock_file}", flush=True)
                except Exception:
                    pass

# 1. Clone or Update Repo
print("📥 Setting up repository...", flush=True)
if not os.path.isdir(REPO_DIR):
    subprocess.run(["git", "clone", "https://github.com/vishvam26/Nexora-AI.git", REPO_DIR], check=True)
else:
    print("ℹ️ Repo already exists, resetting to origin/main...", flush=True)
    os.chdir(REPO_DIR)
    subprocess.run(["git", "fetch", "--all"], check=True)
    subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)

# 2. Install Dependencies
print("📦 Installing system requirements & backend dependencies...", flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", os.path.join(BACKEND_DIR, "requirements.txt")], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyngrok", "huggingface_hub[hf_xet]", "hf_xet"], check=True)

# 3. Import Google Colab Userdata (Secrets) & Set Environment Variables
print("🔑 Configuring environment from Colab Secrets...", flush=True)

groq_key = get_colab_secret("GROQ_API_KEY")
secret_key = get_colab_secret("SECRET_KEY")
supabase_url = get_colab_secret("SUPABASE_URL")
supabase_key = get_colab_secret("SUPABASE_KEY")
ngrok_token = get_colab_secret("NGROK_AUTH_TOKEN")
hf_token = get_colab_secret("HF_TOKEN")
google_key = get_colab_secret("GOOGLE_API_KEY")
qdrant_url = get_colab_secret("QDRANT_URL")
qdrant_key = get_colab_secret("QDRANT_API_KEY")

# Auto-generate a secure random SECRET_KEY if not provided in Colab Secrets to prevent startup crash
if not secret_key or secret_key == "CHANGE_THIS_LATER_IN_ENV":
    secret_key = secrets.token_hex(32)
    print(f"🔑 Generated a temporary secure SECRET_KEY: {secret_key}", flush=True)

# Set in os.environ for current process
if groq_key: os.environ["GROQ_API_KEY"] = groq_key
if secret_key: os.environ["SECRET_KEY"] = secret_key
if supabase_url: os.environ["SUPABASE_URL"] = supabase_url
if supabase_key: os.environ["SUPABASE_KEY"] = supabase_key
if hf_token: os.environ["HF_TOKEN"] = hf_token
if google_key: os.environ["GOOGLE_API_KEY"] = google_key
if qdrant_url: os.environ["QDRANT_URL"] = qdrant_url
if qdrant_key: os.environ["QDRANT_API_KEY"] = qdrant_key

# Also write them to the .env file in the backend to ensure uvicorn reads them!
try:
    env_path = os.path.join(BACKEND_DIR, ".env")
    existing_env = {}
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    existing_env[k.strip()] = v.strip()

    # Update with Colab secrets
    if groq_key: existing_env["GROQ_API_KEY"] = groq_key
    if secret_key: existing_env["SECRET_KEY"] = secret_key
    if supabase_url: existing_env["SUPABASE_URL"] = supabase_url
    if supabase_key: existing_env["SUPABASE_KEY"] = supabase_key
    if hf_token: existing_env["HF_TOKEN"] = hf_token
    if google_key: existing_env["GOOGLE_API_KEY"] = google_key
    if qdrant_url: existing_env["QDRANT_URL"] = qdrant_url
    if qdrant_key: existing_env["QDRANT_API_KEY"] = qdrant_key

    # Force AI_PROVIDER to default to 'nexora' (Local Qwen LoRA) on Colab unless overridden in secrets
    ai_provider = get_colab_secret("AI_PROVIDER") or "nexora"
    existing_env["AI_PROVIDER"] = ai_provider
    print(f"🤖 Configured AI Provider: {ai_provider}", flush=True)

    # Force absolute SQLite path to avoid directory-mismatch bugs
    existing_env["DATABASE_URL"] = "sqlite:////content/Nexora-AI/apps/backend/nexora_ai.db"

    # Write back to .env
    with open(env_path, "w") as f:
        for k, v in existing_env.items():
            f.write(f"{k}={v}\n")
    print("✅ apps/backend/.env file updated successfully!", flush=True)
except Exception as e:
    print(f"⚠️ Warning during .env file update: {e}", flush=True)

# 4. Ngrok Tunnel Setup
print("🌐 Connecting Ngrok tunnel...", flush=True)
try:
    from pyngrok import ngrok
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)
    
    # Disconnect any existing tunnels to avoid active session limits
    tunnels = ngrok.get_tunnels()
    for t in tunnels:
        ngrok.disconnect(t.public_url)
        
    tunnel = ngrok.connect("127.0.0.1:8000")
    print("==================================================")
    print(f"  NGROK PUBLIC URL: {tunnel.public_url}")
    print("==================================================")
except Exception as e:
    print(f"❌ Ngrok setup failed: {e}", flush=True)

# 5. Pre-download RAG Embedding Model
print("🤖 Pre-downloading Embedding Model...", flush=True)
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("✅ Embedding model cached successfully!", flush=True)
except Exception as e:
    print(f"⚠️ Failed to cache embedding model: {e}", flush=True)

# 6. Verify Database Tables
print("📊 Verifying SQLite Database...", flush=True)
try:
    db_path = os.path.join(BACKEND_DIR, "nexora_ai.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables in nexora_ai.db:")
        for (t,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            print(f"  • {t}: {cnt} rows")
        conn.close()
    else:
        print("ℹ️ nexora_ai.db not found, it will be automatically created on startup.")
except Exception as e:
    print(f"⚠️ Database check error: {e}")

# Setup completed successfully! Ready to run uvicorn server.
print("✅ Consolidated setup completed successfully!", flush=True)

# 7. Start Uvicorn Server using Python API (prints logs live to Colab)
print("🚀 Starting FastAPI backend server...", flush=True)
os.chdir(BACKEND_DIR)
import uvicorn
uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")


