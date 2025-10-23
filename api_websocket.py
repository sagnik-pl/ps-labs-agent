"""
WebSocket API for real-time chat interface.

This API provides WebSocket endpoints for the chat interface,
streaming progress updates and results in real-time.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Set, Optional, Any
import json
import uuid
from datetime import datetime, timezone
import logging

from workflow import create_agent_workflow
from workflow.progress import ProgressEvent, get_progress_message
from langchain_core.messages import HumanMessage
from utils.firebase_client import firebase_client
from utils.title_generator import generate_conversation_title
from config.settings import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Photosphere Labs Agent API")

# CORS middleware for frontend
# Parse CORS origins from environment variable (comma-separated string)
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


# ========== Pydantic Models for Profile API ==========

class ProfileUpdate(BaseModel):
    """Model for profile update requests."""
    business_profile: Optional[Dict[str, Any]] = None
    goals: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    learned_context: Optional[Dict[str, Any]] = None


class SectionUpdate(BaseModel):
    """Model for section-specific update requests."""
    data: Dict[str, Any]


# ========== Connection Manager ==========

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
        logger.info(f"📨 [START] Processing query for user {user_id[:8]}..., conversation {conversation_id[:8]}...")
        logger.info(f"📝 Query: {query[:100]}..." if len(query) > 100 else f"📝 Query: {query}")

        # Check if this is a new conversation
        is_new = firebase_client.is_new_conversation(user_id, conversation_id)
        logger.info(f"🆕 New conversation: {is_new}")

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
            logger.info(f"📚 Loading conversation context from Firestore...")
            context = firebase_client.get_context_summary(user_id, conversation_id)
            logger.info(f"✅ Context loaded: {len(context)} characters")
        except Exception as e:
            logger.warning(f"⚠️ Could not load context: {e}")
            context = ""

        # Get user profile from Firestore
        try:
            logger.info(f"👤 Loading user profile from Firestore...")
            user_profile = firebase_client.get_user_profile(user_id)
            logger.info(f"✅ User profile loaded: {user_profile.get('business_name', 'N/A') if user_profile else 'None'}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load user profile: {e}")
            user_profile = None

        # Save user message to Firestore (with title if new conversation)
        try:
            logger.info(f"💾 Saving user message to Firestore...")
            firebase_client.save_message(
                user_id,
                conversation_id,
                "user",
                query,
                title=conversation_title
            )
            logger.info(f"✅ User message saved successfully")
        except Exception as e:
            logger.warning(f"❌ Could not save user message to Firestore: {e}")

        # Prepare state
        initial_state = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "user_profile": user_profile,
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
            logger.info(f"🚀 Starting workflow execution...")
            # Stream workflow execution and send progress for each node
            async for event in workflow.astream(initial_state, config=config):
                # Validate event is a dict
                if not isinstance(event, dict):
                    logger.warning(f"Received non-dict event: {type(event)} = {event}")
                    continue

                # event is a dict with node_name as key and state as value
                for node_name, node_output in event.items():
                    # Skip special nodes
                    if node_name.startswith("__"):
                        # For __end__ node, store the final state
                        if node_name == "__end__" and isinstance(node_output, dict):
                            final_result = node_output
                        continue

                    # Validate node_output is a dict
                    if not isinstance(node_output, dict):
                        logger.warning(f"Node {node_name} returned non-dict output: {type(node_output)}")
                        continue

                    # Send progress update for this node
                    retry_count = 0
                    if "sql_retry_count" in node_output:
                        retry_count = node_output.get("sql_retry_count", 0)
                    elif "interpretation_retry_count" in node_output:
                        retry_count = node_output.get("interpretation_retry_count", 0)

                    logger.info(f"⚙️ Workflow node: {node_name} (retry: {retry_count})")
                    await manager.send_progress(session_id, node_name, retry_count)

                    # Store the latest result
                    final_result = node_output

            # Use the final result from the last node
            result = final_result if final_result else {}
            logger.info(f"✅ Workflow completed successfully")

        except Exception as stream_error:
            logger.error(f"❌ Error during workflow streaming: {stream_error}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't raise - handle error response below
            result = {"final_response": f"I encountered an error processing your request: {str(stream_error)}", "metadata": {"error": True}}

        # Send final result
        final_response = result.get("final_response", "No response generated")
        metadata = result.get("metadata", {})
        logger.info(f"📤 Final response ready: {len(final_response)} characters")

        # Save response to Firestore (both success and error cases)
        try:
            logger.info(f"💾 Saving assistant response to Firestore...")
            firebase_client.save_message(
                user_id,
                conversation_id,
                "assistant",
                final_response,
                metadata=metadata
            )
            logger.info(f"✅ Assistant response saved successfully")
        except Exception as e:
            logger.error(f"❌ Could not save assistant response to Firestore: {e}")

        # Send final result to user
        if metadata.get("error", False):
            logger.info(f"📡 Sending error response to user...")
            import traceback
            await manager.send_error(
                session_id,
                final_response,
                traceback.format_exc()
            )
        else:
            logger.info(f"📡 Sending completed response to user...")
            await manager.send_completed(session_id, final_response, metadata)

        logger.info(f"🎯 [COMPLETE] Query processing finished successfully")

    except Exception as e:
        logger.error(f"💥 [OUTER ERROR] Fatal error processing query: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_msg = f"I encountered an error: {str(e)}"

        # Try to save error message to Firestore
        try:
            logger.info(f"💾 Attempting to save error message to Firestore...")
            firebase_client.save_message(
                user_id,
                conversation_id,
                "assistant",
                error_msg,
                metadata={"error": True}
            )
            logger.info(f"✅ Error message saved to Firestore")
        except Exception as save_error:
            logger.error(f"❌ Could not save error message to Firestore: {save_error}")

        logger.info(f"📡 Sending error to user...")
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


@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration."""
    from config.settings import settings

    return {
        "environment": settings.environment,
        "firebase_secret_name": settings.firebase_secret_name,
        "firebase_secret_dev": settings.firebase_secret_name_dev,
        "firebase_secret_prod": settings.firebase_secret_name_prod,
        "aws_region": settings.aws_region,
        "glue_database": settings.glue_database,
        "athena_s3_output": settings.athena_s3_output_location,
    }


@app.get("/debug/firebase-test")
async def test_firebase():
    """Test Firebase connection by attempting a simple read."""
    try:
        # Try to list conversations for a test user
        test_user_id = "test_debug_user"
        conversations = firebase_client.get_conversations(test_user_id)

        return {
            "status": "success",
            "message": "Firebase connection working",
            "test_user_id": test_user_id,
            "conversations_found": len(conversations)
        }
    except Exception as e:
        logger.error(f"Firebase test failed: {e}")
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
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


@app.delete("/conversations/{user_id}/{conversation_id}")
async def delete_conversation(user_id: str, conversation_id: str):
    """
    Delete a conversation permanently.

    Args:
        user_id: User ID
        conversation_id: Conversation ID to delete

    Returns:
        Success message if deleted, error if not found or failed

    Security:
        - User isolation enforced via user_id in path
        - Permanent deletion (cannot be recovered)
    """
    try:
        deleted = firebase_client.delete_conversation(user_id, conversation_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found for user {user_id}"
            )

        return {
            "message": "Conversation deleted successfully",
            "user_id": user_id,
            "conversation_id": conversation_id
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== User Profile Endpoints ==========

@app.get("/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """
    Get complete user profile.

    Args:
        user_id: User ID

    Returns:
        Complete profile dictionary with all 4 sections
        (business_profile, goals, preferences, learned_context)
    """
    try:
        profile = firebase_client.get_user_profile(user_id)
        return {
            "user_id": user_id,
            "profile": profile
        }
    except Exception as e:
        logger.error(f"Error fetching profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/users/{user_id}/profile")
async def create_or_update_profile(user_id: str, profile_data: ProfileUpdate):
    """
    Create or update user profile (typically used during onboarding).

    Args:
        user_id: User ID
        profile_data: Profile data (one or more sections to update)

    Returns:
        Success message

    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If save fails
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        data_dict = profile_data.model_dump(exclude_none=True)

        if not data_dict:
            raise HTTPException(
                status_code=400,
                detail="No profile data provided. Include at least one section."
            )

        firebase_client.save_user_profile(user_id, data_dict)

        return {
            "user_id": user_id,
            "message": "Profile saved successfully",
            "updated_sections": list(data_dict.keys())
        }
    except ValueError as e:
        # Validation error from profile_defaults validators
        logger.error(f"Validation error for user {user_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/users/{user_id}/profile/{section}")
async def update_profile_section(
    user_id: str,
    section: str,
    section_data: SectionUpdate
):
    """
    Update a specific section of user profile (partial update).

    Args:
        user_id: User ID
        section: Section name ('business_profile', 'goals', 'preferences', 'learned_context')
        section_data: Data to update in the section

    Returns:
        Success message

    Raises:
        HTTPException 400: If section name is invalid or validation fails
        HTTPException 500: If update fails
    """
    try:
        firebase_client.update_profile_section(user_id, section, section_data.data)

        return {
            "user_id": user_id,
            "section": section,
            "message": f"Section '{section}' updated successfully"
        }
    except ValueError as e:
        # Invalid section name or validation error
        logger.error(f"Validation error for user {user_id}, section {section}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating section {section} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/profile/summary")
async def get_profile_summary(user_id: str):
    """
    Get formatted profile context summary for display or agent use.

    Args:
        user_id: User ID

    Returns:
        Formatted string like: "User Profile: Business: BrandName | Category: Fashion | ..."
    """
    try:
        summary = firebase_client.get_profile_context_summary(user_id)

        return {
            "user_id": user_id,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error fetching profile summary for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Encryption Key Management Endpoints ==========

@app.get("/encryption/status")
async def get_encryption_status():
    """
    Get encryption feature status.

    Returns:
        Dict with encryption_enabled and KMS configuration status
    """
    from utils.kms_client import get_kms_client

    try:
        kms = get_kms_client()

        return {
            "encryption_enabled": settings.encryption_enabled,
            "kms_configured": kms.encryption_enabled and kms.kms_key_id is not None,
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(f"Error checking encryption status: {e}")
        return {
            "encryption_enabled": False,
            "kms_configured": False,
            "error": str(e)
        }


@app.post("/users/{user_id}/encryption-key/initialize")
async def initialize_user_encryption_key(user_id: str):
    """
    Initialize encryption key for a user.

    This endpoint generates a new Data Encryption Key (DEK) for the user,
    encrypts it with AWS KMS, and stores it in Firebase. This is called
    automatically when a user sends their first encrypted message.

    Args:
        user_id: User's Firebase Auth ID

    Returns:
        Success status and key metadata
    """
    try:
        if not settings.encryption_enabled:
            raise HTTPException(
                status_code=400,
                detail="Encryption is not enabled on this server"
            )

        # Get or create user's DEK (auto-creates if doesn't exist)
        dek = firebase_client.get_or_create_user_dek(user_id)

        logger.info(f"✅ Encryption key initialized for user {user_id[:8]}...")

        return {
            "success": True,
            "user_id": user_id,
            "message": "Encryption key initialized successfully",
            "key_length": len(dek),
            "algorithm": "AES-256-GCM"
        }

    except Exception as e:
        logger.error(f"Failed to initialize encryption key for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/encryption-key/status")
async def get_user_encryption_key_status(user_id: str):
    """
    Check if user has an encryption key set up.

    Args:
        user_id: User's Firebase Auth ID

    Returns:
        Dict with key existence status and metadata
    """
    try:
        if not settings.encryption_enabled:
            return {
                "encryption_enabled": False,
                "has_key": False,
                "message": "Encryption is disabled on this server"
            }

        # Check if user has encryption key in Firebase
        encryption_ref = firebase_client.get_encryption_ref(user_id)
        doc = encryption_ref.get()

        if doc.exists:
            key_data = doc.to_dict()
            return {
                "encryption_enabled": True,
                "has_key": True,
                "created_at": key_data.get("created_at"),
                "algorithm": key_data.get("algorithm"),
                "kms_key_version": key_data.get("kms_key_version")
            }
        else:
            return {
                "encryption_enabled": True,
                "has_key": False,
                "message": "No encryption key found for this user"
            }

    except Exception as e:
        logger.error(f"Error checking encryption key status for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/encryption-test")
async def test_encryption():
    """
    Test encryption system end-to-end.

    Tests:
    1. KMS access
    2. Encryption/decryption roundtrip
    3. Firebase key storage

    Returns:
        Test results
    """
    from utils.kms_client import get_kms_client
    from utils.encryption import test_encryption_roundtrip

    results = {
        "encryption_enabled": settings.encryption_enabled,
        "tests": {}
    }

    if not settings.encryption_enabled:
        results["message"] = "Encryption is disabled - tests skipped"
        return results

    try:
        # Test 1: KMS access
        kms = get_kms_client()
        kms_test = kms.test_kms_access()
        results["tests"]["kms_access"] = "✅ PASSED" if kms_test else "❌ FAILED"

        # Test 2: Encryption roundtrip
        encryption_test = test_encryption_roundtrip("Test message for encryption")
        results["tests"]["encryption_roundtrip"] = "✅ PASSED" if encryption_test else "❌ FAILED"

        # Test 3: KMS key info
        key_info = kms.get_key_info()
        results["tests"]["kms_key_info"] = key_info

        results["overall"] = "✅ ALL TESTS PASSED" if (kms_test and encryption_test) else "❌ SOME TESTS FAILED"

    except Exception as e:
        results["error"] = str(e)
        results["overall"] = "❌ TESTS FAILED WITH ERROR"

    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
