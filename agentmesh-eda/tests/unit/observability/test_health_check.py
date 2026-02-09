"""
Health Check Module Tests

Tests for the health check functionality including
Kubernetes probe support, component status tracking, and aggregate health reporting.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from agentmesh.infrastructure.observability.health_check import (
    HealthCheckService,
    HealthStatus,
    ComponentHealth,
    SystemHealth,
)


class TestHealthStatus:
    """Test HealthStatus enum functionality"""

    def test_health_status_values(self):
        """Test health status enum has correct values"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_status_members(self):
        """Test health status enum members"""
        assert hasattr(HealthStatus, "HEALTHY")
        assert hasattr(HealthStatus, "DEGRADED")
        assert hasattr(HealthStatus, "UNHEALTHY")
        assert len(HealthStatus) == 3


class TestComponentHealth:
    """Test ComponentHealth model"""

    def test_component_health_creation(self):
        """Test creating a component health record"""
        component = ComponentHealth(
            name="test-component",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.5,
            message="Component is working",
        )

        assert component.name == "test-component"
        assert component.status == HealthStatus.HEALTHY
        assert component.message == "Component is working"
        assert component.response_time_ms == 50.5
        assert component.details == {}

    def test_component_health_with_details(self):
        """Test component health with additional details"""
        details = {"version": "1.0.0", "connections": 5}
        component = ComponentHealth(
            name="database",
            status=HealthStatus.DEGRADED,
            response_time_ms=150.0,
            message="Slow response time",
            details=details,
        )

        assert component.details == details


class TestHealthCheckService:
    """Test HealthCheckService functionality"""

    @pytest.fixture
    def health_service(self):
        """Create a health check service"""
        return HealthCheckService(
            service_name="test-service", version="1.0.0", environment="test"
        )

    def test_service_initialization(self, health_service):
        """Test health service initialization"""
        assert health_service.service_name == "test-service"
        assert health_service.version == "1.0.0"
        assert health_service.environment == "test"
        assert health_service.dependencies == {}

    @pytest.mark.asyncio
    async def test_check_database_no_dependency(self, health_service):
        """Test database check when no dependency configured"""
        result = await health_service.check_database()

        assert result.name == "database"
        assert result.status == HealthStatus.HEALTHY
        assert "not configured" in result.message
        assert result.response_time_ms == 0

    @pytest.mark.asyncio
    async def test_check_message_broker_no_dependency(self, health_service):
        """Test message broker check when no dependency configured"""
        result = await health_service.check_message_broker()

        assert result.name == "message_broker"
        assert result.status == HealthStatus.HEALTHY
        assert "not configured" in result.message
        assert result.response_time_ms == 0

    @pytest.mark.asyncio
    async def test_check_cache_no_dependency(self, health_service):
        """Test cache check when no dependency configured"""
        result = await health_service.check_cache()

        assert result.name == "cache"
        assert result.status == HealthStatus.HEALTHY
        assert "not configured" in result.message
        assert result.response_time_ms == 0

    @pytest.mark.asyncio
    async def test_check_event_store_no_dependency(self, health_service):
        """Test event store check when no dependency configured"""
        result = await health_service.check_event_store()

        assert result.name == "event_store"
        assert result.status == HealthStatus.HEALTHY
        assert "not configured" in result.message
        assert result.response_time_ms == 0

    @pytest.mark.asyncio
    async def test_get_system_health_no_dependencies(self, health_service):
        """Test getting system health with no dependencies"""
        health = await health_service.get_system_health(use_cache=False)

        assert isinstance(health, SystemHealth)
        assert health.overall_status == HealthStatus.HEALTHY
        assert health.version == "1.0.0"
        assert health.environment == "test"
        assert len(health.components) == 4  # db, broker, cache, event_store
        assert health.metrics["component_count"] == 4
        assert health.metrics["healthy_count"] == 4

    @pytest.mark.asyncio
    async def test_system_health_caching(self, health_service):
        """Test system health caching behavior"""
        # First call should compute health
        health1 = await health_service.get_system_health(use_cache=False)

        # Second call with cache=True should return cached result
        health2 = await health_service.get_system_health(use_cache=True)

        assert health1.timestamp == health2.timestamp

        # Call with use_cache=False should recompute
        await asyncio.sleep(0.1)
        health3 = await health_service.get_system_health(use_cache=False)

        assert health3.timestamp > health2.timestamp

    @pytest.mark.asyncio
    async def test_wait_for_ready(self, health_service):
        """Test waiting for system to be ready"""
        # System should be ready immediately with no dependencies
        ready = await health_service.wait_for_ready(
            max_retries=3, retry_delay_seconds=0.1
        )
        assert ready is True


class TestSystemHealth:
    """Test SystemHealth model"""

    def test_system_health_creation(self):
        """Test creating system health"""
        components = [
            ComponentHealth("comp1", HealthStatus.HEALTHY, 10.0, "OK"),
            ComponentHealth("comp2", HealthStatus.DEGRADED, 50.0, "Slow"),
        ]
        dependencies = {"comp1": HealthStatus.HEALTHY, "comp2": HealthStatus.DEGRADED}

        health = SystemHealth(
            overall_status=HealthStatus.DEGRADED,
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="test",
            components=components,
            dependencies=dependencies,
        )

        assert health.overall_status == HealthStatus.DEGRADED
        assert health.version == "1.0.0"
        assert health.environment == "test"
        assert len(health.components) == 2
        assert len(health.dependencies) == 2

    def test_is_ready_with_healthy_system(self):
        """Test readiness check for healthy system"""
        health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="test",
            components=[],
            dependencies={"db": HealthStatus.HEALTHY},
        )

        assert health.is_ready() is True

    def test_is_ready_with_unhealthy_dependency(self):
        """Test readiness check with unhealthy dependency"""
        health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="test",
            components=[],
            dependencies={"db": HealthStatus.UNHEALTHY},
        )

        assert health.is_ready() is False

    def test_is_alive(self):
        """Test aliveness check"""
        healthy = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="test",
            components=[],
            dependencies={},
        )

        unhealthy = SystemHealth(
            overall_status=HealthStatus.UNHEALTHY,
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="test",
            components=[],
            dependencies={},
        )

        assert healthy.is_alive() is True
        assert unhealthy.is_alive() is False

    def test_to_dict(self):
        """Test converting system health to dictionary"""
        components = [ComponentHealth("comp1", HealthStatus.HEALTHY, 10.0, "OK")]
        health = SystemHealth(
            overall_status=HealthStatus.HEALTHY,
            timestamp="2023-01-01T00:00:00Z",
            version="1.0.0",
            environment="test",
            components=components,
            dependencies={},
        )

        result = health.to_dict()

        assert result["overall_status"] == "healthy"
        assert result["version"] == "1.0.0"
        assert result["environment"] == "test"
        assert result["is_ready"] is True
        assert result["is_alive"] is True
        assert len(result["components"]) == 1
        assert result["dependencies"] == {}
