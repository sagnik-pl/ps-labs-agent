"""
FastAPI endpoint for the Photosphere Labs Agent System.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from agents.supervisor_agent import SupervisorAgent
from utils.firebase_client import firebase_client
import uuid
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Photosphere Labs Agent API", version="1.0.0")

# Initialize supervisor agent
supervisor = SupervisorAgent(use_anthropic=True)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    user_id: str
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str
    conversation_id: str
    agent_used: Optional[str] = None
    routing_decision: Optional[dict] = None


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Photosphere Labs Agent API"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Process a user chat message and return agent response.

    Args:
        request: Chat request with user_id, message, and optional conversation_id

    Returns:
        ChatResponse with agent's response and metadata
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Get conversation context from Firestore
        try:
            context = firebase_client.get_context_summary(
                request.user_id, conversation_id
            )
        except Exception as e:
            print(f"Warning: Could not load context: {e}")
            context = ""

        # Save user message to Firestore
        try:
            firebase_client.save_message(
                request.user_id, conversation_id, "user", request.message
            )
        except Exception as e:
            print(f"Warning: Could not save user message: {e}")

        # Process query with supervisor agent
        result = supervisor.process_query(request.message, request.user_id, context)

        # Save agent response to Firestore
        try:
            firebase_client.save_message(
                request.user_id,
                conversation_id,
                "assistant",
                result["response"],
                metadata=result.get("routing_decision"),
            )
        except Exception as e:
            print(f"Warning: Could not save agent response: {e}")

        return ChatResponse(
            response=result["response"],
            conversation_id=conversation_id,
            agent_used=result.get("agent_used"),
            routing_decision=result.get("routing_decision"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with progress streaming.

    Accepts JSON messages:
    {
        "user_id": "...",
        "message": "...",
        "conversation_id": "..."  # optional
    }

    Sends progress updates:
    {
        "type": "progress",
        "stage": "planning|routing|executing|interpreting|formatting",
        "message": "Status message..."
    }

    Sends final response:
    {
        "type": "response",
        "content": "Full response...",
        "conversation_id": "...",
        "metadata": {...}
    }
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            logger.info(f"Received WebSocket message for user {data.get('user_id', 'unknown')[:8]}...")

            user_id = data.get("user_id")
            message = data.get("message")
            conversation_id = data.get("conversation_id") or str(uuid.uuid4())

            if not user_id or not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Missing required fields: user_id and message"
                })
                continue

            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "conversation_id": conversation_id
            })

            try:
                # Send progress: Loading context
                await websocket.send_json({
                    "type": "progress",
                    "stage": "initializing",
                    "message": "Loading conversation context..."
                })

                # Get context
                try:
                    context = firebase_client.get_context_summary(user_id, conversation_id)
                except Exception as e:
                    logger.warning(f"Could not load context: {e}")
                    context = ""

                # Save user message
                try:
                    firebase_client.save_message(user_id, conversation_id, "user", message)
                except Exception as e:
                    logger.warning(f"Could not save user message: {e}")

                # Send progress: Analyzing query
                await websocket.send_json({
                    "type": "progress",
                    "stage": "routing",
                    "message": "Analyzing your query..."
                })

                # Process query
                result = supervisor.process_query(message, user_id, context)

                # Save agent response
                try:
                    firebase_client.save_message(
                        user_id,
                        conversation_id,
                        "assistant",
                        result["response"],
                        metadata=result.get("routing_decision")
                    )
                except Exception as e:
                    logger.warning(f"Could not save agent response: {e}")

                # Send final response
                await websocket.send_json({
                    "type": "response",
                    "content": result["response"],
                    "conversation_id": conversation_id,
                    "metadata": {
                        "agent_used": result.get("agent_used"),
                        "routing_decision": result.get("routing_decision")
                    }
                })

                # Send completion signal
                await websocket.send_json({
                    "type": "complete",
                    "conversation_id": conversation_id
                })

                logger.info(f"WebSocket request completed for user {user_id[:8]}...")

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass  # Connection may already be closed


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
