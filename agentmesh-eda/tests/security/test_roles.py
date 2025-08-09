from agentmesh.security.roles import UserRole, has_role


def test_has_role_true():
    user_roles = [UserRole.ADMIN, UserRole.AGENT]
    required_roles = [UserRole.AGENT]
    assert has_role(user_roles, required_roles)


def test_has_role_false():
    user_roles = [UserRole.OBSERVER]
    required_roles = [UserRole.AGENT, UserRole.ADMIN]
    assert not has_role(user_roles, required_roles)


def test_has_role_empty_user_roles():
    user_roles = []
    required_roles = [UserRole.AGENT]
    assert not has_role(user_roles, required_roles)


def test_has_role_empty_required_roles():
    user_roles = [UserRole.ADMIN]
    required_roles = []
    assert has_role(user_roles, required_roles)  # If no roles are required, it always passes
