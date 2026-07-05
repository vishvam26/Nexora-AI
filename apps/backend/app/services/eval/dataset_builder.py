"""
DatasetBuilder — Volume 4 Continuous Learning Auto Dataset Builder

Features:
  - Hash Deduplication (MD5 checking of queries to prevent redundant training samples).
  - Conversational JSONL compiler matching QLoRA datasets specifications.
  - Custom metadata encapsulation wrapper.
  - CSV format exporter.
"""
import os
import json
import hashlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger("app.services.eval.dataset_builder")

DATASET_DIR = os.path.join("storage", "datasets")
os.makedirs(DATASET_DIR, exist_ok=True)

JSONL_PATH = os.path.join(DATASET_DIR, "tuning_queue.jsonl")


class DatasetBuilder:
    """
    Saves and exports approved feedback records to training datasets.
    """

    @classmethod
    def calculate_hash(cls, query: str, response: str) -> str:
        """
        Generates lookup MD5 key to prevent duplicate training inputs.
        """
        payload = f"{query.strip()}|||{response.strip()}"
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    @classmethod
    def append_to_jsonl(cls, record_id: int, query: str, response: str, context_chunks: List[str], metadata: Dict[str, Any]) -> bool:
        """
        Appends a deduplicated conversational line wrapper to the training dataset.
        """
        # Deduplication check: verify if hash already exists in JSONL
        q_hash = cls.calculate_hash(query, response)
        
        if os.path.exists(JSONL_PATH):
            try:
                with open(JSONL_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        parsed_line = json.loads(line)
                        if parsed_line.get("query_hash") == q_hash:
                            logger.info(f"[DatasetBuilder] Duplicate skipped: {q_hash}")
                            return False # Duplicate found
            except Exception as e:
                logger.error(f"[DatasetBuilder] JSONL read fail: {e}")

        # Assemble Conversational Message payload
        # Includes prompt system guidelines + context embeddings grounding injection
        context_str = "\n".join(context_chunks)
        system_content = (
            "You are Nexora, a professional enterprise assistant. "
            "Use only the provided context to answer questions accurately without hallucinating."
        )
        user_content = f"Context:\n{context_str}\n\nQuestion: {query}"

        conversational_payload = {
            "id": f"sample_{record_id}",
            "query_hash": q_hash,
            "model_version": metadata.get("model_version", "nexora-v1"),
            "dataset_version": metadata.get("dataset_version", "ds-v1"),
            "rag_pipeline_version": metadata.get("rag_pipeline_version", "rag-v2.1"),
            "confidence": metadata.get("confidence", 0.8),
            "hallucination": metadata.get("hallucination", 0.2),
            "domain_tag": metadata.get("domain_tag", "General"),
            "root_cause": metadata.get("root_cause", "None"),
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": response}
            ]
        }

        try:
            with open(JSONL_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(conversational_payload) + "\n")
            logger.info(f"[DatasetBuilder] Added record ID {record_id} to JSONL queue.")
            return True
        except Exception as e:
            logger.error(f"[DatasetBuilder] JSONL write failed: {e}")
            return False

    @classmethod
    def compile_csv_bytes(cls, records: List[Dict[str, Any]]) -> bytes:
        """
        Compiles list of database records into a CSV payload byte buffer.
        """
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)
        
        # CSV Headers
        writer.writerow([
            "id", "query", "response", "domain_tag", "root_cause",
            "faithfulness", "hallucination", "confidence", "priority",
            "model_version", "rag_pipeline_version"
        ])

        for r in records:
            writer.writerow([
                r.get("id"),
                r.get("query"),
                r.get("response"),
                r.get("domain_tag"),
                r.get("root_cause"),
                r.get("faithfulness"),
                r.get("hallucination"),
                r.get("confidence"),
                r.get("priority"),
                r.get("model_version"),
                r.get("rag_pipeline_version")
            ])

        return output.getvalue().encode("utf-8")
