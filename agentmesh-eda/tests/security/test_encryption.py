from agentmesh.security.encryption import encrypt_data, decrypt_data
from loguru import logger
from unittest.mock import patch


def test_encrypt_data():
    data = b"test_data"
    encrypted_data = encrypt_data(data)
    assert encrypted_data != data  # Should be encrypted (different)
    assert len(encrypted_data) > len(data)  # Encrypted data is larger
    assert isinstance(encrypted_data, bytes)


def test_decrypt_data():
    data = b"test_data"
    encrypted_data = encrypt_data(data)
    decrypted_data = decrypt_data(encrypted_data)
    assert decrypted_data == data  # Should match original


def test_encrypt_decrypt_roundtrip():
    """Test that encrypt/decrypt maintains data integrity"""
    original_data = b"sensitive_information_123"
    encrypted = encrypt_data(original_data)
    decrypted = decrypt_data(encrypted)

    assert decrypted == original_data
    assert encrypted != original_data
