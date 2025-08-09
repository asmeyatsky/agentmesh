Security
========

The Security module provides services for authenticating and authorizing users and agents.

Core Components
---------------

- **Authentication:** A service for verifying the identity of a user or agent.
- **Authorization:** A service for determining whether a user or agent is allowed to perform a certain action.
- **Encryption:** A service for encrypting and decrypting data.

Usage
-----

To use the Security module, you can use the `create_access_token` and `verify_access_token` functions to generate and verify JWTs.

.. code-block:: python

    from agentmesh.security.auth import create_access_token, verify_access_token

    data = {"sub": "testuser"}
    tenant_id = "test_tenant"
    token = create_access_token(data, tenant_id)

    try:
        payload = verify_access_token(token, credentials_exception=Exception)
        print(payload)
    except Exception as e:
        print(f"Invalid token: {e}")
