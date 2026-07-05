import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("app.services.huggingface_service")


class HuggingFaceService:
    """
    Module 1: Hugging Face Hub Integration
    Handles authentication, repository creations, metadata cards and pushing compiled adapters/GGUF models.
    """

    @staticmethod
    def login(token: str) -> bool:
        """Authenticates token against huggingface hub API."""
        if not token or len(token) < 20:
            return False
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
            user = api.whoami()
            logger.info(f"HuggingFace: Successfully authenticated user: {user.get('username')}")
            return True
        except Exception as e:
            logger.warning(f"HuggingFace: Hub login failed: {e}")
            return False

    @staticmethod
    def create_hub_repository(token: str, repo_id: str, private: bool = True) -> str:
        """Creates target model repository on HF Hub."""
        try:
            from huggingface_hub import create_repo
            url = create_repo(repo_id=repo_id, token=token, private=private, exist_ok=True)
            return url.repo_id
        except Exception as e:
            logger.error(f"HuggingFace: Failed to create repository {repo_id}: {e}")
            raise RuntimeError(f"HuggingFace Repository creation failed: {e}")

    @staticmethod
    def push_to_hub(token: str, repo_id: str, folder_path: str, commit_message: str = "Upload Nexora fine-tuned adapter") -> bool:
        """Pushes folder binaries to huggingface model hub."""
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=token)
            api.upload_folder(
                folder_path=folder_path,
                repo_id=repo_id,
                commit_message=commit_message
            )
            return True
        except Exception as e:
            logger.error(f"HuggingFace: Failed to upload folder to {repo_id}: {e}")
            return False
