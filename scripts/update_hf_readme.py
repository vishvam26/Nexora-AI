"""
update_hf_readme.py — HuggingFace Model README Uploader

Upload a README.md to a HuggingFace model repo to tag it as
a conversational model (enables chat UI in HuggingFace).

Usage:
    cd scripts/
    python update_hf_readme.py

Requires:
    - HF_TOKEN in apps/backend/.env
    - NEXORA_MODEL_ID in apps/backend/.env
"""
import sys
import os
from huggingface_hub import HfApi

# Parse .env manually to get the token
env_path = os.path.join(os.path.dirname(__file__), "..", "apps", "backend", ".env")
env_vars = {}
try:
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
except Exception as e:
    print(f"Error reading .env: {e}")
    sys.exit(1)

token = env_vars.get("HF_TOKEN")
model = env_vars.get("NEXORA_MODEL_ID")

if not token or "hf_" not in token:
    print("ERROR: Please set HF_TOKEN in apps/backend/.env")
    sys.exit(1)
if not model:
    print("ERROR: NEXORA_MODEL_ID not found in apps/backend/.env")
    sys.exit(1)

readme_content = """---
license: apache-2.0
tags:
- conversational
- text-generation
pipeline_tag: text-generation
---

# Nexora Qwen3.5 4B Merged
Custom conversational model merged for Nexora AI.
"""

temp_path = os.path.join(os.path.dirname(__file__), "temp_readme.md")
with open(temp_path, "w", encoding="utf-8") as f:
    f.write(readme_content)

print(f"Uploading README.md to {model}...")
api = HfApi()
try:
    api.upload_file(
        path_or_fileobj=temp_path,
        path_in_repo="README.md",
        repo_id=model,
        token=token
    )
    print("SUCCESS! README.md uploaded.")
except Exception as e:
    print(f"Upload failed: {e}")
finally:
    if os.path.exists(temp_path):
        os.remove(temp_path)
