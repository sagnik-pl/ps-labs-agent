"""
WebSocket API for real-time chat interface.

This API provides WebSocket endpoints for the chat interface,
streaming progress updates and results in real-time.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set
import json
import uuid
from datetime import datetime, timezone
import logging

from workflow import create_agent_workflow
from workflow.progress import ProgressEvent, get_progress_message
from langchain_core.messages import HumanMessage
from utils.firebase_client import firebase_client
from utils.title_generator import generate_conversation_title

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Photosphere Labs Agent API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id[:12]}...")

    def disconnect(self, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id[:12]}...")

    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

    async def send_progress(self, session_id: str, node_name: str, retry_count: int = 0):
        """Send progress update."""
        event = ProgressEvent.progress(node_name, retry_count)
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        await self.send_message(session_id, event)

    async def send_completed(self, session_id: str, response: str, metadata: dict = None):
        """Send completion message."""
        event = ProgressEvent.completed(response, metadata)
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        await self.send_message(session_id, event)

    async def send_error(self, session_id: str, error: str, details: str = None):
        """Send error message."""
        event = ProgressEvent.error(error, details)
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        await self.send_message(session_id, event)


manager = ConnectionManager()


@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    """
    WebSocket endpoint for chat interface.

    Args:
        user_id: User ID for authentication
        session_id: Unique session/conversation ID
    """
    await manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type", "query")  # Default to "query" if type not specified

            if message_type == "query":
                # User sent a query
                query = data.get("query")
                conversation_id = data.get("conversation_id", session_id)

                if not query:
                    logger.warning("No query provided in message")
                    continue

                logger.info(f"Processing query: '{query[:60]}...'")  # Truncate for logs

                # Send started event
                await manager.send_message(
                    session_id,
                    {
                        **ProgressEvent.started(query),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )

                # Process query with workflow
                await process_query_with_progress(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    query=query,
                    session_id=session_id
                )

            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.send_error(session_id, str(e))
        manager.disconnect(session_id)


async def process_query_with_progress(
    user_id: str,
    conversation_id: str,
    query: str,
    session_id: str
):
    """
    Process query and stream progress updates via WebSocket.

    Args:
        user_id: User ID
        conversation_id: Conversation ID
        query: User's query
        session_id: WebSocket session ID
    """
    try:
        # Check if this is a new conversation
        is_new = firebase_client.is_new_conversation(user_id, conversation_id)

        # Generate title for new conversations
        conversation_title = None
        if is_new:
            try:
                conversation_title = generate_conversation_title(query)
                logger.info(f"Generated conversation title: '{conversation_title}'")

                # Send conversation metadata to frontend
                current_date = datetime.now(timezone.utc).strftime("%Y/%m/%d")
                await manager.send_message(
                    session_id,
                    {
                        **ProgressEvent.conversation_metadata(
                            conversation_title,
                            current_date,
                            conversation_id
                        ),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            except Exception as e:
                logger.warning(f"Could not generate conversation title: {e}")

        # Get conversation context from Firestore
        try:
            context = firebase_client.get_context_summary(user_id, conversation_id)
        except Exception:
            context = ""

        # Save user message to Firestore (with title if new conversation)
        try:
            firebase_client.save_message(
                user_id,
                conversation_id,
                "user",
                query,
                title=conversation_title
            )
        except Exception as e:
            logger.warning(f"Could not save message to Firestore: {e}")

        # Prepare state
        initial_state = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "query": query,
            "context": context,
            "messages": [HumanMessage(content=query)],
            "agent_results": {},
            "metadata": {},
            "needs_retry": False,
            "retry_count": 0,
            "interpretation_retry_count": 0,
            "sql_retry_count": 0,
        }

        # Create workflow
        workflow = create_agent_workflow()

        # Configure checkpointing
        config = {
            "configurable": {
                "thread_id": conversation_id
            }
        }

        # Stream execution with real-time progress updates
        final_result = None

        try:
            # Stream workflow execution and send progress for each node
            async for event in workflow.astream(initial_state, config=config):
                # event is a dict with node_name as key and state as value
                for node_name, node_output in event.items():
                    # Skip special nodes
                    if node_name.startswith("__"):
                        continue

                    # Send progress update for this node
                    retry_count = 0
                    if "sql_retry_count" in node_output:
                        retry_count = node_output.get("sql_retry_count", 0)
                    elif "interpretation_retry_count" in node_output:
                        retry_count = node_output.get("interpretation_retry_count", 0)

                    await manager.send_progress(session_id, node_name, retry_count)

                    # Store the latest result
                    final_result = node_output

            # Use the final result from the last node
            result = final_result if final_result else {}

        except Exception as stream_error:
            logger.error(f"Error during workflow streaming: {stream_error}")
            raise

        # Send final result
        final_response = result.get("final_response", "No response generated")
        metadata = result.get("metadata", {})

        await manager.send_completed(session_id, final_response, metadata)

        # Save response to Firestore
        try:
            firebase_client.save_message(
                user_id,
                conversation_id,
                "assistant",
                final_response,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Could not save response to Firestore: {e}")

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        import traceback
        await manager.send_error(
            session_id,
            str(e),
            traceback.format_exc()
        )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Photosphere Labs Agent API",
        "version": "1.0.0"
    }


@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str):
    """
    Get all conversations for a user.

    Args:
        user_id: User ID

    Returns:
        List of conversations with metadata
    """
    try:
        conversations = firebase_client.get_conversations(user_id)
        return {
            "user_id": user_id,
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        logger.error(f"Error fetching conversations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{user_id}/{conversation_id}/messages")
async def get_messages(user_id: str, conversation_id: str, limit: int = 50):
    """
    Get all messages in a conversation.

    Args:
        user_id: User ID
        conversation_id: Conversation ID
        limit: Maximum number of messages to return (default: 50)

    Returns:
        List of messages with metadata
    """
    try:
        messages = firebase_client.get_conversation_messages(
            user_id,
            conversation_id,
            limit=limit
        )
        return {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Error fetching messages for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
