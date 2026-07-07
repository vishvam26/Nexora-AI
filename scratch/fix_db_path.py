import os

# Detect paths
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
env_path = os.path.join(backend_dir, ".env")

print("=== SQLite Absolute Path Fixer ===")

# Compute absolute DB path
if os.name == "nt":
    # Windows absolute sqlite path
    db_file = os.path.join(backend_dir, "nexora_ai.db").replace("\\", "/")
    absolute_db_url = f"sqlite:///{db_file}"
else:
    # Linux (Colab) absolute sqlite path
    absolute_db_url = "sqlite:////content/Nexora-AI/apps/backend/nexora_ai.db"

print(f"Computed absolute DATABASE_URL: {absolute_db_url}")

# Read and update .env
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("DATABASE_URL="):
            new_lines.append(f"DATABASE_URL={absolute_db_url}\n")
            updated = True
        else:
            new_lines.append(line)
            
    if not updated:
        new_lines.append(f"\nDATABASE_URL={absolute_db_url}\n")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Successfully updated .env with absolute SQLite database URL! ✅")
else:
    print(".env file not found inside apps/backend/ ❌")
