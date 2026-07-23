import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings


def _get_aes_key() -> bytes:
    """
    Derives a 32-byte key from settings.SECRET_KEY using SHA-256.
    Matches AES-256 keysize requirement.
    """
    secret = settings.SECRET_KEY or "NEXORA_SECURE_FALLBACK_KEY_32BYTES_LONG"
    return hashlib.sha256(secret.encode()).digest()


def encrypt_key(plain_text: str) -> str:
    """
    Encrypts plain text string using AES-256-GCM.
    Returns base64 encoded string combining nonce + ciphertext.
    """
    if not plain_text:
        return ""
    
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 12 bytes nonce is standard for GCM
    
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')


def decrypt_key(cipher_text: str) -> str:
    """
    Decrypts base64 encoded nonce + ciphertext back to plain text using AES-256-GCM.
    Falls back to Fernet for backward compatibility with existing legacy secrets.
    """
    if not cipher_text:
        return ""
    
    # 1. Try AES-256-GCM first
    try:
        key = _get_aes_key()
        aesgcm = AESGCM(key)
        
        raw_data = base64.b64decode(cipher_text.encode('utf-8'))
        if len(raw_data) >= 12:
            nonce = raw_data[:12]
            ciphertext = raw_data[12:]
            return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    except Exception:
        pass

    # 2. Fallback to Fernet for legacy keys
    try:
        from cryptography.fernet import Fernet
        secret = settings.SECRET_KEY or "NEXORA_SECURE_FALLBACK_KEY_32BYTES_LONG"
        key_hash = hashlib.sha256(secret.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_hash)
        f = Fernet(fernet_key)
        return f.decrypt(cipher_text.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt key with all providers: {e}")
