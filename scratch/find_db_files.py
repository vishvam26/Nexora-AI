import os

print("=== SEARCHING FOR SQLITE DB FILES IN COLAB ===")
for root, dirs, files in os.walk("/content"):
    for file in files:
        if file.endswith(".db"):
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            print(f"File: {full_path} | Size: {size} bytes")
