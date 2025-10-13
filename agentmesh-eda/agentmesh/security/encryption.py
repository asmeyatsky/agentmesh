from loguru import logger
from cryptography.fernet import Fernet

# In a real application, this key would be securely managed (e.g., environment variable, KMS)
# For demonstration purposes, we'll generate one or use a fixed one.
# You should generate a new key for production environments.
# key = Fernet.generate_key() # Use this to generate a new key
ENCRYPTION_KEY = b'YOUR_SECURE_KEY_HERE_REPLACE_THIS_WITH_A_GENERATED_KEY='

fernet = Fernet(ENCRYPTION_KEY)

def encrypt_data(data: bytes) -> bytes:
    logger.debug("Encrypting data...")
    return fernet.encrypt(data)

def decrypt_data(data: bytes) -> bytes:
    logger.debug("Decrypting data...")
    return fernet.decrypt(data)
