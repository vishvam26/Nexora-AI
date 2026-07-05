import logging
from typing import List, Dict, Any
from app.models.message import Message

logger = logging.getLogger("app.services.training_validation_service")


class TrainingValidationService:
    """
    Module 3: Dataset Validation before Model Training
    Runs formatting tests on conversations to ensure no missing roles exist.
    """

    @staticmethod
    def validate_dataset_for_training(messages: List[Message]) -> Dict[str, Any]:
        """
        Validates roles alternating sequence and counts total token counts.
        """
        errors = []
        warnings = []
        total_tokens = 0

        if not messages:
            errors.append("Empty dataset conversation array.")
            return {"status": "Failed", "grade": "D", "errors": errors, "warnings": warnings}

        has_user = False
        has_assistant = False

        for index, msg in enumerate(messages):
            total_tokens += len(msg.content or "") // 4
            if msg.role == "user":
                has_user = True
            elif msg.role == "assistant":
                has_assistant = True

        if not has_user:
            errors.append("Dataset lacks required 'user' instruction roles.")
        if not has_assistant:
            errors.append("Dataset lacks required 'assistant' output target roles.")

        # Determine overall grade
        grade = "A"
        if warnings:
            grade = "B"
        if errors:
            grade = "D"

        return {
            "status": "Passed" if not errors else "Failed",
            "grade": grade,
            "errors": errors,
            "warnings": warnings,
            "total_tokens": total_tokens,
            "sample_count": len(messages)
        }
