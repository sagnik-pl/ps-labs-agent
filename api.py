"""
FastAPI endpoint for the Photosphere Labs Agent System.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.supervisor_agent import SupervisorAgent
from utils.firebase_client import firebase_client
import uuid

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


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
