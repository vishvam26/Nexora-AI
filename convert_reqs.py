import os

def convert_file(path):
    if not os.path.exists(path):
        print(f"File {path} does not exist.")
        return
    
    # Try reading as UTF-16
    try:
        with open(path, "r", encoding="utf-16") as f:
            content = f.read()
        print(f"Successfully read {path} as UTF-16")
    except Exception as e:
        # Fallback to UTF-8
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"Successfully read {path} as UTF-8")
        except Exception as e2:
            print(f"Could not read {path}: {e} / {e2}")
            return
            
    # Add alembic if it's requirements.txt
    if "requirements.txt" in path and "alembic" not in content.lower():
        # Ensure we add it cleanly
        if not content.endswith("\n"):
            content += "\n"
        content += "alembic==1.13.1\n"
        print(f"Added alembic to {path}")
        
    # Write back as UTF-8
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully wrote {path} as UTF-8")

if __name__ == "__main__":
    convert_file("requirements.txt")
    convert_file("apps/backend/requirements.txt")
