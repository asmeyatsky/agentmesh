from loguru import logger
from agentmesh.aol.simple_agent import SimpleAgent
from agentmesh.mal.message import UniversalMessage
from agentmesh.cqrs.event import TaskAssigned
from agentmesh.mal.adapters.base import MessagePlatformAdapter


class TaskExecutorAgent(SimpleAgent):
    def __init__(
        self, id: str, capabilities: list[str], adapter: MessagePlatformAdapter
    ):
        super().__init__(id, capabilities, adapter)
        self.subscription_topic = f"agent.task_executor.{self.id}.commands"

    async def process_message(self, message: UniversalMessage):
        logger.info(f"TaskExecutorAgent {self.id} received message: {message.payload}")
        try:
            # Assuming the payload directly contains the event data
            event_data = message.payload
            if event_data.get("event_type") == "TaskAssigned":
                task_assigned_event = TaskAssigned(
                    event_id=event_data["event_id"],
                    created_at=event_data["created_at"],
                    task_id=event_data["task_id"],
                    agent_id=event_data["agent_id"],
                    task_details=event_data["task_details"],
                )
                logger.info(
                    f"TaskExecutorAgent {self.id} executing task: {task_assigned_event.task_id} "
                    f"for agent {task_assigned_event.agent_id} with details: {task_assigned_event.task_details}"
                )
                # Here, the agent would perform the actual task execution
            else:
                logger.warning(
                    f"TaskExecutorAgent {self.id} received unknown event type: {event_data.get("event_type")}"
                )
        except KeyError as e:
            logger.error(f"TaskExecutorAgent {self.id} missing key in payload: {e}")
