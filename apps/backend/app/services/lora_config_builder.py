import logging
from typing import Dict, Any

logger = logging.getLogger("app.services.lora_config_builder")


class LoraConfigBuilder:
    """
    Module 5: QLoRA Configuration Builder
    Builds target ranks and scaling factor adapters.
    """

    @staticmethod
    def build_config(
        r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: list = None
    ) -> Dict[str, Any]:
        """
        Builds PEFT LoRA dictionary parameters.
        """
        if target_modules is None:
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

        # Basic limits checks
        if r <= 0 or r > 512:
            raise ValueError("LoRA Rank must be within range (1 - 512)")
        if lora_alpha <= 0:
            raise ValueError("LoRA Alpha must be greater than zero")

        return {
            "r": r,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "target_modules": target_modules,
            "bias": "none",
            "task_type": "CAUSAL_LM"
        }
