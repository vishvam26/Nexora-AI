import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings


def _get_fernet() -> Fernet:
    """
    Derives a 32-byte URL-safe base64-encoded key from settings.SECRET_KEY using SHA-256.
    """
    secret = settings.SECRET_KEY or "NEXORA_SECURE_FALLBACK_KEY_32BYTES_LONG"
    key_hash = hashlib.sha256(secret.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(fernet_key)


def encrypt_key(plain_text: str) -> str:
    """
    Encrypts external API key string to a secure AES cipher text.
    """
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode()).decode()


def decrypt_key(cipher_text: str) -> str:
    """
    Decrypts external API key secure AES cipher text back to plain text.
    """
    if not cipher_text:
        return ""
    f = _get_fernet()
    return f.decrypt(cipher_text.encode()).decode()
