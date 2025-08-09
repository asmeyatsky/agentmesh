import pytest
from datetime import timedelta
from agentmesh.security.auth import create_access_token


@pytest.fixture
def valid_token():
    data = {"sub": "testuser", "roles": ["agent"]}
    token = create_access_token(data, expires_delta=timedelta(days=3650))
    return token
