"""
Encryption utilities for LLM API keys.

Uses AES-GCM encryption with a server-side KMS secret.
Keys are encrypted at rest and only decrypted in memory for outbound calls.
"""

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


def _get_key() -> bytes:
    """Derive a 256-bit AES key from the KMS secret."""
    kms_secret = getattr(settings, "KMS_SECRET", "")
    if not kms_secret:
        raise ValueError("KMS_SECRET not configured")
    # Use SHA-256 to derive a consistent 32-byte key from the secret
    return hashlib.sha256(kms_secret.encode()).digest()


def encrypt_api_key(plaintext: str) -> bytes:
    """
    Encrypt an API key using AES-GCM.

    Args:
        plaintext: The API key to encrypt

    Returns:
        bytes: nonce (12 bytes) + ciphertext + tag
    """
    if not plaintext:
        raise ValueError("Cannot encrypt empty API key")

    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce + ciphertext


def decrypt_api_key(encrypted_data: bytes) -> str:
    """
    Decrypt an API key using AES-GCM.

    Args:
        encrypted_data: nonce (12 bytes) + ciphertext + tag

    Returns:
        str: The decrypted API key
    """
    if not encrypted_data or len(encrypted_data) < 13:
        raise ValueError("Invalid encrypted data")

    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()


def encrypt_api_key_b64(plaintext: str) -> str:
    """
    Encrypt an API key and return as base64 string.

    Useful for serialization and transport.
    """
    encrypted = encrypt_api_key(plaintext)
    return base64.b64encode(encrypted).decode()


def decrypt_api_key_b64(encrypted_b64: str) -> str:
    """
    Decrypt a base64-encoded encrypted API key.
    """
    encrypted = base64.b64decode(encrypted_b64)
    return decrypt_api_key(encrypted)
