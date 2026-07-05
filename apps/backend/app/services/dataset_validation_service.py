import logging
from typing import List, Dict, Any
from app.models.message import Message

logger = logging.getLogger("app.services.dataset_validation_service")


class DatasetValidationService:
    """
    Module 18: Dataset Validation
    Runs sanity checks before exporting data to ensure no formatting errors exist.
    """

    @staticmethod
    def validate_messages(messages: List[Message]) -> Dict[str, Any]:
        """
        Validates roles, order, and format completeness.
        """
        errors = []
        warnings = []

        if not messages:
            errors.append("No messages found inside conversation dataset")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # Check role order (e.g. should ideally alternate user / assistant)
        last_role = None
        for index, m in enumerate(messages):
            if not m.content or not m.content.strip():
                errors.append(f"Empty content detected on message index {index}")

            # Warning if system role appears in the middle
            if m.role == "system" and index > 0:
                warnings.append("System role message detected in the middle of conversation list")

            if m.role == last_role and m.role != "system":
                warnings.append(f"Consecutive messages with same role: {m.role} on index {index}")

            last_role = m.role

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_messages": len(messages)
        }
