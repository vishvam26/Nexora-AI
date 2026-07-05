import logging
from typing import Dict, Any

logger = logging.getLogger("app.services.gpu_detection_service")


class GPUDetectionService:
    """
    Module 8: GPU Detection
    Detects CUDA devices, VRAM size, compute capabilities, and recommends training hyperparameters.
    """

    @staticmethod
    def detect_gpu_resources() -> Dict[str, Any]:
        """
        Calculates active system GPU profiles.
        """
        # Fallback values for mock profiles when PyTorch/CUDA is unavailable
        cuda_available = False
        gpu_name = "NVIDIA GeForce RTX 4090 (Mock)"
        vram_gb = 24.0
        compute_capability = "8.9"
        supports_bf16 = True

        try:
            import torch
            if torch.cuda.is_available():
                cuda_available = True
                gpu_name = torch.cuda.get_device_name(0)
                # Convert bytes to GB
                vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
                major, minor = torch.cuda.get_device_capability(0)
                compute_capability = f"{major}.{minor}"
                supports_bf16 = torch.cuda.is_bf16_supported()
        except ImportError:
            logger.info("PyTorch not installed. Using baseline hardware profile.")

        # Recommendations based on VRAM size
        recommended_batch = 4
        recommended_seq = 2048

        if vram_gb >= 24.0:
            recommended_batch = 16
            recommended_seq = 4096
        elif vram_gb >= 16.0:
            recommended_batch = 8
            recommended_seq = 2048

        return {
            "cuda_available": cuda_available,
            "gpu_name": gpu_name,
            "vram_gb": vram_gb,
            "compute_capability": compute_capability,
            "supports_bf16": supports_bf16,
            "recommendations": {
                "batch_size": recommended_batch,
                "sequence_length": recommended_seq,
                "rank": 16,
                "alpha": 32
            }
        }
