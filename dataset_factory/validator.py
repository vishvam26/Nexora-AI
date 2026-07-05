import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

class DatasetValidator:
    """
    Automated validator for Nexora AI JSONL datasets.
    Checks:
      - UTF-8 encoding
      - Valid JSON on each line
      - Presence and schema of 'messages' array
      - Valid roles (user, assistant, system)
      - Non-empty content
      - Duplicate conversation checks
    """

    def __init__(self, datasets_dir: Path):
        self.datasets_dir = datasets_dir

    def validate_file(self, filename: str) -> Tuple[bool, List[str]]:
        filepath = self.datasets_dir / filename
        errors = []
        
        if not filepath.exists():
            errors.append(f"File {filename} does not exist.")
            return False, errors

        seen_conversations = set()
        line_count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, 1):
                    line_count += 1
                    line = line.strip()
                    if not line:
                        errors.append(f"Line {line_idx}: Empty line found.")
                        continue

                    # 1. JSON Valid check
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_idx}: Invalid JSON syntax. Details: {e}")
                        continue

                    # 2. Schema structure check
                    if "messages" not in data:
                        errors.append(f"Line {line_idx}: Missing 'messages' key.")
                        continue

                    messages = data["messages"]
                    if not isinstance(messages, list) or len(messages) == 0:
                        errors.append(f"Line {line_idx}: 'messages' must be a non-empty list.")
                        continue

                    # 3. Message validation
                    for msg_idx, msg in enumerate(messages):
                        if not isinstance(msg, dict):
                            errors.append(f"Line {line_idx}, message {msg_idx}: Message is not a JSON object.")
                            continue
                        
                        if "role" not in msg or "content" not in msg:
                            errors.append(f"Line {line_idx}, message {msg_idx}: Message missing 'role' or 'content'.")
                            continue

                        role = msg["role"]
                        content = msg["content"]

                        if role not in ["user", "assistant", "system"]:
                            errors.append(f"Line {line_idx}, message {msg_idx}: Invalid role '{role}'.")

                        if not isinstance(content, str) or not content.strip():
                            errors.append(f"Line {line_idx}, message {msg_idx}: Content is empty or not a string.")

                    # 4. Duplicate checks (hash of prompt content)
                    try:
                        # Find the first user message as unique identifier for duplicates
                        user_msgs = [m["content"] for m in messages if m["role"] == "user"]
                        if user_msgs:
                            prompt_hash = hash(user_msgs[0].strip().lower())
                            if prompt_hash in seen_conversations:
                                errors.append(f"Line {line_idx}: Duplicate conversation detected.")
                            seen_conversations.add(prompt_hash)
                    except Exception as ex:
                        errors.append(f"Line {line_idx}: Error during hashing check: {ex}")

        except UnicodeDecodeError:
            errors.append("File contains non-UTF-8 characters or encoding error.")

        if line_count == 0:
            errors.append("File is empty (contains 0 lines).")

        return len(errors) == 0, errors

    def validate_all(self, expected_files: List[str]) -> Dict[str, Any]:
        """Validates all files in the expected_files list."""
        report = {}
        all_ok = True
        
        for name in expected_files:
            ok, errors = self.validate_file(name)
            report[name] = {
                "valid": ok,
                "errors": errors[:10]  # limit to top 10 errors for brevity
            }
            if not ok:
                all_ok = False

        return {
            "all_valid": all_ok,
            "report": report
        }
