"""
Encryption Module

Architectural Intent:
- Provides encryption/decryption services using Fernet (symmetric encryption)
- Uses secure configuration from environment variables
- Centralizes all encryption operations
- Supports audit logging of encryption operations

Key Design Decisions:
1. Configuration injected at module initialization (testability)
2. Lazy initialization of Fernet cipher
3. Comprehensive error handling and logging
4. Support for encrypted payload in UniversalMessage
"""

from loguru import logger
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional
from .config import get_security_config


class EncryptionService:
    """
    Service for encrypting and decrypting data.

    Invariants:
    - Cipher is initialized once from secure configuration
    - All encryption operations are logged
    - Decryption failures are caught and logged
    """

    def __init__(self):
        """Initialize encryption service with configured key"""
        config = get_security_config()
        try:
            # Convert string key to bytes for Fernet
            key_bytes = config.encryption_key.encode() if isinstance(config.encryption_key, str) else config.encryption_key
            self._cipher = Fernet(key_bytes)
            logger.info("EncryptionService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EncryptionService: {e}")
            raise

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data using Fernet symmetric encryption.

        Args:
            data: Raw bytes to encrypt

        Returns:
            Encrypted bytes (includes timestamp and IV)

        Raises:
            TypeError: If data is not bytes
        """
        if not isinstance(data, bytes):
            raise TypeError(f"Data must be bytes, got {type(data)}")

        try:
            encrypted = self._cipher.encrypt(data)
            logger.debug(f"Successfully encrypted {len(data)} bytes -> {len(encrypted)} bytes")
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data using Fernet symmetric decryption.

        Args:
            encrypted_data: Encrypted bytes from encrypt_data()

        Returns:
            Decrypted bytes

        Raises:
            InvalidToken: If decryption fails (corrupted or tampered data)
            TypeError: If encrypted_data is not bytes
        """
        if not isinstance(encrypted_data, bytes):
            raise TypeError(f"Encrypted data must be bytes, got {type(encrypted_data)}")

        try:
            decrypted = self._cipher.decrypt(encrypted_data)
            logger.debug(f"Successfully decrypted {len(encrypted_data)} bytes -> {len(decrypted)} bytes")
            return decrypted
        except InvalidToken as e:
            logger.error(f"Decryption failed - data is corrupted or tampered: {e}")
            raise ValueError("Failed to decrypt data - invalid token or corrupted data") from e
        except Exception as e:
            logger.error(f"Decryption failed with unexpected error: {e}")
            raise


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get or initialize global encryption service.

    Uses lazy initialization pattern for dependency injection compatibility.

    Returns:
        Singleton EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


def encrypt_data(data: bytes) -> bytes:
    """Legacy function interface - delegates to service"""
    return get_encryption_service().encrypt_data(data)


def decrypt_data(data: bytes) -> bytes:
    """Legacy function interface - delegates to service"""
    return get_encryption_service().decrypt_data(data)
