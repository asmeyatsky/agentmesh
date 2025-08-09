import pytest
import asyncio
from unittest.mock import patch, MagicMock
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.adapters.base import MessagePlatformAdapter


class MockAdapter(MessagePlatformAdapter):
    def __init__(self):
        self.sent_messages = []

    async def send(self, message: UniversalMessage, target: str):
        self.sent_messages.append((message, target))
        await asyncio.sleep(0)

    async def consume(self, subscription: str):
        pass


@pytest.mark.asyncio
async def test_message_router(valid_token):
    with patch("agentmesh.mal.router.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        router = MessageRouter()
        mock_adapter = MockAdapter()
        router.add_adapter("mock", mock_adapter)

        message = UniversalMessage(
            routing={"targets": ["mock:test_topic"]}, metadata={"token": valid_token}
        )
        await router.route_message(message)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_session.close.assert_called_once()

        assert len(mock_adapter.sent_messages) == 1
        sent_message, target = mock_adapter.sent_messages[0]
        assert sent_message == message
        assert target == "test_topic"
