"""
Tests for LLM API key encryption utilities.
"""

import pytest
from django.test import override_settings

from apps.llm_config.encryption import (
    decrypt_api_key,
    decrypt_api_key_b64,
    encrypt_api_key,
    encrypt_api_key_b64,
)


class TestEncryption:
    """Tests for AES-GCM encryption utilities."""

    @override_settings(KMS_SECRET="test-kms-secret-key")
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are reversible."""
        original_key = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(original_key)
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original_key

    @override_settings(KMS_SECRET="test-kms-secret-key")
    def test_encrypt_produces_different_output(self):
        """Test that same input produces different ciphertext (due to random nonce)."""
        api_key = "sk-test-api-key"
        encrypted1 = encrypt_api_key(api_key)
        encrypted2 = encrypt_api_key(api_key)
        # Different nonces mean different ciphertext
        assert encrypted1 != encrypted2
        # But both decrypt to same value
        assert decrypt_api_key(encrypted1) == api_key
        assert decrypt_api_key(encrypted2) == api_key

    @override_settings(KMS_SECRET="test-kms-secret-key")
    def test_encrypt_empty_raises_error(self):
        """Test that encrypting empty string raises error."""
        with pytest.raises(ValueError, match="Cannot encrypt empty"):
            encrypt_api_key("")

    @override_settings(KMS_SECRET="test-kms-secret-key")
    def test_decrypt_invalid_data_raises_error(self):
        """Test that decrypting invalid data raises error."""
        with pytest.raises(ValueError, match="Invalid encrypted data"):
            decrypt_api_key(b"")

        with pytest.raises(ValueError, match="Invalid encrypted data"):
            decrypt_api_key(b"short")

    @override_settings(KMS_SECRET="test-kms-secret-key")
    def test_base64_roundtrip(self):
        """Test base64 encryption/decryption helpers."""
        api_key = "sk-openai-test-key"
        encrypted_b64 = encrypt_api_key_b64(api_key)
        # Should be valid base64 string
        assert isinstance(encrypted_b64, str)
        decrypted = decrypt_api_key_b64(encrypted_b64)
        assert decrypted == api_key

    @override_settings(KMS_SECRET="")
    def test_encrypt_without_kms_secret_raises_error(self):
        """Test that encryption fails without KMS_SECRET configured."""
        with pytest.raises(ValueError, match="KMS_SECRET not configured"):
            encrypt_api_key("test-key")

    @override_settings(KMS_SECRET="different-secret")
    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails."""
        # Encrypt with one key
        from django.test import override_settings as os_inner

        with os_inner(KMS_SECRET="original-secret"):
            encrypted = encrypt_api_key("test-key")

        # Try to decrypt with different key (current setting)
        with pytest.raises(Exception):  # Will raise InvalidTag
            decrypt_api_key(encrypted)

    @override_settings(KMS_SECRET="test-kms-secret-key")
    def test_handles_unicode(self):
        """Test that unicode characters in keys are handled."""
        api_key = "sk-test-key-with-unicode-émoji-🔑"
        encrypted = encrypt_api_key(api_key)
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == api_key

    @override_settings(KMS_SECRET="test-kms-secret-key")
    def test_handles_long_keys(self):
        """Test that long API keys are handled."""
        api_key = "sk-" + "a" * 1000
        encrypted = encrypt_api_key(api_key)
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == api_key
