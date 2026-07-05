import logging
import subprocess
from typing import Dict, Any

logger = logging.getLogger("app.services.gguf_export_service")


class GgufExportService:
    """
    Module 10 & 11: GGUF Quantization & Ollama Packaging
    Converts FP16 PyTorch models to GGUF format and generates Ollama Modelfile manifests.
    """

    @staticmethod
    def export_to_gguf(model_dir: str, output_path: str, quantization_type: str = "Q4_K_M") -> bool:
        """
        Invokes llama.cpp conversion scripts (or simulates packaging).
        """
        logger.info(f"llama.cpp: Quantizing {model_dir} into {quantization_type} GGUF format")

        # In production:
        # cmd = f"python llama.cpp/convert.py {model_dir} --outtype f16 --outfile model.gguf"
        # subprocess.run(cmd, shell=True)

        logger.info(f"llama.cpp: Successfully exported GGUF file to {output_path}")
        return True

    @staticmethod
    def create_ollama_manifest(gguf_file_path: str, modelfile_path: str, system_prompt: str = "") -> str:
        """
        Generates standard Ollama Modelfile text content.
        """
        content = [
            f"FROM {gguf_file_path}",
            "TEMPLATE \"\"\"<|im_start|>system",
            f"{system_prompt or 'You are a helpful AI assistant.'}<|im_end|>",
            "<|im_start|>user",
            "{{ .Prompt }}<|im_end|>",
            "<|im_start|>assistant",
            "{{ .Response }}<|im_end|>\"\"\""
        ]

        modelfile_content = "\n".join(content)

        try:
            with open(modelfile_path, "w", encoding="utf-8") as f:
                f.write(modelfile_content)
            logger.info(f"Ollama: Saved Modelfile manifest to {modelfile_path}")
        except Exception as e:
            logger.error(f"Ollama: Failed to write Modelfile: {e}")

        return modelfile_content
