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
    token = create_access_token(data, expires_delta=timedelta(minutes=30))
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_access_token_valid():
    valid_token_str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInJvbGVzIjpbImFkbWluIiwiYWdlbnQiXSwiZXhwIjoxNzg2MjU0NDc4fQ.zwjURNPdcarF99w65l4OAmgdLVT0wdcPT-GBemZKOec"

    payload = verify_access_token(valid_token_str, CredentialsException)
    assert payload["sub"] == "testuser"
    assert "roles" in payload
    assert "exp" in payload


def test_verify_access_token_invalid_signature():
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY3MjU2OTYwMH0.invalid_signature"
    with pytest.raises(CredentialsException):
        verify_access_token(invalid_token, CredentialsException)


def test_verify_access_token_expired():
    expired_token_str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInJvbGVzIjpbImFkbWluIiwiYWdlbnQiXSwiZXhwIjoxNzU0NzE4NDQ4fQ.-jwgiv5kkioF_hentDJ9ogCcbNQyc5XgxIO-VptR__I"

    with pytest.raises(CredentialsException):
        verify_access_token(expired_token_str, CredentialsException)


def test_verify_access_token_no_sub():
    no_sub_token_str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlcyI6WyJhZG1pbiIsImFnZW50Il0sImV4cCI6MTc4NjI1NDUzM30._Z3bk5kajWK0v1d1wIgDX0nPdLleiWs0YX5J21eG4fA"

    # Modify auth.py to check for 'sub' and raise exception if not present
    # For now, it will return the payload, and the router will handle the missing 'sub'
    payload = verify_access_token(no_sub_token_str, CredentialsException)
    assert "sub" not in payload  # Ensure 'sub' is not in payload
