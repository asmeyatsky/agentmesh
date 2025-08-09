from loguru import logger
import argparse
import json
import os
import uuid
from agentmesh.db.database import SessionLocal, engine, Base, Tenant, Message, init_db

# TENANTS_FILE = "tenants.json" # No longer needed

# def get_tenants(): # No longer needed
#     if not os.path.exists(TENANTS_FILE):
#         return []
#     with open(TENANTS_FILE, "r") as f:
#         return json.load(f)

# def save_tenants(tenants): # No longer needed
#     with open(TENANTS_FILE, "w") as f:
#         json.dump(tenants, f, indent=2)


def main():
    init_db() # Initialize the database

    parser = argparse.ArgumentParser(description="AgentMesh EDA CLI Tool")
    parser.add_argument("--version", action="version", version="AgentMesh EDA 0.1.0")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Tenant command
    tenant_parser = subparsers.add_parser("tenant", help="Manage tenants")
    tenant_subparsers = tenant_parser.add_subparsers(
        dest="tenant_command", help="Tenant commands"
    )
    tenant_create_parser = tenant_subparsers.add_parser(
        "create", help="Create a new tenant"
    )
    tenant_create_parser.add_argument("name", help="Name of the tenant")
    tenant_subparsers.add_parser("list", help="List all tenants")

    # Status command
    subparsers.add_parser("status", help="View system status")

    # Message command
    message_parser = subparsers.add_parser("message", help="Inspect messages")
    message_subparsers = message_parser.add_subparsers(
        dest="message_command", help="Message commands"
    )
    message_view_parser = message_subparsers.add_parser(
        "view", help="View a message by ID"
    )
    message_view_parser.add_argument("id", help="ID of the message")

    args = parser.parse_args()

    if args.command == "tenant":
        db = SessionLocal()
        try:
            if args.tenant_command == "create":
                existing_tenant = db.query(Tenant).filter(Tenant.name == args.name).first()
                if existing_tenant:
                    logger.error(f"Tenant with name '{args.name}' already exists.")
                else:
                    new_tenant = Tenant(id=str(uuid.uuid4()), name=args.name)
                    db.add(new_tenant)
                    db.commit()
                    db.refresh(new_tenant)
                    logger.info(f"Tenant '{args.name}' created successfully.")
            elif args.tenant_command == "list":
                tenants = db.query(Tenant).all()
                if not tenants:
                    logger.info("No tenants found.")
                else:
                    for tenant in tenants:
                        print(tenant.name)
        finally:
            db.close()

    elif args.command == "status":
        # In a real application, this would check the health of the messaging system,
        # the agent registry, and other components.
        logger.info("System status: OK")
    elif args.command == "message":
        from loguru import logger
import argparse
import json
import os
import uuid
from agentmesh.db.database import SessionLocal, engine, Base, Tenant, Message, init_db
from agentmesh.aol.simple_agent import SimpleAgent
from agentmesh.mal.adapters.nats import NATSAdapter
from agentmesh.aol.registry import AgentRegistry
from agentmesh.aol.task_executor_agent import TaskExecutorAgent
from agentmesh.aol.orchestrator_agent import OrchestratorAgent
from agentmesh.mal.router import MessageRouter
from agentmesh.aol.kafka_agent import KafkaAgent
from agentmesh.mal.adapters.kafka import KafkaAdapter

# TENANTS_FILE = "tenants.json" # No longer needed

# def get_tenants(): # No longer needed
#     if not os.path.exists(TENANTS_FILE):
#         return []
#     with open(TENANTS_FILE, "r") as f:
#         return json.load(f)

# def save_tenants(tenants): # No longer needed
#     with open(TENANTS_FILE, "w") as f:
#         json.dump(tenants, f, indent=2)


def main():
    init_db() # Initialize the database

    parser = argparse.ArgumentParser(description="AgentMesh EDA CLI Tool")
    parser.add_argument("--version", action="version", version="AgentMesh EDA 0.1.0")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Tenant command
    tenant_parser = subparsers.add_parser("tenant", help="Manage tenants")
    tenant_subparsers = tenant_parser.add_subparsers(
        dest="tenant_command", help="Tenant commands"
    )
    tenant_create_parser = tenant_subparsers.add_parser(
        "create", help="Create a new tenant"
    )
    tenant_create_parser.add_argument("name", help="Name of the tenant")
    tenant_subparsers.add_parser("list", help="List all tenants")

    # Status command
    subparsers.add_parser("status", help="View system status")

    # Message command
    message_parser = subparsers.add_parser("message", help="Inspect messages")
    message_subparsers = message_parser.add_subparsers(
        dest="message_command", help="Message commands"
    )
    message_view_parser = message_subparsers.add_parser(
        "view", help="View a message by ID"
    )
    message_view_parser.add_argument("id", help="ID of the message")

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Manage agents")
    agent_subparsers = agent_parser.add_subparsers(
        dest="agent_command", help="Agent commands"
    )
    agent_start_parser = agent_subparsers.add_parser(
        "start", help="Start a simple agent"
    )
    agent_start_parser.add_argument("id", help="ID of the agent")
    agent_start_parser.add_argument(
        "--capabilities", nargs='+', help="Capabilities of the agent"
    )

    agent_task_executor_start_parser = agent_subparsers.add_parser(
        "start-task-executor", help="Start a TaskExecutorAgent"
    )
    agent_task_executor_start_parser.add_argument("id", help="ID of the agent")
    agent_task_executor_start_parser.add_argument(
        "--capabilities", nargs='+', help="Capabilities of the agent"
    )

    agent_orchestrator_start_parser = agent_subparsers.add_parser(
        "start-orchestrator", help="Start an OrchestratorAgent"
    )
    agent_orchestrator_start_parser.add_argument("id", help="ID of the agent")
    agent_orchestrator_start_parser.add_argument(
        "--capabilities", nargs='+', help="Capabilities of the agent"
    )
    agent_orchestrator_start_parser.add_argument(
        "--tenant-id", required=True, help="Tenant ID for the orchestrator"
    )
    agent_orchestrator_start_parser.add_argument(
        "--target-agent-id", required=True, help="ID of the target agent to assign tasks to"
    )
    agent_orchestrator_start_parser.add_argument(
        "--task-details", required=True, help="JSON string of task details"
    )

    agent_kafka_start_parser = agent_subparsers.add_parser(
        "start-kafka-agent", help="Start a KafkaAgent"
    )
    agent_kafka_start_parser.add_argument("id", help="ID of the agent")
    agent_kafka_start_parser.add_argument(
        "--capabilities", nargs='+', help="Capabilities of the agent"
    )

    args = parser.parse_args()

    if args.command == "tenant":
        db = SessionLocal()
        try:
            if args.tenant_command == "create":
                existing_tenant = db.query(Tenant).filter(Tenant.name == args.name).first()
                if existing_tenant:
                    logger.error(f"Tenant with name '{args.name}' already exists.")
                else:
                    new_tenant = Tenant(id=str(uuid.uuid4()), name=args.name)
                    db.add(new_tenant)
                    db.commit()
                    db.refresh(new_tenant)
                    logger.info(f"Tenant '{args.name}' created successfully.")
            elif args.tenant_command == "list":
                tenants = db.query(Tenant).all()
                if not tenants:
                    logger.info("No tenants found.")
                else:
                    for tenant in tenants:
                        print(tenant.name)
        finally:
            db.close()

    elif args.command == "status":
        # In a real application, this would check the health of the messaging system,
        # the agent registry, and other components.
        logger.info("System status: OK")
    elif args.command == "message":
        db = SessionLocal()
        try:
            if args.message_command == "view":
                message = db.query(Message).filter(Message.id == args.id).first()
                if message:
                    logger.info(f"Message ID: {message.id}")
                    logger.info(f"Tenant ID: {message.tenant_id}")
                    logger.info(f"Payload: {message.payload}")
                else:
                    logger.warning(f"Message with ID: {args.id} not found.")
        finally:
            db.close()
    elif args.command == "agent":
        if args.agent_command == "start":
            nats_adapter = NATSAdapter()
            agent = SimpleAgent(args.id, args.capabilities or [], nats_adapter)
            registry = AgentRegistry()
            registry.register_agent(agent)
            logger.info(f"Agent {agent.id} registered with capabilities: {agent.capabilities}")
            # Start the agent (this would typically be in a separate process/thread)
            import asyncio
            asyncio.run(agent.start())
        elif args.agent_command == "start-task-executor":
            nats_adapter = NATSAdapter()
            agent = TaskExecutorAgent(args.id, args.capabilities or [], nats_adapter)
            registry = AgentRegistry()
            registry.register_agent(agent)
            logger.info(f"TaskExecutorAgent {agent.id} registered with capabilities: {agent.capabilities}")
            import asyncio
            asyncio.run(agent.start())
        elif args.agent_command == "start-orchestrator":
            nats_adapter = NATSAdapter()
            router = MessageRouter() # Need a router instance
            orchestrator = OrchestratorAgent(
                args.id, args.capabilities or [], nats_adapter, router
            )
            registry = AgentRegistry()
            registry.register_agent(orchestrator)
            logger.info(f"OrchestratorAgent {orchestrator.id} registered with capabilities: {orchestrator.capabilities}")
            import asyncio
            try:
                task_details = json.loads(args.task_details)
                asyncio.run(orchestrator.assign_task(args.tenant_id, args.target_agent_id, task_details))
            except json.JSONDecodeError:
                logger.error("Invalid JSON for --task-details")
            except Exception as e:
                logger.error(f"Error assigning task: {e}")
        elif args.agent_command == "start-kafka-agent":
            kafka_adapter = KafkaAdapter() # Assuming KafkaAdapter is configured
            agent = KafkaAgent(args.id, args.capabilities or [], kafka_adapter)
            registry = AgentRegistry()
            registry.register_agent(agent)
            logger.info(f"KafkaAgent {agent.id} registered with capabilities: {agent.capabilities}")
            import asyncio
            asyncio.run(agent.start())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
