import pytest
from unittest.mock import MagicMock
from agentmesh.mal.adapters.snssqs import SNSSQSAdapter
from agentmesh.mal.message import UniversalMessage


@pytest.fixture
def mock_boto3_client():
    return MagicMock()


@pytest.mark.asyncio
async def test_snssqs_adapter_send_sns(mock_boto3_client):
    adapter = SNSSQSAdapter(region_name="us-east-1")
    adapter.sns = mock_boto3_client

    message = UniversalMessage(payload={"test": "message"})
    await adapter.send(message, "arn:aws:sns:us-east-1:123456789012:test-topic")

    mock_boto3_client.publish.assert_called_once()


@pytest.mark.asyncio
async def test_snssqs_adapter_send_sqs(mock_boto3_client):
    adapter = SNSSQSAdapter(region_name="us-east-1")
    adapter.sqs = mock_boto3_client

    message = UniversalMessage(payload={"test": "message"})
    await adapter.send(
        message, "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
    )

    mock_boto3_client.send_message.assert_called_once()
