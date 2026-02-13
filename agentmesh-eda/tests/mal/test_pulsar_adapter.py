import pytest
import sys
from unittest.mock import MagicMock

# Mock the pulsar import before importing the adapter
sys.modules["pulsar"] = MagicMock()

from agentmesh.mal.adapters.pulsar import PulsarAdapter
from agentmesh.mal.message import UniversalMessage


@pytest.fixture
def mock_pulsar_client():
    return MagicMock()


@pytest.mark.asyncio
async def test_pulsar_adapter_send(mock_pulsar_client):
    adapter = PulsarAdapter(service_url="pulsar://localhost:6650")
    adapter.client = mock_pulsar_client

    producer = MagicMock()
    mock_pulsar_client.create_producer.return_value = producer

    message = UniversalMessage(payload={"test": "message"})
    await adapter.send(message, "test-topic")

    mock_pulsar_client.create_producer.assert_called_with("test-topic")
    producer.send.assert_called_once()
