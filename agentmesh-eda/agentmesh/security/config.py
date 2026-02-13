"""
Security Configuration Module

Architectural Intent:
- Centralizes security configuration management
- Supports environment-based configuration for production safety
- Enforces validation of security parameters
- Enables key rotation and secure secrets management

Key Design Decisions:
1. Configuration loaded from environment variables (12-factor app)
2. Mandatory encryption key validation on startup
3. Support for multiple secret providers (env vars, KMS, vaults)
4. Immutable configuration after initialization
"""

import os
import threading
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass(frozen=True)
class SecurityConfig:
    """
    Immutable Security Configuration

    Invariants:
    - encryption_key must be valid Fernet key (44 bytes, base64-encoded)
    - jwt_secret_key must not be empty
    - jwt_algorithm must be supported
    """
    encryption_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    def __post_init__(self):
        """Validate configuration on creation"""
        if not self.encryption_key:
            raise ValueError("encryption_key is required and cannot be empty")

        # Validate encryption key format (Fernet keys are 44 bytes, URL-safe base64)
        if len(self.encryption_key) != 44:
            raise ValueError(
                f"encryption_key must be 44 bytes (base64-encoded Fernet key), "
                f"got {len(self.encryption_key)} bytes. "
                f"Generate a new key using: from cryptography.fernet import Fernet; "
                f"print(Fernet.generate_key().decode())"
            )

        if not self.jwt_secret_key:
            raise ValueError("jwt_secret_key is required and cannot be empty")

        if self.jwt_algorithm not in ["HS256", "HS384", "HS512", "RS256"]:
            raise ValueError(
                f"jwt_algorithm must be one of [HS256, HS384, HS512, RS256], "
                f"got {self.jwt_algorithm}"
            )

        if self.jwt_expiration_hours <= 0:
            raise ValueError("jwt_expiration_hours must be positive")

        logger.info(f"SecurityConfig initialized with algorithm={self.jwt_algorithm}")


def load_security_config() -> SecurityConfig:
    """
    Load security configuration from environment variables.

    Environment Variables:
    - ENCRYPTION_KEY: Fernet encryption key (required)
    - JWT_SECRET_KEY: JWT signing key (required)
    - JWT_ALGORITHM: JWT algorithm (default: HS256)
    - JWT_EXPIRATION_HOURS: Token expiration in hours (default: 24)

    Returns:
        SecurityConfig instance with validated configuration

    Raises:
        ValueError: If required environment variables are missing or invalid
    """
    encryption_key = os.getenv("ENCRYPTION_KEY")
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")

    if not encryption_key:
        raise ValueError(
            "ENCRYPTION_KEY environment variable is required but not set. "
            "Generate one using: from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())"
        )

    if not jwt_secret_key:
        raise ValueError(
            "JWT_SECRET_KEY environment variable is required but not set. "
            "Use a strong random string (e.g., openssl rand -hex 32)"
        )

    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    logger.info(
        f"Loading security config from environment: "
        f"algorithm={jwt_algorithm}, expiration={jwt_expiration}h"
    )

    return SecurityConfig(
        encryption_key=encryption_key,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        jwt_expiration_hours=jwt_expiration
    )


def generate_encryption_key() -> str:
    """
    Generate a new encryption key for Fernet.

    Returns:
        Base64-encoded Fernet key string (44 characters)

    Usage:
        key = generate_encryption_key()
        print(f"ENCRYPTION_KEY={key}")
        # Save to environment or secrets manager
    """
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


# Global config instance (thread-safe lazy init)
_config: Optional[SecurityConfig] = None
_config_lock = threading.Lock()


def get_security_config() -> SecurityConfig:
    """
    Get or initialize global security configuration.

    Uses double-checked locking for thread-safe lazy initialization.

    Returns:
        Singleton SecurityConfig instance
    """
    global _config
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = load_security_config()
    return _config
