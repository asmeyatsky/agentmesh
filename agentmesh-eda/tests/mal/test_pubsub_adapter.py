import pytest
import sys
from unittest.mock import MagicMock

# Mock the pubsub import before importing the adapter
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.pubsub_v1"] = MagicMock()

from agentmesh.mal.adapters.pubsub import PubSubAdapter
from agentmesh.mal.message import UniversalMessage


@pytest.fixture
def mock_pubsub_client():
    return MagicMock()


@pytest.mark.asyncio
async def test_pubsub_adapter_send(mock_pubsub_client):
    adapter = PubSubAdapter(project_id="test-project")
    adapter.publisher = mock_pubsub_client

    message = UniversalMessage(payload={"test": "message"})
    await adapter.send(message, "test-topic")

    mock_pubsub_client.topic_path.assert_called_with("test-project", "test-topic")
    mock_pubsub_client.publish.assert_called_once()
