from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from loguru import logger
import asyncio

from agentmesh.mal.message import UniversalMessage
from agentmesh.mal.router import MessageRouter
from agentmesh.mal.adapters.nats import NATSAdapter
from agentmesh.security.auth import verify_access_token
from agentmesh.aol.registry import AgentRegistry # New import
from agentmesh.aol.coordinator import AgentCoordinator # New import
from agentmesh.cqrs.bus import CqrsBus # New import
from agentmesh.cqrs.query import GetAgentStatusQuery # New import
from agentmesh.cqrs.query_handler import GetAgentStatusQueryHandler # New import
from agentmesh.cqrs.read_model import AgentStatusReadModel # New import


app = FastAPI(title="AgentMesh EDA API Gateway")

# Initialize core components
nats_adapter = NATSAdapter()
message_router = MessageRouter()
message_router.add_adapter("nats", nats_adapter)

agent_registry = AgentRegistry() # New
agent_coordinator = AgentCoordinator(registry=agent_registry, router=message_router) # New

cqrs_bus = CqrsBus() # New
agent_status_read_model = AgentStatusReadModel() # New
cqrs_bus.register_query_handler(GetAgentStatusQuery, GetAgentStatusQueryHandler(agent_status_read_model)) # New

class MessagePayload(BaseModel):
    tenant_id: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    routing: Dict[str, Any] = {}

class SubmitTaskPayload(BaseModel): # New
    workflow_type: str
    workflow_data: Dict[str, Any]
    tenant_id: str

class GetAgentStatusPayload(BaseModel): # New
    agent_id: str
    tenant_id: str

async def get_current_user(request: Request):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise credentials_exception
    token = token.split(" ")[1]
    user = verify_access_token(token, credentials_exception)
    return user

@app.post("/publish")
async def publish_message(msg_payload: MessagePayload, current_user: Dict[str, Any] = Depends(get_current_user)):
    logger.info(f"Received message for publishing from user: {current_user.get("sub")}")
    # Ensure the tenant_id in the payload matches the user's tenant_id from the token
    if current_user.get("tenant_id") != msg_payload.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID mismatch or unauthorized")

    universal_message = UniversalMessage(
        tenant_id=msg_payload.tenant_id,
        payload=msg_payload.payload,
        metadata={**msg_payload.metadata, "source_api": "api_gateway", "token": request.headers.get("Authorization")},
        routing=msg_payload.routing
    )

    try:
        await message_router.route_message(universal_message)
        return {"status": "success", "message_id": universal_message.metadata.get("id")}
    except Exception as e:
        logger.error(f"Error routing message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish message: {e}")

@app.post("/submit_task") # New endpoint
async def submit_task(task_payload: SubmitTaskPayload, current_user: Dict[str, Any] = Depends(get_current_user)):
    logger.info(f"Received task submission for workflow {task_payload.workflow_type} from user: {current_user.get("sub")}")
    if current_user.get("tenant_id") != task_payload.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID mismatch or unauthorized")

    try:
        # Pass the original Authorization token to the coordinator for internal routing
        token = Depends(get_current_user) # This is not how it works, need to pass the actual token string
        # Correct way to get the token string from the request
        request = Depends(Request)
        auth_header = request.headers.get("Authorization")
        token_string = auth_header.split(" ")[1] if auth_header and auth_header.startswith("Bearer ") else None

        await agent_coordinator.execute_workflow(
            workflow_type=task_payload.workflow_type,
            workflow_data=task_payload.workflow_data,
            token=token_string,
            tenant_id=task_payload.tenant_id
        )
        return {"status": "success", "message": "Task submitted successfully"}
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")

@app.get("/agent_status") # New endpoint
async def get_agent_status(agent_id: str, tenant_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    logger.info(f"Received agent status request for agent {agent_id} in tenant {tenant_id} from user: {current_user.get("sub")}")
    if current_user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID mismatch or unauthorized")

    try:
        query = GetAgentStatusQuery(agent_id=agent_id, tenant_id=tenant_id)
        status = await cqrs_bus.dispatch_query(query)
        return {"status": "success", "data": status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
