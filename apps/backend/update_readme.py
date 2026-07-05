import sys
from huggingface_hub import HfApi

# Parse .env manually to get the token
env_vars = {}
try:
    with open(".env", "r") as f:
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
    print("❌ ERROR: Please make sure your new Write token is set in .env line 36.")
    sys.exit(1)
if not model:
    print("❌ ERROR: NEXORA_MODEL_ID not found in .env")
    sys.exit(1)

# Correct metadata format for Hugging Face
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

# Save README.md locally first
try:
    with open("temp_readme.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
except Exception as e:
    print(f"Error writing local temp file: {e}")
    sys.exit(1)

print(f"Uploading README.md with conversational tags to {model}...")
api = HfApi()
try:
    api.upload_file(
        path_or_fileobj="temp_readme.md",
        path_in_repo="README.md",
        repo_id=model,
        token=token
    )
    print("\n🎉 SUCCESS! README.md uploaded. Hugging Face is now indexing your model as a chat-capable model!")
except Exception as e:
    print(f"\n❌ Upload failed: {e}")
