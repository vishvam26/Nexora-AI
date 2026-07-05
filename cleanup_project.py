import os
import shutil

def cleanup():
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"=== NEXORA AI PROJECT CLEANUP ===")
    print(f"Project directory: {project_root}\n")

    # 1. Paths to remove recursively (folders)
    folders_to_remove = [
        os.path.join(project_root, ".cache"),  # Hugging Face model cache (approx 9GB!)
        os.path.join(project_root, "apps", "backend", "__pycache__"),
        os.path.join(project_root, "apps", "backend", "app", "__pycache__"),
        os.path.join(project_root, "apps", "backend", "app", "api", "__pycache__"),
        os.path.join(project_root, "apps", "backend", "app", "api", "v1", "__pycache__"),
    ]
    
    # Safely scan and add all __pycache__ directories
    for root, dirs, files in os.walk(project_root):
        if "__pycache__" in dirs:
            folders_to_remove.append(os.path.join(root, "__pycache__"))

    # 2. Individual files to remove
    files_to_remove = [
        os.path.join(project_root, "apps", "backend", "temp_readme.md"),
        os.path.join(project_root, "apps", "backend", "nexora_ai.db"),  # Local SQLite database
        os.path.join(project_root, "apps", "backend", "update_readme.py"),
    ]

    # Perform folder cleanup
    freed_space_folders = 0
    for folder in set(folders_to_remove):
        if folder and os.path.exists(folder):
            try:
                # Estimate folder size for logging
                folder_size = 0
                for dirpath, dirnames, filenames in os.walk(folder):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            folder_size += os.path.getsize(fp)
                
                shutil.rmtree(folder)
                print(f"✅ Deleted folder: {os.path.relpath(folder, project_root)} (~{folder_size / (1024*1024):.2f} MB)")
            except Exception as e:
                print(f"❌ Failed to delete folder {os.path.relpath(folder, project_root)}: {e}")

    # Perform file cleanup
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                file_size = os.path.getsize(file)
                os.remove(file)
                print(f"✅ Deleted file: {os.path.relpath(file, project_root)} (~{file_size / 1024:.2f} KB)")
            except Exception as e:
                print(f"❌ Failed to delete file {os.path.relpath(file, project_root)}: {e}")

    print("\n🎉 CLEANUP COMPLETED SUCCESSFULLY! Your disk space has been reclaimed.")

if __name__ == "__main__":
    cleanup()
