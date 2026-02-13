"""
Mock Pulsar implementation for testing

This provides a mock implementation when pulsar is not available
in the test environment.
"""

from typing import Any, Dict, List, Optional, Callable
from unittest.mock import MagicMock
import asyncio


class MockClient:
    """Mock Pulsar client"""

    def __init__(self, service_url: str, **kwargs):
        self.service_url = service_url
        self.producers = {}
        self.consumers = {}

    def create_producer(self, topic: str, **kwargs):
        """Mock create_producer"""
        producer = MockProducer(topic)
        self.producers[topic] = producer
        return producer

    def subscribe(self, topic: str, subscription_name: str, **kwargs):
        """Mock subscribe"""
        consumer = MockConsumer(topic, subscription_name)
        key = f"{topic}:{subscription_name}"
        self.consumers[key] = consumer
        return consumer

    def close(self):
        """Mock close"""
        pass


class MockProducer:
    """Mock Pulsar producer"""

    def __init__(self, topic: str):
        self.topic = topic
        self.messages = []

    def send(self, content: bytes, **kwargs):
        """Mock send"""
        message_id = MagicMock()
        message_id.result.return_value = MagicMock()
        self.messages.append(content)
        return message_id

    def close(self):
        """Mock close"""
        pass


class MockConsumer:
    """Mock Pulsar consumer"""

    def __init__(self, topic: str, subscription: str):
        self.topic = topic
        self.subscription = subscription
        self.messages = []
        self.message_queue = asyncio.Queue()

    def receive(self, timeout_millis: Optional[int] = None):
        """Mock receive"""
        try:
            return self.message_queue.get_nowait()
        except asyncio.QueueEmpty:
            raise TimeoutError("No message available")

    def acknowledge(self, msg_id):
        """Mock acknowledge"""
        pass

    def negative_acknowledge(self, msg_id):
        """Mock negative_acknowledge"""
        pass

    def close(self):
        """Mock close"""
        pass

    def add_message(self, message):
        """Helper method for testing"""
        self.message_queue.put_nowait(message)


# Mock the pulsar module structure
class MockPulsar:
    Client = MockClient


# Provide compatibility with missing imports
try:
    import pulsar
except ImportError:
    # Use our mock implementation
    pulsar = MockPulsar()
