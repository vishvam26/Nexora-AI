import os

log_path = "/content/Nexora-AI/backend.log"
print("=== NEW SERVER LOG TRACE ===")
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"Total log lines: {len(lines)}")
    print("\n--- Last 50 Lines of backend.log ---")
    for line in lines[-50:]:
        print(line.strip())
else:
    # Try looking in the apps/backend/backend.log as well just in case
    alt_log_path = "/content/Nexora-AI/apps/backend/backend.log"
    print(f"backend.log NOT found at {log_path} ❌. Checking alt log path: {alt_log_path}")
    if os.path.exists(alt_log_path):
        with open(alt_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"Total log lines in alt log: {len(lines)}")
        print("\n--- Last 50 Lines of alt backend.log ---")
        for line in lines[-50:]:
            print(line.strip())
    else:
        print("Alt backend.log NOT found either ❌")
