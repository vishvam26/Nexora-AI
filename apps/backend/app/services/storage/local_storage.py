import os
import logging
from app.services.storage.storage_interface import StorageInterface

logger = logging.getLogger("app.services.storage.local_storage")


class LocalStorage(StorageInterface):
    """
    Local filesystem storage provider for saving and retrieving uploaded workspace files.
    """

    def __init__(self, base_upload_dir: str = "storage"):
        self.base_dir = os.path.abspath(base_upload_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, content: bytes, filename: str, subfolder: str) -> str:
        """
        Saves file bytes inside local directory context, returning the relative filepath.
        """
        # Clean folder context
        dest_dir = os.path.join(self.base_dir, subfolder)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, filename)
        with open(dest_path, "wb") as f:
            f.write(content)

        # Return relative reference to base dir
        return os.path.relpath(dest_path, self.base_dir)

    def read_file(self, path: str) -> bytes:
        """
        Reads files from storage.
        """
        full_path = os.path.join(self.base_dir, path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")

        with open(full_path, "rb") as f:
            return f.read()

    def delete_file(self, path: str) -> None:
        """
        Deletes local file.
        """
        full_path = os.path.join(self.base_dir, path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Deleted local file from storage: {path}")
