import os
import sys
import shutil

# Exclude directories that are auto-generated, dependency collections, or configuration metadata
EXCLUDED_DIRS = {
    "node_modules", ".next", "__pycache__", "venv", ".venv", ".git", ".github", ".agents",
    "build", "dist", ".gemini", "out", ".cache", "alembic", "scratch"
}

# Exclude specific files that are config files but not directly imported in code
EXCLUDED_FILES = {
    "package.json", "package-lock.json", "tsconfig.json", "tailwind.config.js",
    "tailwind.config.ts", "postcss.config.js", "next.config.js", "next.config.ts",
    "requirements.txt", "mypy.ini", ".flake8", ".gitignore", "cleanup_agent.py",
    "README.md", "eslint.config.mjs", "next-env.d.ts", "layout.tsx", "page.tsx",
    "route.ts", "global.css", "globals.css"
}

# Supported extensions to check for references
CHECK_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".json", ".csv"}


def get_all_project_files(root_dir):
    """
    Recursively fetches all files.
    Returns:
      - audited_files: Files that we want to check if they are unused.
      - scanner_files: All files (including pages/layouts) that we must read to find references.
    """
    audited_files = []
    scanner_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prevent searching inside virtual environments, cache, or migrations
        path_parts = dirpath.replace("\\", "/").split("/")
        if any(part in EXCLUDED_DIRS or "venv" in part or ".cache" in part or "alembic" in part for part in path_parts):
            continue
            
        # Exclude directories in-place to prevent walking down them
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and "venv" not in d and "alembic" not in d]
        
        for file in filenames:
            ext = os.path.splitext(file)[1].lower()
            if ext in CHECK_EXTENSIONS:
                full_path = os.path.join(dirpath, file)
                scanner_files.append(full_path)
                
                # Only audit files that are not in the excluded configurations list
                if file not in EXCLUDED_FILES:
                    audited_files.append(full_path)
                    
    return audited_files, scanner_files


def analyze_file_references(root_dir, audited_files, scanner_files):
    """
    Scans the contents of all scanner_files to check if they reference audited_files.
    """
    ref_counts = {f: 0 for f in audited_files}
    
    # Store clean filenames and module basenames for matching references
    file_metadata = {}
    for f in audited_files:
        basename = os.path.basename(f)
        name_without_ext, ext = os.path.splitext(basename)
        file_metadata[f] = {
            "basename": basename,
            "name_without_ext": name_without_ext,
            "ext": ext
        }

    print("\n[+] Analyzing codebase references. Reading all files line by line...")
    total_loc = 0
    
    # Scan through every scanner file to count references in audited files
    for scanner_file in scanner_files:
        try:
            with open(scanner_file, 'r', encoding='utf-8', errors='ignore') as sf:
                content = sf.read()
                total_loc += len(content.splitlines())
                
                # Check references for each target file
                for target_file, meta in file_metadata.items():
                    if scanner_file == target_file:
                        continue  # Do not count self-references
                    
                    basename = meta["basename"]
                    name_no_ext = meta["name_without_ext"]
                    
                    # Direct check of module name/filename inside the import path
                    if name_no_ext in content:
                        ref_counts[target_file] += 1
        except Exception as e:
            print(f"[!] Error reading file {scanner_file}: {e}")

    return ref_counts, total_loc


def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"=== Nexora AI CleanUp & Review Agent ===")
    print(f"[+] Root Directory: {root_dir}")
    
    # 1. Fetch files
    audited_files, scanner_files = get_all_project_files(root_dir)
    print(f"[+] Found {len(scanner_files)} source files in project.")
    
    # 2. Analyze references
    ref_counts, total_loc = analyze_file_references(root_dir, audited_files, scanner_files)
    
    # 3. Filter unused files
    unused_files = [f for f, count in ref_counts.items() if count == 0]
    
    # 4. Display Report
    print(f"\n=========================================")
    print(f"            PROJECT AUDIT REPORT         ")
    print(f"=========================================")
    print(f"  - Total Lines of Code (LOC): {total_loc:,}")
    print(f"  - Total Audited Files:       {len(audited_files)}")
    print(f"  - Unused / Orphan Files:     {len(unused_files)}")
    print(f"=========================================\n")
    
    if not unused_files:
        print("[✔] Excellent! No unused or orphan files detected in the project.")
        sys.exit(0)
        
    print("[⚠] The following files are NOT referenced or imported anywhere:")
    for idx, f in enumerate(unused_files, 1):
        rel_path = os.path.relpath(f, root_dir)
        print(f"  {idx}. {rel_path}")
        
    print("\n[!] CAUTION: Dynamic paths, API route entrypoints, or root layouts may not trigger references.")
    print("Please review the list above carefully before deleting.")
    
    # 5. Interactive Deletion prompt
    confirm = input("\n[?] Do you want to delete these unused files? (y/N): ").strip().lower()
    if confirm == 'y':
        deleted_count = 0
        for f in unused_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    rel_path = os.path.relpath(f, root_dir)
                    print(f"[-] Deleted: {rel_path}")
                    deleted_count += 1
            except Exception as e:
                print(f"[!] Failed to delete {f}: {e}")
        print(f"\n[✔] Successfully deleted {deleted_count} unused files.")
    else:
        print("[*] Cleanup cancelled. No files were deleted.")

if __name__ == "__main__":
    main()
