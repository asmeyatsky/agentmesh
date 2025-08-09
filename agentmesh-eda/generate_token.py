from datetime import timedelta
from agentmesh.security.auth import create_access_token

data = {"roles": ["admin", "agent"]}  # No 'sub' field
token = create_access_token(data, expires_delta=timedelta(days=365))
print(token)
