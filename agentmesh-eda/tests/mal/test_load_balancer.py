import pytest
from agentmesh.mal.load_balancer import IntelligentLoadBalancer


def test_load_balancer_select_target():
    load_balancer = IntelligentLoadBalancer()
    targets = ["target1", "target2", "target3"]

    # For simplicity, our current load balancer always selects the first target
    selected = load_balancer.select_target(targets)
    assert selected == "target1"


def test_load_balancer_select_target_empty():
    load_balancer = IntelligentLoadBalancer()
    with pytest.raises(ValueError, match="No targets available for load balancing"):
        load_balancer.select_target([])
