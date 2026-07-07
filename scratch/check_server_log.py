import os

log_path = "/content/Nexora-AI/apps/backend/backend.log"
print("=== SERVER LOG TRACE ===")
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"Total log lines: {len(lines)}")
    print("\n--- Last 50 Lines of backend.log ---")
    for line in lines[-50:]:
        print(line.strip())
else:
    print(f"backend.log NOT found at {log_path} ❌")
