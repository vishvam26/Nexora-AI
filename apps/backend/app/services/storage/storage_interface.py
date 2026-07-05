from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """
    Interface for Workspace document storage (Local, S3, Azure, GCS, MinIO).
    """

    @abstractmethod
    def save_file(self, content: bytes, filename: str, subfolder: str) -> str:
        """
        Saves file bytes and returns the unique storage path reference string.
        """
        pass

    @abstractmethod
    def read_file(self, path: str) -> bytes:
        """
        Reads file bytes from storage.
        """
        pass

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """
        Deletes file from storage.
        """
        pass
