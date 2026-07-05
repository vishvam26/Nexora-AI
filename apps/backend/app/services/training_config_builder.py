import logging
from typing import Dict, Any

logger = logging.getLogger("app.services.training_config_builder")


class TrainingConfigBuilder:
    """
    Module 6: Training Configuration Builder
    Generates optimizer, batch, and epoch learning parameters.
    """

    @staticmethod
    def build_config(
        epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 10,
        preset: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Calculates training variables with preset configurations.
        """
        config = {
            "num_train_epochs": epochs,
            "per_device_train_batch_size": batch_size,
            "learning_rate": learning_rate,
            "warmup_steps": warmup_steps,
            "weight_decay": 0.01,
            "optim": "adamw_8bit",
            "lr_scheduler_type": "cosine",
            "seed": 42
        }

        # Handle Preset adjustments
        if preset.lower() == "fast":
            config["learning_rate"] = 3e-4
            config["num_train_epochs"] = 1
        elif preset.lower() == "high quality":
            config["learning_rate"] = 1e-4
            config["weight_decay"] = 0.05

        return config
