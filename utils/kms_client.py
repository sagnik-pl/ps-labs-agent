"""
AWS KMS client for envelope encryption of user encryption keys.

This module provides AWS Key Management Service integration for protecting
user Data Encryption Keys (DEKs). Uses envelope encryption pattern:

- User messages encrypted with DEK (fast, local)
- DEK encrypted with KMS master key (secure, centralized)
- Encrypted DEK stored in Firebase
- KMS master key never leaves AWS

Security Benefits:
- Separation of concerns: Firebase admins can't decrypt without KMS access
- Centralized key management: Rotate master key without re-encrypting messages
- Audit trail: All KMS operations logged in CloudTrail
- Hardware-backed: KMS keys protected by HSMs (FIPS 140-2 Level 3)

Architecture:
┌──────────┐
│  User    │
└────┬─────┘
     │
     ▼
┌──────────────────┐      ┌─────────────┐
│ User's DEK       │─────▶│  Firebase   │
│ (32 bytes)       │      │  (stores)   │
└──────────────────┘      └─────────────┘
     │ encrypt/decrypt
     ▼
┌──────────────────┐      ┌─────────────┐
│ KMS Master Key   │◀────▶│  AWS KMS    │
│ (never exposed)  │      │  (manages)  │
└──────────────────┘      └─────────────┘

Usage:
    from utils.kms_client import kms_client
    from utils.encryption import generate_dek

    # Generate and encrypt user's DEK
    dek = generate_dek()
    encrypted_dek = kms_client.encrypt_dek(dek)

    # Later: decrypt to use
    dek = kms_client.decrypt_dek(encrypted_dek)
"""

import boto3
import base64
import logging
from typing import Optional
from config.settings import settings

logger = logging.getLogger(__name__)


class KMSClient:
    """AWS KMS client for encrypting/decrypting user encryption keys."""

    def __init__(self):
        """
        Initialize KMS client with AWS credentials.

        Connects to AWS KMS using credentials from settings.
        Validates KMS configuration on init.
        """
        try:
            self.kms_client = boto3.client(
                'kms',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )

            # Get KMS key ID from settings
            self.kms_key_id = settings.kms_key_id

            # Check if encryption is enabled
            self.encryption_enabled = settings.encryption_enabled

            if self.encryption_enabled:
                if not self.kms_key_id:
                    raise ValueError("KMS_KEY_ID must be set when ENCRYPTION_ENABLED=true")

                logger.info(f"✅ KMS client initialized (Key: {self.kms_key_id[:20]}...)")
            else:
                logger.info("⚠️  KMS client initialized but encryption is DISABLED")

        except Exception as e:
            logger.error(f"❌ Failed to initialize KMS client: {e}")
            raise Exception(f"KMS initialization failed: {str(e)}")

    def encrypt_dek(self, dek: bytes) -> str:
        """
        Encrypt a user's Data Encryption Key using KMS master key.

        Uses AWS KMS Encrypt API to wrap the user's DEK with the master key.
        The encrypted DEK can be safely stored in Firebase.

        Args:
            dek: 32-byte user encryption key to protect

        Returns:
            str: Base64-encoded encrypted DEK (safe for Firebase storage)

        Raises:
            Exception: If KMS encryption fails

        Example:
            >>> from utils.encryption import generate_dek
            >>> dek = generate_dek()
            >>> encrypted = kms_client.encrypt_dek(dek)
            >>> len(encrypted) > 100  # Encrypted is longer than original
            True
        """
        if not self.encryption_enabled:
            raise Exception("Encryption is disabled - cannot encrypt DEK")

        try:
            # Call KMS to encrypt the DEK
            response = self.kms_client.encrypt(
                KeyId=self.kms_key_id,
                Plaintext=dek,
                EncryptionAlgorithm='SYMMETRIC_DEFAULT'  # AES-256-GCM
            )

            # Extract ciphertext blob and encode for storage
            encrypted_dek = base64.b64encode(response['CiphertextBlob']).decode('utf-8')

            logger.info(f"✅ DEK encrypted successfully (length: {len(encrypted_dek)} chars)")

            return encrypted_dek

        except Exception as e:
            logger.error(f"❌ KMS encryption failed: {e}")
            raise Exception(f"Failed to encrypt DEK with KMS: {str(e)}")

    def decrypt_dek(self, encrypted_dek: str) -> bytes:
        """
        Decrypt a user's Data Encryption Key using KMS.

        Uses AWS KMS Decrypt API to unwrap the DEK. KMS automatically
        determines which master key was used for encryption.

        Args:
            encrypted_dek: Base64-encoded encrypted DEK from Firebase

        Returns:
            bytes: 32-byte decrypted DEK ready for use

        Raises:
            Exception: If KMS decryption fails (wrong key, tampering, etc.)

        Example:
            >>> encrypted = kms_client.encrypt_dek(dek)
            >>> decrypted = kms_client.decrypt_dek(encrypted)
            >>> decrypted == dek
            True
        """
        if not self.encryption_enabled:
            raise Exception("Encryption is disabled - cannot decrypt DEK")

        try:
            # Decode from Base64
            ciphertext_blob = base64.b64decode(encrypted_dek)

            # Call KMS to decrypt (KMS knows which key to use)
            response = self.kms_client.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionAlgorithm='SYMMETRIC_DEFAULT'
            )

            # Extract plaintext DEK
            dek = response['Plaintext']

            logger.debug(f"✅ DEK decrypted successfully (length: {len(dek)} bytes)")

            return dek

        except Exception as e:
            logger.error(f"❌ KMS decryption failed: {e}")
            raise Exception(f"Failed to decrypt DEK with KMS: {str(e)}")

    def get_key_info(self) -> dict:
        """
        Get information about the KMS key.

        Useful for debugging and verification.

        Returns:
            dict: KMS key metadata (ID, ARN, status, etc.)

        Example:
            >>> info = kms_client.get_key_info()
            >>> info['KeyState']
            'Enabled'
        """
        if not self.encryption_enabled:
            return {"status": "disabled"}

        try:
            response = self.kms_client.describe_key(KeyId=self.kms_key_id)
            return {
                "key_id": response['KeyMetadata']['KeyId'],
                "arn": response['KeyMetadata']['Arn'],
                "state": response['KeyMetadata']['KeyState'],
                "enabled": response['KeyMetadata']['Enabled'],
                "description": response['KeyMetadata'].get('Description', 'No description')
            }
        except Exception as e:
            logger.error(f"Failed to get KMS key info: {e}")
            return {"error": str(e)}

    def test_kms_access(self) -> bool:
        """
        Test KMS access by performing a dummy encrypt/decrypt operation.

        Useful for validating KMS configuration and permissions.

        Returns:
            bool: True if KMS is accessible and working, False otherwise

        Example:
            >>> kms_client.test_kms_access()
            True
        """
        if not self.encryption_enabled:
            logger.info("⚠️  Encryption disabled - skipping KMS test")
            return True  # Not an error if encryption is off

        try:
            # Generate test data
            test_data = b"test encryption key 1234567890123456"  # 32 bytes

            # Encrypt
            encrypted = self.encrypt_dek(test_data)

            # Decrypt
            decrypted = self.decrypt_dek(encrypted)

            # Verify
            if decrypted == test_data:
                logger.info("✅ KMS access test passed")
                return True
            else:
                logger.error("❌ KMS roundtrip failed - data mismatch")
                return False

        except Exception as e:
            logger.error(f"❌ KMS access test failed: {e}")
            return False


# Global KMS client instance (lazy initialization)
_kms_client_instance: Optional[KMSClient] = None


def get_kms_client() -> KMSClient:
    """
    Get singleton KMS client instance.

    Lazily initializes KMS client on first use.
    Reuses same instance for all subsequent calls.

    Returns:
        KMSClient: Singleton KMS client instance

    Example:
        >>> kms = get_kms_client()
        >>> kms.encryption_enabled
        True
    """
    global _kms_client_instance

    if _kms_client_instance is None:
        _kms_client_instance = KMSClient()

    return _kms_client_instance


# Convenience instance for direct import
kms_client = get_kms_client()


if __name__ == "__main__":
    # Run self-test
    print("Testing KMS client...")

    try:
        kms = get_kms_client()

        print(f"Encryption enabled: {kms.encryption_enabled}")

        if kms.encryption_enabled:
            print(f"KMS Key ID: {kms.kms_key_id}")

            # Test KMS access
            print("\nTesting KMS access...")
            success = kms.test_kms_access()

            if success:
                print("✅ KMS client working correctly!")
            else:
                print("❌ KMS test failed")

            # Get key info
            print("\nKMS Key Info:")
            info = kms.get_key_info()
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️  Encryption is disabled - KMS tests skipped")

    except Exception as e:
        print(f"❌ KMS test failed with error: {e}")
