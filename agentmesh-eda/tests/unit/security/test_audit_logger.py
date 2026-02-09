"""
Audit Logger Module Tests

Tests for the audit logging functionality including
immutable audit logging, sensitive action detection, and audit trail integrity.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from agentmesh.infrastructure.security.audit_logger import (
    AuditLogger,
    AuditLogEntry,
    AuditAction,
    AuditStatus,
)


class MockAuditStore:
    """Mock implementation of audit store for testing"""

    def __init__(self):
        self.entries = []
        self.corrupted = False
        self.next_id = 1

    async def append(self, entry: AuditLogEntry) -> str:
        if self.corrupted:
            raise Exception("Store corrupted")
        entry_id = f"entry_{self.next_id}"
        self.next_id += 1
        self.entries.append(entry)
        return entry_id

    async def query(self, query) -> List[AuditLogEntry]:
        return [e for e in self.entries if self._matches_query(e, query)]

    async def get_by_id(self, entry_id: str) -> AuditLogEntry:
        for i, entry in enumerate(self.entries):
            if f"entry_{i + 1}" == entry_id:
                return entry
        return None

    async def get_by_request_id(self, request_id: str) -> List[AuditLogEntry]:
        return [e for e in self.entries if e.request_id == request_id]

    async def get_actor_history(
        self, tenant_id: str, actor_id: str, limit: int = 100
    ) -> List[AuditLogEntry]:
        return [
            e
            for e in self.entries
            if e.tenant_id == tenant_id and e.actor_id == actor_id
        ][:limit]

    async def get_resource_history(
        self, tenant_id: str, resource_id: str, limit: int = 100
    ) -> List[AuditLogEntry]:
        return [
            e
            for e in self.entries
            if e.tenant_id == tenant_id and e.resource_id == resource_id
        ][:limit]

    async def export_range(self, tenant_id: str, start_date, end_date) -> bytes:
        filtered = [e for e in self.entries if e.tenant_id == tenant_id]
        return b"export_data"

    async def verify_integrity(self) -> bool:
        return not self.corrupted

    def _matches_query(self, entry: AuditLogEntry, query) -> bool:
        if hasattr(query, "tenant_id") and entry.tenant_id != query.tenant_id:
            return False
        if (
            hasattr(query, "actor_id")
            and query.actor_id
            and entry.actor_id != query.actor_id
        ):
            return False
        if hasattr(query, "action") and query.action and entry.action != query.action:
            return False
        return True


class TestAuditLogEntry:
    """Test AuditLogEntry model"""

    def test_audit_entry_creation(self):
        """Test creating an audit entry"""
        entry = AuditLogEntry(
            action=AuditAction.AUTH_SUCCESS,
            actor_id="user123",
            actor_type="user",
            resource_id="/api/login",
            resource_type="endpoint",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            timestamp=datetime.now().isoformat(),
            request_id="req123",
        )

        assert entry.action == AuditAction.AUTH_SUCCESS
        assert entry.actor_id == "user123"
        assert entry.actor_type == "user"
        assert entry.resource_id == "/api/login"
        assert entry.resource_type == "endpoint"
        assert entry.status == AuditStatus.SUCCESS
        assert entry.tenant_id == "tenant1"
        assert entry.request_id == "req123"
        assert entry.is_sensitive is False
        assert entry.details == {}

    def test_sensitive_entry_creation(self):
        """Test creating a sensitive audit entry"""
        entry = AuditLogEntry(
            action=AuditAction.SECRET_ACCESSED,
            actor_id="admin123",
            actor_type="user",
            resource_id="secret_key",
            resource_type="secret",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            timestamp=datetime.now().isoformat(),
            request_id="req456",
            is_sensitive=True,
            data_classification="confidential",
        )

        assert entry.is_sensitive is True
        assert entry.data_classification == "confidential"

    def test_entry_to_dict(self):
        """Test converting audit entry to dictionary"""
        entry = AuditLogEntry(
            action=AuditAction.AGENT_CREATED,
            actor_id="service123",
            actor_type="service",
            resource_id="agent456",
            resource_type="agent",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            timestamp="2023-01-01T00:00:00Z",
            request_id="req789",
        )

        result = entry.to_dict()

        assert result["action"] == "agent_created"
        assert result["actor_id"] == "service123"
        assert result["resource_id"] == "agent456"
        assert result["status"] == "success"
        assert result["tenant_id"] == "tenant1"

    def test_entry_to_json(self):
        """Test converting audit entry to JSON"""
        entry = AuditLogEntry(
            action=AuditAction.TASK_COMPLETED,
            actor_id="agent123",
            actor_type="agent",
            resource_id="task456",
            resource_type="task",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            timestamp="2023-01-01T00:00:00Z",
            request_id="req111",
        )

        json_str = entry.to_json()

        assert "task_completed" in json_str
        assert "agent123" in json_str
        assert "task456" in json_str


class TestAuditLogger:
    """Test AuditLogger functionality"""

    @pytest.fixture
    def mock_store(self):
        """Create a mock audit store"""
        return MockAuditStore()

    @pytest.fixture
    def audit_logger(self, mock_store):
        """Create an audit logger with mock store"""
        return AuditLogger(audit_store=mock_store)

    def test_audit_logger_initialization(self, mock_store):
        """Test audit logger initialization"""
        logger = AuditLogger(audit_store=mock_store)
        assert logger.store == mock_store
        assert logger.logger is not None

    @pytest.mark.asyncio
    async def test_log_basic_action(self, audit_logger, mock_store):
        """Test logging a basic audit action"""
        entry = await audit_logger.log_action(
            action=AuditAction.AUTH_SUCCESS,
            actor_id="user123",
            actor_type="user",
            resource_id="/api/login",
            resource_type="endpoint",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req123",
        )

        assert len(mock_store.entries) == 1
        assert mock_store.entries[0] == entry
        assert entry.action == AuditAction.AUTH_SUCCESS
        assert entry.actor_id == "user123"
        assert entry.status == AuditStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_log_action_with_details(self, audit_logger, mock_store):
        """Test logging an action with additional details"""
        details = {
            "method": "POST",
            "response_time_ms": 150,
            "user_agent": "Mozilla/5.0",
        }

        entry = await audit_logger.log_action(
            action=AuditAction.MESSAGE_ROUTED,
            actor_id="service123",
            actor_type="service",
            resource_id="message456",
            resource_type="message",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req456",
            source_ip="192.168.1.1",
            result_message="Message routed successfully",
            details=details,
        )

        assert entry.details == details
        assert entry.source_ip == "192.168.1.1"
        assert entry.result_message == "Message routed successfully"

    @pytest.mark.asyncio
    async def test_log_sensitive_action(self, audit_logger, mock_store):
        """Test logging a sensitive action"""
        entry = await audit_logger.log_action(
            action=AuditAction.SECRET_ACCESSED,
            actor_id="admin123",
            actor_type="user",
            resource_id="db_password",
            resource_type="secret",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req789",
            is_sensitive=True,
            details={"data_classification": "restricted"},
        )

        assert entry.is_sensitive is True
        assert entry.data_classification == "restricted"

    @pytest.mark.asyncio
    async def test_log_failed_action(self, audit_logger, mock_store):
        """Test logging a failed action"""
        entry = await audit_logger.log_action(
            action=AuditAction.AUTH_FAILURE,
            actor_id="user123",
            actor_type="user",
            resource_id="/api/login",
            resource_type="endpoint",
            status=AuditStatus.FAILURE,
            tenant_id="tenant1",
            request_id="req999",
            result_message="Authentication failed",
            error_details="Invalid credentials",
        )

        assert entry.status == AuditStatus.FAILURE
        assert entry.error_details == "Invalid credentials"
        assert entry.result_message == "Authentication failed"

    @pytest.mark.asyncio
    async def test_log_agent_lifecycle_actions(self, audit_logger, mock_store):
        """Test logging agent lifecycle actions"""
        # Create agent
        create_entry = await audit_logger.log_action(
            action=AuditAction.AGENT_CREATED,
            actor_id="admin123",
            actor_type="user",
            resource_id="agent456",
            resource_type="agent",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req001",
        )

        # Update agent
        update_entry = await audit_logger.log_action(
            action=AuditAction.AGENT_UPDATED,
            actor_id="admin123",
            actor_type="user",
            resource_id="agent456",
            resource_type="agent",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req002",
        )

        # Terminate agent
        terminate_entry = await audit_logger.log_action(
            action=AuditAction.AGENT_TERMINATED,
            actor_id="admin123",
            actor_type="user",
            resource_id="agent456",
            resource_type="agent",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req003",
        )

        assert len(mock_store.entries) == 3
        assert mock_store.entries[0].action == AuditAction.AGENT_CREATED
        assert mock_store.entries[1].action == AuditAction.AGENT_UPDATED
        assert mock_store.entries[2].action == AuditAction.AGENT_TERMINATED

    @pytest.mark.asyncio
    async def test_log_task_operations(self, audit_logger, mock_store):
        """Test logging task operations"""
        # Assign task
        assign_entry = await audit_logger.log_action(
            action=AuditAction.TASK_ASSIGNED,
            actor_id="scheduler123",
            actor_type="service",
            resource_id="task789",
            resource_type="task",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req111",
            details={"agent_id": "agent456", "priority": "high"},
        )

        # Complete task
        complete_entry = await audit_logger.log_action(
            action=AuditAction.TASK_COMPLETED,
            actor_id="agent456",
            actor_type="agent",
            resource_id="task789",
            resource_type="task",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req111",
            details={"execution_time_ms": 250, "result": "success"},
        )

        assert len(mock_store.entries) == 2
        assert mock_store.entries[0].action == AuditAction.TASK_ASSIGNED
        assert mock_store.entries[1].action == AuditAction.TASK_COMPLETED

    @pytest.mark.asyncio
    async def test_immutable_entries(self, audit_logger):
        """Test that audit log entries are immutable"""
        entry = await audit_logger.log_action(
            action=AuditAction.AUTH_SUCCESS,
            actor_id="user123",
            actor_type="user",
            resource_id="/api/login",
            resource_type="endpoint",
            status=AuditStatus.SUCCESS,
            tenant_id="tenant1",
            request_id="req123",
        )

        # Attempting to modify should fail due to frozen dataclass
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            entry.actor_id = "user456"

    @pytest.mark.asyncio
    async def test_concurrent_logging(self, audit_logger, mock_store):
        """Test concurrent logging of multiple actions"""

        async def log_actions(user_id: str, count: int):
            for i in range(count):
                await audit_logger.log_action(
                    action=AuditAction.MESSAGE_ROUTED,
                    actor_id=user_id,
                    actor_type="user",
                    resource_id=f"message_{i}",
                    resource_type="message",
                    status=AuditStatus.SUCCESS,
                    tenant_id="tenant1",
                    request_id=f"req_{user_id}_{i}",
                )

        # Log actions concurrently
        await asyncio.gather(
            log_actions("user1", 3), log_actions("user2", 2), log_actions("user3", 4)
        )

        # Verify all actions were logged
        assert len(mock_store.entries) == 9

        # Verify actions are properly attributed
        user1_actions = [e for e in mock_store.entries if e.actor_id == "user1"]
        user2_actions = [e for e in mock_store.entries if e.actor_id == "user2"]
        user3_actions = [e for e in mock_store.entries if e.actor_id == "user3"]

        assert len(user1_actions) == 3
        assert len(user2_actions) == 2
        assert len(user3_actions) == 4


class TestAuditAction:
    """Test AuditAction enum"""

    def test_agent_actions(self):
        """Test agent-related actions"""
        assert hasattr(AuditAction, "AGENT_CREATED")
        assert hasattr(AuditAction, "AGENT_UPDATED")
        assert hasattr(AuditAction, "AGENT_TERMINATED")
        assert hasattr(AuditAction, "AGENT_RESTARTED")

    def test_task_actions(self):
        """Test task-related actions"""
        assert hasattr(AuditAction, "TASK_ASSIGNED")
        assert hasattr(AuditAction, "TASK_COMPLETED")
        assert hasattr(AuditAction, "TASK_FAILED")
        assert hasattr(AuditAction, "TASK_CANCELLED")

    def test_security_actions(self):
        """Test security-related actions"""
        assert hasattr(AuditAction, "AUTH_SUCCESS")
        assert hasattr(AuditAction, "AUTH_FAILURE")
        assert hasattr(AuditAction, "UNAUTHORIZED_ACCESS")
        assert hasattr(AuditAction, "SECRET_ACCESSED")

    def test_action_values(self):
        """Test action enum values"""
        assert AuditAction.AUTH_SUCCESS.value == "auth_success"
        assert AuditAction.AGENT_CREATED.value == "agent_created"
        assert AuditAction.TASK_COMPLETED.value == "task_completed"


class TestAuditStatus:
    """Test AuditStatus enum"""

    def test_status_values(self):
        """Test status enum values"""
        assert AuditStatus.SUCCESS.value == "success"
        assert AuditStatus.FAILURE.value == "failure"
        assert AuditStatus.DENIED.value == "denied"
        assert AuditStatus.TIMEOUT.value == "timeout"
        assert AuditStatus.UNKNOWN.value == "unknown"

    def test_status_members(self):
        """Test all expected status members exist"""
        expected_statuses = ["SUCCESS", "FAILURE", "DENIED", "TIMEOUT", "UNKNOWN"]
        for status in expected_statuses:
            assert hasattr(AuditStatus, status)
