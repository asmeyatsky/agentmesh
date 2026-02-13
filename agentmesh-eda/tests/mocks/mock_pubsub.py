"""
Mock Google Cloud Pub/Sub implementation for testing

This provides a mock implementation when google.cloud is not available
in the test environment.
"""

from typing import Any, Dict, List, Optional, Callable
from unittest.mock import MagicMock
import asyncio


class MockPublisherClient:
    """Mock Pub/Sub publisher client"""

    def __init__(self, *args, **kwargs):
        self.topics = {}
        self.published_messages = []

    def topic_path(self, project_id: str, topic_id: str) -> str:
        return f"projects/{project_id}/topics/{topic_id}"

    def publish(self, topic_path: str, data: bytes, **kwargs) -> MagicMock:
        """Mock publish method"""
        mock_future = MagicMock()
        mock_future.result.return_value = "mock-message-id"

        self.published_messages.append(
            {"topic": topic_path, "data": data, "kwargs": kwargs}
        )

        return mock_future


class MockSubscriberClient:
    """Mock Pub/Sub subscriber client"""

    def __init__(self, *args, **kwargs):
        self.subscriptions = {}
        self.pull_responses = []

    def subscription_path(self, project_id: str, subscription_id: str) -> str:
        return f"projects/{project_id}/subscriptions/{subscription_id}"

    def pull(self, subscription_path: str, **kwargs) -> MagicMock:
        """Mock pull method"""
        mock_response = MagicMock()
        mock_response.received_messages = self.pull_responses or []
        return mock_response

    def acknowledge(self, subscription_path: str, ack_ids: List[str]):
        """Mock acknowledge method"""
        pass

    def modify_ack_deadline(
        self, subscription_path: str, ack_ids: List[str], ack_deadline_seconds: int
    ):
        """Mock modify_ack_deadline method"""
        pass


class MockScheduler:
    """Mock scheduler for threading"""

    def __init__(self):
        pass

    def start(self):
        pass

    def shutdown(self):
        pass


# Mock the pubsub_v1 module structure
class MockPubSubV1:
    PublisherClient = MockPublisherClient
    SubscriberClient = MockSubscriberClient
    scheduler = type("scheduler", (), {"Scheduler": MockScheduler})()


# Provide compatibility with missing imports
try:
    from google.cloud import pubsub_v1
except ImportError:
    # Use our mock implementation
    pubsub_v1 = MockPubSubV1()
