"""
Message encryption utilities for end-to-end encryption of chat conversations.

This module provides AES-256-GCM encryption for securing user messages in Firebase.
Messages are encrypted before storage and decrypted when retrieved, ensuring that
database administrators cannot read conversation content.

Security Features:
- AES-256-GCM authenticated encryption (AEAD)
- Per-user encryption keys (DEK - Data Encryption Key)
- AWS KMS envelope encryption for key protection
- Automatic nonce generation for each message
- Version tagging for future migration support

Architecture:
- Each user has a unique DEK (32-byte AES key)
- User's DEK is encrypted with AWS KMS master key
- Encrypted DEK stored in Firebase
- Messages encrypted with user's DEK before storage
- Backend processes plaintext temporarily for AI, re-encrypts for storage

Usage:
    from utils.encryption import encrypt_message, decrypt_message, generate_dek

    # Generate new user key
    dek = generate_dek()

    # Encrypt message
    encrypted_data = encrypt_message("Hello world", dek)

    # Decrypt message
    plaintext = decrypt_message(encrypted_data, dek)
"""

import os
import base64
import logging
from typing import Dict, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Encryption constants
ENCRYPTION_VERSION = 1
KEY_SIZE = 32  # 256 bits for AES-256
NONCE_SIZE = 12  # 96 bits recommended for AES-GCM


def generate_dek() -> bytes:
    """
    Generate a new Data Encryption Key (DEK) for a user.

    Uses cryptographically secure random number generator to create
    a 256-bit AES key unique to each user.

    Returns:
        bytes: 32-byte encryption key

    Example:
        >>> dek = generate_dek()
        >>> len(dek)
        32
    """
    return AESGCM.generate_key(bit_length=256)


def encrypt_message(plaintext: str, key: bytes) -> Dict[str, str]:
    """
    Encrypt a message using AES-256-GCM.

    AES-GCM provides both confidentiality (encryption) and authenticity (MAC tag).
    Each encryption uses a unique random nonce to ensure the same message
    encrypts to different ciphertext each time.

    Args:
        plaintext: The message to encrypt (UTF-8 string)
        key: 32-byte AES encryption key

    Returns:
        Dictionary containing:
        - ciphertext: Base64-encoded encrypted message
        - nonce: Base64-encoded nonce (required for decryption)
        - version: Encryption version (for future migration)
        - algorithm: Encryption algorithm used

    Raises:
        ValueError: If key is not 32 bytes
        Exception: If encryption fails

    Example:
        >>> key = generate_dek()
        >>> encrypted = encrypt_message("Secret message", key)
        >>> encrypted.keys()
        dict_keys(['ciphertext', 'nonce', 'version', 'algorithm'])
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")

    try:
        # Generate random nonce (NEVER reuse with same key!)
        nonce = os.urandom(NONCE_SIZE)

        # Create AES-GCM cipher
        aesgcm = AESGCM(key)

        # Encrypt (GCM automatically adds authentication tag)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

        # Return Base64-encoded for storage
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'nonce': base64.b64encode(nonce).decode('utf-8'),
            'version': ENCRYPTION_VERSION,
            'algorithm': 'AES-256-GCM'
        }

    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise Exception(f"Message encryption failed: {str(e)}")


def decrypt_message(encrypted_data: Dict[str, str], key: bytes) -> str:
    """
    Decrypt a message encrypted with encrypt_message().

    Verifies the authentication tag before decrypting. If the message has been
    tampered with, decryption will fail (preventing attacks).

    Args:
        encrypted_data: Dictionary with 'ciphertext' and 'nonce' (Base64-encoded)
        key: 32-byte AES encryption key (same key used for encryption)

    Returns:
        str: Decrypted plaintext message

    Raises:
        ValueError: If key is wrong length or data is malformed
        Exception: If decryption fails (wrong key, tampered data, etc.)

    Example:
        >>> key = generate_dek()
        >>> encrypted = encrypt_message("Secret message", key)
        >>> plaintext = decrypt_message(encrypted, key)
        >>> plaintext
        'Secret message'
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")

    try:
        # Decode from Base64
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])

        # Create AES-GCM cipher
        aesgcm = AESGCM(key)

        # Decrypt and verify authentication tag
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext_bytes.decode('utf-8')

    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise Exception(f"Message decryption failed: {str(e)}")


def encode_key_for_storage(key: bytes) -> str:
    """
    Encode encryption key as Base64 string for storage.

    Args:
        key: Binary encryption key

    Returns:
        str: Base64-encoded key string

    Example:
        >>> key = generate_dek()
        >>> encoded = encode_key_for_storage(key)
        >>> len(encoded)
        44  # Base64 of 32 bytes
    """
    return base64.b64encode(key).decode('utf-8')


def decode_key_from_storage(encoded_key: str) -> bytes:
    """
    Decode encryption key from Base64 storage format.

    Args:
        encoded_key: Base64-encoded key string

    Returns:
        bytes: Binary encryption key

    Raises:
        ValueError: If decoded key is not 32 bytes

    Example:
        >>> key = generate_dek()
        >>> encoded = encode_key_for_storage(key)
        >>> decoded = decode_key_from_storage(encoded)
        >>> decoded == key
        True
    """
    key = base64.b64decode(encoded_key)
    if len(key) != KEY_SIZE:
        raise ValueError(f"Decoded key must be {KEY_SIZE} bytes, got {len(key)}")
    return key


def test_encryption_roundtrip(message: str = "Test message") -> bool:
    """
    Test encryption/decryption roundtrip to verify functionality.

    Useful for testing encryption setup and troubleshooting.

    Args:
        message: Test message to encrypt and decrypt

    Returns:
        bool: True if roundtrip successful, False otherwise

    Example:
        >>> test_encryption_roundtrip()
        True
    """
    try:
        # Generate test key
        key = generate_dek()

        # Encrypt
        encrypted = encrypt_message(message, key)

        # Decrypt
        decrypted = decrypt_message(encrypted, key)

        # Verify
        success = (decrypted == message)

        if success:
            logger.info("✅ Encryption roundtrip test passed")
        else:
            logger.error(f"❌ Encryption roundtrip failed: '{message}' != '{decrypted}'")

        return success

    except Exception as e:
        logger.error(f"❌ Encryption test failed with error: {e}")
        return False


# Optional: Derive key from password (for future use if needed)
def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """
    Derive an encryption key from a user password using PBKDF2.

    WARNING: Not currently used. Kept for potential future password-based encryption.
    Current system uses randomly generated keys protected by AWS KMS.

    Args:
        password: User's password
        salt: Random salt (should be stored with encrypted data)

    Returns:
        bytes: 32-byte derived encryption key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=480000,  # OWASP recommendation as of 2024
    )
    return kdf.derive(password.encode('utf-8'))


if __name__ == "__main__":
    # Run self-test
    print("Running encryption self-test...")

    # Test 1: Basic encryption/decryption
    success = test_encryption_roundtrip()

    # Test 2: Different messages produce different ciphertext
    key = generate_dek()
    enc1 = encrypt_message("Same message", key)
    enc2 = encrypt_message("Same message", key)
    different = (enc1['ciphertext'] != enc2['ciphertext'])

    if different:
        print("✅ Nonce randomization working (same message → different ciphertext)")
    else:
        print("❌ WARNING: Nonce randomization may not be working!")

    # Test 3: Wrong key fails decryption
    try:
        wrong_key = generate_dek()
        decrypt_message(enc1, wrong_key)
        print("❌ WARNING: Decryption succeeded with wrong key (security issue!)")
    except:
        print("✅ Wrong key correctly rejected")

    print("\nAll encryption tests completed!")
