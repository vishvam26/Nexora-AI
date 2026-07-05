import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("app.services.real_dataset_loader")


class RealDatasetLoader:
    """
    Module 3: Real Dataset Loader
    Parses and loads multiple dataset file layouts (JSONL, ShareGPT, OpenAI Messages)
    into structured list arrays suitable for tokenization processing.
    """

    @staticmethod
    def load_dataset(file_path: str) -> List[Dict[str, Any]]:
        """
        Detects file layout and extracts message roles.
        """
        parsed = []
        try:
            if file_path.endswith(".jsonl"):
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            parsed.append(json.loads(line))
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    parsed = json.load(f)
        except Exception as e:
            logger.error(f"DatasetLoader: Failed to parse dataset file {file_path}: {e}")
            raise ValueError(f"Failed to read dataset file: {e}")

        # Normalise list formats to standard conversation segments
        normalized = []
        for sample in parsed:
            # Check ShareGPT format (conversations block)
            if "conversations" in sample:
                convs = []
                for turn in sample["conversations"]:
                    role_map = {"human": "user", "gpt": "assistant", "system": "system"}
                    convs.append({
                        "role": role_map.get(turn.get("from"), "user"),
                        "content": turn.get("value", "")
                    })
                normalized.append(convs)

            # Check OpenAI chat format (messages block)
            elif "messages" in sample:
                normalized.append([
                    {"role": m.get("role"), "content": m.get("content", "")}
                    for m in sample["messages"]
                ])

            # Check Alpaca style layout
            elif "instruction" in sample:
                normalized.append([
                    {"role": "user", "content": f"{sample.get('instruction')}\n{sample.get('input', '')}".strip()},
                    {"role": "assistant", "content": sample.get("output", "")}
                ])

        logger.info(f"DatasetLoader: Loaded and normalized {len(normalized)} conversation lines from {file_path}")
        return normalized
