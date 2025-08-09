from agentmesh.security.encryption import encrypt_data, decrypt_data
from loguru import logger
from unittest.mock import patch


def test_encrypt_data():
    data = b"test_data"
    with patch.object(logger, "warning") as mock_warning:
        encrypted_data = encrypt_data(data)
        assert encrypted_data == data
        mock_warning.assert_called_once_with(
            "Encryption is a placeholder and not implemented yet."
        )


def test_decrypt_data():
    data = b"test_data"
    with patch.object(logger, "warning") as mock_warning:
        decrypted_data = decrypt_data(data)
        assert decrypted_data == data
        mock_warning.assert_called_once_with(
            "Decryption is a placeholder and not implemented yet."
        )
