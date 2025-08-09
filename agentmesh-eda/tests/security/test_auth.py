import pytest
from datetime import timedelta
from agentmesh.security.auth import (
    create_access_token,
    verify_access_token,
)


class CredentialsException(Exception):
    pass


def test_create_access_token():
    data = {"sub": "testuser", "roles": ["admin", "agent"]}
    tenant_id = "test_tenant"
    token = create_access_token(
        data, tenant_id=tenant_id, expires_delta=timedelta(minutes=30)
    )
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_access_token_valid():
    data = {"sub": "testuser", "roles": ["admin", "agent"]}
    tenant_id = "test_tenant"
    token = create_access_token(data, tenant_id=tenant_id)

    payload = verify_access_token(token, CredentialsException)
    assert payload["sub"] == "testuser"
    assert payload["tenant_id"] == tenant_id
    assert "roles" in payload
    assert "exp" in payload


def test_verify_access_token_invalid_signature():
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY3MjU2OTYwMH0.invalid_signature"
    with pytest.raises(CredentialsException):
        verify_access_token(invalid_token, CredentialsException)


def test_verify_access_token_expired():
    data = {"sub": "testuser"}
    tenant_id = "test_tenant"
    expired_token = create_access_token(
        data, tenant_id=tenant_id, expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(CredentialsException):
        verify_access_token(expired_token, CredentialsException)


def test_verify_access_token_no_tenant_id():
    # Token created without tenant_id (using old method or a different issuer)
    from jose import jwt

    SECRET_KEY = "your-secret-key"
    ALGORITHM = "HS256"
    no_tenant_token = jwt.encode({"sub": "testuser"}, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(CredentialsException):
        verify_access_token(no_tenant_token, CredentialsException)
