# AgentMesh Security Setup Guide

## Overview

This guide explains how to properly configure security for AgentMesh in a secure, production-ready manner.

## Critical Security Configuration

### 1. Generate Encryption Key

AgentMesh uses Fernet (symmetric encryption) to protect sensitive data. You **must** generate a secure encryption key:

```bash
# Generate a new Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

This will output something like:
```
2FZWFO3VEVZVU0VYODBWRVBVD0ZBVDBFQTQZMDQ0MTRMZTM1N0U=
```

### 2. Generate JWT Secret Key

AgentMesh uses JWT tokens for authentication. Generate a strong secret:

```bash
# Generate a 256-bit (32-byte) random secret
openssl rand -hex 32
```

This will output something like:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

### 3. Configure Environment Variables

#### Development Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in the generated keys:
```bash
# Generate keys
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Create .env file
cat > .env << EOF
ENCRYPTION_KEY=$ENCRYPTION_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
DATABASE_URL=postgresql://agentmesh:agentmesh@localhost:5432/agentmesh
NATS_URL=nats://localhost:4222
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF
```

3. Verify the file was created:
```bash
cat .env
```

4. **IMPORTANT**: Add `.env` to `.gitignore`:
```bash
echo ".env" >> .gitignore
```

#### Production Setup

For production, use a secure secrets management system:

**Option 1: AWS Secrets Manager**
```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='agentmesh/security')
encryption_key = secret['SecretString']['ENCRYPTION_KEY']
```

**Option 2: Google Cloud Secret Manager**
```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
secret = client.access_secret_version(
    request={"name": "projects/PROJECT/secrets/ENCRYPTION_KEY/versions/latest"}
)
encryption_key = secret.payload.data.decode()
```

**Option 3: HashiCorp Vault**
```python
import hvac

client = hvac.Client(url='http://127.0.0.1:8200')
secret = client.secrets.kv.read_secret_version(path='agentmesh/security')
encryption_key = secret['data']['data']['ENCRYPTION_KEY']
```

### 4. Docker Compose Setup

For local development with Docker Compose:

```bash
# Create .env file with dev keys
python -c "
from cryptography.fernet import Fernet
import subprocess
import os

encryption_key = Fernet.generate_key().decode()
jwt_secret = subprocess.check_output(['openssl', 'rand', '-hex', '32']).decode().strip()

with open('.env', 'w') as f:
    f.write(f'ENCRYPTION_KEY={encryption_key}\n')
    f.write(f'JWT_SECRET_KEY={jwt_secret}\n')
    f.write('JWT_ALGORITHM=HS256\n')
    f.write('JWT_EXPIRATION_HOURS=24\n')
    f.write('DATABASE_URL=postgresql://agentmesh:agentmesh@postgres:5432/agentmesh\n')
    f.write('NATS_URL=nats://nats:4222\n')
    f.write('ENVIRONMENT=development\n')
    f.write('LOG_LEVEL=INFO\n')

print(f'ENCRYPTION_KEY={encryption_key}')
print(f'JWT_SECRET_KEY={jwt_secret}')
"

# Start services
docker-compose up -d
```

## Security Best Practices

### 1. Key Rotation

Implement regular key rotation (quarterly):

```python
from agentmesh.security.config import generate_encryption_key, get_security_config
from agentmesh.security.encryption import decrypt_data, encrypt_data
import os

def rotate_encryption_key():
    """Rotate encryption key"""
    # Generate new key
    new_key = generate_encryption_key()

    # Decrypt all data with old key
    old_service = get_security_config()

    # Re-encrypt with new key
    # Update all encrypted data in database

    # Update environment variable
    os.environ['ENCRYPTION_KEY'] = new_key

    # Restart application
    print(f"New ENCRYPTION_KEY: {new_key}")
```

### 2. Secret Scanning

Prevent accidental commits of secrets:

```bash
# Install git-secrets
brew install git-secrets

# Configure for your repo
git secrets --install
git secrets --register-aws
git secrets --add-provider -- git config --file .gitmodules --get-regexp url

# Scan existing commits
git secrets --scan-history
```

### 3. Security Audit Logging

Monitor all encryption operations:

```python
from agentmesh.security.encryption import get_encryption_service
from loguru import logger

service = get_encryption_service()

# All operations automatically logged:
# - Successful encryption/decryption
# - Failed decryption attempts
# - Invalid token errors
# - Configuration initialization
```

Check logs for suspicious activity:

```bash
# Monitor in real-time
tail -f logs/agentmesh.log | grep "Decryption failed"

# Analyze decryption failures
grep "Decryption failed" logs/agentmesh.log | tail -100
```

### 4. Token Security

Manage JWT tokens securely:

```python
from agentmesh.security.auth import create_access_token

# Create short-lived tokens (1-24 hours)
token = create_access_token(
    data={"sub": "user@example.com", "tenant_id": "tenant-1"},
    expires_delta=timedelta(hours=1)  # Short expiration
)

# Store tokens securely:
# - httpOnly cookies (not accessible to JavaScript)
# - Secure flag (HTTPS only)
# - SameSite=Strict (CSRF protection)

# Never log tokens
logger.info(f"Token created: {token[:20]}...") # Only log prefix
```

## Verification

### Test Encryption Configuration

```bash
# Run tests
cd agentmesh-eda
python -m pytest tests/security/test_encryption.py -v

# Expected output:
# test_encryption_config_validates_key ✓
# test_encryption_service_encrypts_data ✓
# test_encryption_service_decrypts_data ✓
# test_encryption_fails_with_invalid_key ✓
```

### Verify Environment Configuration

```bash
# Check that required environment variables are set
python -c "
from agentmesh.security.config import load_security_config
try:
    config = load_security_config()
    print('✓ Security configuration loaded successfully')
    print(f'  - Encryption key: {config.encryption_key[:20]}...')
    print(f'  - JWT algorithm: {config.jwt_algorithm}')
    print(f'  - Token expiration: {config.jwt_expiration_hours} hours')
except ValueError as e:
    print(f'✗ Configuration error: {e}')
"
```

## Troubleshooting

### Missing ENCRYPTION_KEY

**Error**: `ValueError: ENCRYPTION_KEY environment variable is required but not set`

**Solution**:
```bash
# Generate and set the key
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
```

### Missing JWT_SECRET_KEY

**Error**: `ValueError: JWT_SECRET_KEY environment variable is required but not set`

**Solution**:
```bash
# Generate and set the key
export JWT_SECRET_KEY=$(openssl rand -hex 32)
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> .env
```

### Decryption Failures

**Error**: `ValueError: Failed to decrypt data - invalid token or corrupted data`

**Causes**:
- Using wrong encryption key
- Data was encrypted with different key
- Data is corrupted

**Solution**:
1. Verify ENCRYPTION_KEY environment variable matches key used for encryption
2. Check data integrity in database
3. Restore from backup if needed

## Migration from Hardcoded Key

If upgrading from older AgentMesh version:

1. Generate secure keys (see above)
2. Set environment variables
3. Run migration script:

```python
from agentmesh.security.encryption import decrypt_data, encrypt_data
from agentmesh.db.database import get_session, Message

# Decrypt with old hardcoded key
old_key = b'YOUR_SECURE_KEY_HERE_...'
old_cipher = Fernet(old_key)

# For each encrypted message in database
session = get_session()
messages = session.query(Message).filter(Message.encrypted_payload != None).all()

for msg in messages:
    # Decrypt with old key
    decrypted = old_cipher.decrypt(msg.encrypted_payload)

    # Re-encrypt with new key (from environment)
    msg.encrypted_payload = encrypt_data(decrypted)

    session.add(msg)

session.commit()
print(f"Migrated {len(messages)} messages to new encryption key")
```

## References

- [Cryptography.io Fernet Documentation](https://cryptography.io/en/latest/fernet/)
- [Python-jose JWT Documentation](https://python-jose.readthedocs.io/)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Configuration](https://12factor.net/config)

---

**Last Updated**: 2024
**Status**: Implementation Ready
