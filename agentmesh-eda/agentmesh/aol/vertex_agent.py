"""
Advanced AI Agent implementation using Google Cloud Vertex AI
"""
from agentmesh.aol.agent import Agent
from agentmesh.mal.adapters.vertex_ai import VertexAIAdapter
from agentmesh.mal.message import UniversalMessage
from typing import Dict, Any, List
import asyncio
import logging

logger = logging.getLogger(__name__)

class VertexAIAgent(Agent):
    """
    Advanced agent that leverages Google Cloud Vertex AI for enhanced intelligence
    """
    
    def __init__(self, agent_id: str, capabilities: List[str], vertex_adapter: VertexAIAdapter, 
                 model_name: str = "text-bison@001"):
        super().__init__(agent_id, capabilities)
        self.vertex_adapter = vertex_adapter
        self.model_name = model_name
        self.conversation_history = []
        
    async def process_message(self, message: UniversalMessage) -> UniversalMessage:
        """
        Process incoming message using Vertex AI for enhanced understanding and response
        """
        try:
            logger.info(f"Processing message with VertexAIAgent: {message.metadata['id']}")
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": str(message.payload),
                "timestamp": message.metadata.get("timestamp")
            })
            
            # Prepare context for the AI model
            context = self._build_context(message)
            
            # Generate response using Vertex AI
            prompt = self._build_prompt(message, context)
            response = await self.vertex_adapter.generate_content(prompt)
            
            # Create response message
            response_message = UniversalMessage(
                metadata={
                    "id": f"response_{message.metadata['id']}",
                    "original_id": message.metadata["id"],
                    "timestamp": message.metadata["timestamp"],
                    "processed_by": self.id
                },
                routing={
                    "source": self.id,
                    "destination": message.routing.get("source", "unknown"),
                    "type": "response"
                },
                payload={
                    "response": response,
                    "original_request": message.payload,
                    "model_used": self.model_name,
                    "confidence": 0.95  # This would come from actual AI model
                },
                context=context,
                security={
                    "encrypted": message.security.get("encrypted", False),
                    "access_level": "standard"
                },
                tenant_id=message.tenant_id
            )
            
            # Add response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": response_message.metadata["timestamp"]
            })
            
            return response_message
            
        except Exception as e:
            logger.error(f"Error processing message in VertexAIAgent: {e}")
            # Return error message
            return UniversalMessage(
                metadata={
                    "id": f"error_{message.metadata['id']}",
                    "original_id": message.metadata["id"],
                    "timestamp": message.metadata["timestamp"],
                    "processed_by": self.id,
                    "error": str(e)
                },
                routing={
                    "source": self.id,
                    "destination": message.routing.get("source", "unknown"),
                    "type": "error"
                },
                payload={
                    "error": f"Error processing message: {str(e)}"
                },
                context={},
                security={
                    "encrypted": message.security.get("encrypted", False),
                    "access_level": "error"
                },
                tenant_id=message.tenant_id
            )
    
    def _build_context(self, message: UniversalMessage) -> Dict[str, Any]:
        """
        Build context for the AI model based on message and agent state
        """
        return {
            "agent_capabilities": self.capabilities,
            "conversation_history": self.conversation_history[-5:],  # Last 5 exchanges
            "current_request": message.payload,
            "tenant_context": message.tenant_id,
            "routing_info": message.routing,
            "timestamp": message.metadata.get("timestamp")
        }
    
    def _build_prompt(self, message: UniversalMessage, context: Dict[str, Any]) -> str:
        """
        Build a prompt for the Vertex AI model
        """
        prompt = f"""
        You are an advanced AI agent with the following capabilities: {', '.join(self.capabilities)}.
        
        Context:
        - Tenant ID: {context.get('tenant_context', 'default')}
        - Current request: {context.get('current_request', {})}
        - Previous conversation: {context.get('conversation_history', [])}
        
        Request:
        {message.payload}
        
        Please provide a comprehensive, accurate response based on your capabilities and the context provided.
        Ensure your response is structured and actionable.
        """
        
        return prompt
    
    async def start(self):
        """
        Start the Vertex AI Agent
        """
        logger.info(f"Starting Vertex AI Agent: {self.id}")
        
        # In a real implementation, this would connect to message queues/subscriptions
        # For now, we'll simulate processing with a simple loop
        while True:
            try:
                # Simulate waiting for messages
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in VertexAIAgent {self.id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying