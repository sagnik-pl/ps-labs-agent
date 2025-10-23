"""
Unit tests for encryption utilities.

Tests AES-256-GCM encryption, decryption, key generation,
and integration with AWS KMS envelope encryption.
"""

import pytest
import base64
from utils.encryption import (
    generate_dek,
    encrypt_message,
    decrypt_message,
    encode_key_for_storage,
    decode_key_from_storage,
    test_encryption_roundtrip,
    KEY_SIZE,
    NONCE_SIZE,
)


class TestKeyGeneration:
    """Test encryption key generation."""

    def test_generate_dek_length(self):
        """Test that generated DEK is correct length (32 bytes)."""
        dek = generate_dek()
        assert len(dek) == KEY_SIZE
        assert isinstance(dek, bytes)

    def test_generate_dek_uniqueness(self):
        """Test that each generated DEK is unique."""
        dek1 = generate_dek()
        dek2 = generate_dek()
        assert dek1 != dek2

    def test_generate_dek_randomness(self):
        """Test that generated DEKs have high entropy (not all zeros/ones)."""
        dek = generate_dek()
        # Check it's not all zeros
        assert dek != b"\x00" * KEY_SIZE
        # Check it's not all ones
        assert dek != b"\xff" * KEY_SIZE


class TestEncryption:
    """Test message encryption functionality."""

    def test_encrypt_message_basic(self):
        """Test basic message encryption."""
        key = generate_dek()
        plaintext = "Hello, World!"

        encrypted = encrypt_message(plaintext, key)

        # Check return structure
        assert "ciphertext" in encrypted
        assert "nonce" in encrypted
        assert "version" in encrypted
        assert "algorithm" in encrypted

        # Check values are Base64 encoded strings
        assert isinstance(encrypted["ciphertext"], str)
        assert isinstance(encrypted["nonce"], str)

        # Ciphertext should be different from plaintext
        assert encrypted["ciphertext"] != plaintext

    def test_encrypt_message_nonce_randomness(self):
        """Test that each encryption uses a different nonce."""
        key = generate_dek()
        plaintext = "Same message"

        encrypted1 = encrypt_message(plaintext, key)
        encrypted2 = encrypt_message(plaintext, key)

        # Nonces should be different
        assert encrypted1["nonce"] != encrypted2["nonce"]

        # Ciphertexts should be different (due to different nonces)
        assert encrypted1["ciphertext"] != encrypted2["ciphertext"]

    def test_encrypt_message_wrong_key_length(self):
        """Test that encryption rejects keys of wrong length."""
        bad_key = b"short_key"
        plaintext = "Test message"

        with pytest.raises(ValueError, match="Key must be 32 bytes"):
            encrypt_message(plaintext, bad_key)

    def test_encrypt_empty_message(self):
        """Test encrypting an empty string."""
        key = generate_dek()
        plaintext = ""

        encrypted = encrypt_message(plaintext, key)

        # Should succeed
        assert "ciphertext" in encrypted
        assert "nonce" in encrypted

    def test_encrypt_long_message(self):
        """Test encrypting a long message."""
        key = generate_dek()
        plaintext = "A" * 10000  # 10KB message

        encrypted = encrypt_message(plaintext, key)

        # Should succeed
        assert "ciphertext" in encrypted
        assert len(encrypted["ciphertext"]) > 0

    def test_encrypt_unicode_message(self):
        """Test encrypting Unicode characters."""
        key = generate_dek()
        plaintext = "Hello 世界 🌍 Привет"

        encrypted = encrypt_message(plaintext, key)

        # Should succeed
        assert "ciphertext" in encrypted


class TestDecryption:
    """Test message decryption functionality."""

    def test_decrypt_message_basic(self):
        """Test basic message decryption."""
        key = generate_dek()
        plaintext = "Secret message"

        encrypted = encrypt_message(plaintext, key)
        decrypted = decrypt_message(encrypted, key)

        assert decrypted == plaintext

    def test_decrypt_with_wrong_key(self):
        """Test that decryption fails with wrong key."""
        key1 = generate_dek()
        key2 = generate_dek()
        plaintext = "Secret message"

        encrypted = encrypt_message(plaintext, key1)

        # Should raise exception (authentication tag verification fails)
        with pytest.raises(Exception):
            decrypt_message(encrypted, key2)

    def test_decrypt_tampered_ciphertext(self):
        """Test that decryption fails if ciphertext is tampered."""
        key = generate_dek()
        plaintext = "Secret message"

        encrypted = encrypt_message(plaintext, key)

        # Tamper with ciphertext
        ciphertext_bytes = base64.b64decode(encrypted["ciphertext"])
        tampered_bytes = bytes([b ^ 0xFF for b in ciphertext_bytes])  # Flip all bits
        encrypted["ciphertext"] = base64.b64encode(tampered_bytes).decode("utf-8")

        # Should raise exception (authentication tag verification fails)
        with pytest.raises(Exception):
            decrypt_message(encrypted, key)

    def test_decrypt_wrong_nonce(self):
        """Test that decryption fails with wrong nonce."""
        key = generate_dek()
        plaintext = "Secret message"

        encrypted1 = encrypt_message(plaintext, key)
        encrypted2 = encrypt_message(plaintext, key)

        # Use ciphertext from encrypted1 but nonce from encrypted2
        mixed = {
            "ciphertext": encrypted1["ciphertext"],
            "nonce": encrypted2["nonce"],
            "version": 1,
            "algorithm": "AES-256-GCM",
        }

        # Should fail (wrong nonce)
        with pytest.raises(Exception):
            decrypt_message(mixed, key)


class TestEncryptionRoundtrip:
    """Test full encryption/decryption roundtrips."""

    def test_roundtrip_short_message(self):
        """Test encrypt/decrypt roundtrip with short message."""
        key = generate_dek()
        original = "Hi!"

        encrypted = encrypt_message(original, key)
        decrypted = decrypt_message(encrypted, key)

        assert decrypted == original

    def test_roundtrip_long_message(self):
        """Test encrypt/decrypt roundtrip with long message."""
        key = generate_dek()
        original = "Lorem ipsum dolor sit amet. " * 1000  # ~28KB

        encrypted = encrypt_message(original, key)
        decrypted = decrypt_message(encrypted, key)

        assert decrypted == original

    def test_roundtrip_special_characters(self):
        """Test roundtrip with special characters and newlines."""
        key = generate_dek()
        original = 'Special chars: \n\t\r"\'!@#$%^&*()'

        encrypted = encrypt_message(original, key)
        decrypted = decrypt_message(encrypted, key)

        assert decrypted == original

    def test_roundtrip_json_data(self):
        """Test roundtrip with JSON-like data."""
        key = generate_dek()
        original = '{"user": "test@example.com", "message": "Hello, World!"}'

        encrypted = encrypt_message(original, key)
        decrypted = decrypt_message(encrypted, key)

        assert decrypted == original

    def test_roundtrip_multiple_messages(self):
        """Test encrypting/decrypting multiple messages with same key."""
        key = generate_dek()
        messages = [
            "First message",
            "Second message",
            "Third message with more text",
            "Fourth",
        ]

        encrypted_messages = [encrypt_message(msg, key) for msg in messages]
        decrypted_messages = [decrypt_message(enc, key) for enc in encrypted_messages]

        assert decrypted_messages == messages


class TestKeyStorage:
    """Test key encoding/decoding for storage."""

    def test_encode_key_for_storage(self):
        """Test encoding key as Base64 string."""
        key = generate_dek()
        encoded = encode_key_for_storage(key)

        # Should be Base64 string
        assert isinstance(encoded, str)
        assert len(encoded) == 44  # Base64 of 32 bytes

        # Should be valid Base64
        decoded = base64.b64decode(encoded)
        assert len(decoded) == KEY_SIZE

    def test_decode_key_from_storage(self):
        """Test decoding key from Base64 string."""
        key = generate_dek()
        encoded = encode_key_for_storage(key)
        decoded = decode_key_from_storage(encoded)

        assert decoded == key

    def test_decode_invalid_key(self):
        """Test that decoding invalid key raises error."""
        # Too short
        with pytest.raises(ValueError, match="Decoded key must be 32 bytes"):
            decode_key_from_storage(base64.b64encode(b"short").decode("utf-8"))


class TestEncryptionHelpers:
    """Test helper functions."""

    def test_encryption_roundtrip_test(self):
        """Test the built-in encryption test function."""
        result = test_encryption_roundtrip("Test message")
        assert result is True

    def test_encryption_roundtrip_test_custom_message(self):
        """Test roundtrip with custom message."""
        result = test_encryption_roundtrip("Custom test message with 世界 Unicode")
        assert result is True


class TestEncryptionSecurity:
    """Security-focused tests."""

    def test_nonce_never_reused(self):
        """Test that nonces are never reused (critical for GCM security)."""
        key = generate_dek()
        plaintext = "Same message"

        # Generate 100 encryptions
        nonces = []
        for _ in range(100):
            encrypted = encrypt_message(plaintext, key)
            nonces.append(encrypted["nonce"])

        # All nonces should be unique
        assert len(nonces) == len(set(nonces))

    def test_authentication_tag_verification(self):
        """Test that GCM authentication tag is verified on decryption."""
        key = generate_dek()
        plaintext = "Authenticated message"

        encrypted = encrypt_message(plaintext, key)

        # Modify the last byte of ciphertext (which contains auth tag)
        ciphertext_bytes = bytearray(base64.b64decode(encrypted["ciphertext"]))
        ciphertext_bytes[-1] ^= 0xFF  # Flip last byte
        encrypted["ciphertext"] = base64.b64encode(bytes(ciphertext_bytes)).decode(
            "utf-8"
        )

        # Should fail authentication
        with pytest.raises(Exception):
            decrypt_message(encrypted, key)

    def test_key_separation(self):
        """Test that different keys produce different ciphertexts."""
        key1 = generate_dek()
        key2 = generate_dek()
        plaintext = "Same plaintext"

        encrypted1 = encrypt_message(plaintext, key1)
        encrypted2 = encrypt_message(plaintext, key2)

        # Ciphertexts should be completely different
        assert encrypted1["ciphertext"] != encrypted2["ciphertext"]

        # Each should only decrypt with its own key
        assert decrypt_message(encrypted1, key1) == plaintext
        assert decrypt_message(encrypted2, key2) == plaintext

        with pytest.raises(Exception):
            decrypt_message(encrypted1, key2)

        with pytest.raises(Exception):
            decrypt_message(encrypted2, key1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
