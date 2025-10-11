"""
Firebase client utilities for conversation context management.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.settings import settings
import boto3
import json
import logging

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Firebase client for managing conversation context."""

    def __init__(self):
        # Fetch Firebase credentials from AWS Secrets Manager
        secret_name = settings.firebase_secret_name
        region_name = settings.aws_region

        logger.info("=" * 80)
        logger.info(f"Initializing Firebase with environment: {settings.environment}")
        logger.info(f"Using Firebase secret: {secret_name}")
        logger.info(f"AWS Region: {region_name}")
        logger.info("=" * 80)

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )

        # Retrieve the secret
        try:
            logger.info(f"Attempting to fetch secret: {secret_name}")
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            secret_string = get_secret_value_response['SecretString']
            firebase_creds = json.loads(secret_string)
            logger.info("✅ Successfully retrieved Firebase credentials from Secrets Manager")
        except Exception as e:
            logger.error(f"❌ Error retrieving Firebase credentials from Secrets Manager: {str(e)}")
            raise Exception(f"Error retrieving Firebase credentials from Secrets Manager: {str(e)}")

        # Initialize Firebase Admin SDK
        try:
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("✅ Firebase Admin SDK initialized successfully")
            logger.info(f"Firestore client created: {self.db is not None}")
        except Exception as e:
            logger.error(f"❌ Error initializing Firebase Admin SDK: {str(e)}")
            raise Exception(f"Error initializing Firebase Admin SDK: {str(e)}")

    def get_user_doc_ref(self, user_id: str):
        """Get Firestore reference to user document."""
        return self.db.collection("conversations").document(user_id)

    def get_conversation_ref(self, user_id: str, conversation_id: str):
        """Get Firestore reference to a conversation."""
        return self.db.collection("conversations").document(user_id).collection(
            "chats"
        ).document(conversation_id)

    def get_conversation_history(
        self, user_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history from Firestore."""
        conv_ref = self.get_conversation_ref(user_id, conversation_id)
        doc = conv_ref.get()

        if doc.exists:
            data = doc.to_dict()
            return data.get("messages", [])
        return []

    def save_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ):
        """Save a message to conversation history."""
        from datetime import datetime, timezone

        try:
            now = datetime.now(timezone.utc)

            logger.info(f"Attempting to save message: user={user_id[:8]}..., conv={conversation_id[:8]}..., role={role}")

            # Ensure user document exists (prevent ghost document)
            user_doc_ref = self.get_user_doc_ref(user_id)
            user_doc = user_doc_ref.get()
            if not user_doc.exists:
                logger.info(f"Creating new user document for {user_id[:8]}...")
                user_doc_ref.set({
                    "user_id": user_id,
                    "created_at": now,
                    "last_updated": now
                })
            else:
                logger.info(f"Updating existing user document for {user_id[:8]}...")
                user_doc_ref.update({"last_updated": now})

            # Save message to conversation
            conv_ref = self.get_conversation_ref(user_id, conversation_id)
            doc = conv_ref.get()

            message = {
                "role": role,
                "content": content,
                "timestamp": now,
                "metadata": metadata or {},
            }

            # Create last_message preview (first 50 chars)
            last_message_preview = content[:50] + "..." if len(content) > 50 else content

            if doc.exists:
                # Update existing conversation
                logger.info(f"Updating existing conversation {conversation_id[:8]}...")
                update_data = {
                    "messages": firestore.ArrayUnion([message]),
                    "last_updated": now,
                    "last_message": last_message_preview
                }
                conv_ref.update(update_data)
            else:
                # Create new conversation
                logger.info(f"Creating new conversation {conversation_id[:8]}... with title: {title}")
                conv_data = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "created_at": now,
                    "last_updated": now,
                    "messages": [message],
                    "last_message": last_message_preview
                }
                # Add title if provided (for first message)
                if title:
                    conv_data["title"] = title

                conv_ref.set(conv_data)

            logger.info(f"✅ Successfully saved {role} message to Firestore")

        except Exception as e:
            logger.error(f"❌ Error saving message to Firestore: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def get_context_summary(self, user_id: str, conversation_id: str) -> str:
        """Get a summary of conversation context for agent use."""
        messages = self.get_conversation_history(user_id, conversation_id)

        if not messages:
            return "No previous conversation history."

        # Format last N messages for context
        context_messages = messages[-5:]  # Last 5 messages
        formatted = []

        for msg in context_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversations for a user.

        Args:
            user_id: User ID

        Returns:
            List of conversations with metadata (sorted by last updated)
        """
        try:
            # Query all conversations for this user
            chats_ref = self.db.collection("conversations").document(user_id).collection("chats")
            conversations = []

            for doc in chats_ref.stream():
                data = doc.to_dict()

                # Get timestamps (return full timestamp for proper sorting)
                created_at = data.get("created_at")
                last_updated = data.get("last_updated", created_at)

                # Convert Firestore timestamps to ISO format strings
                created_at_str = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at) if created_at else None
                last_updated_str = last_updated.isoformat() if hasattr(last_updated, 'isoformat') else str(last_updated) if last_updated else None

                conversations.append({
                    "conversation_id": doc.id,
                    "title": data.get("title", f"Conversation {doc.id[:8]}"),
                    "created_at": created_at_str,
                    "updated_at": last_updated_str,
                    "message_count": len(data.get("messages", [])),
                    "last_message": data.get("last_message", self._get_conversation_preview(data.get("messages", []))),
                    "_sort_timestamp": last_updated or created_at  # Store for sorting
                })

            # Sort by last updated timestamp (most recent first)
            conversations.sort(
                key=lambda x: x.get("_sort_timestamp") or datetime.min,
                reverse=True
            )

            # Remove the sorting helper field before returning
            for conv in conversations:
                conv.pop("_sort_timestamp", None)

            return conversations

        except Exception as e:
            logger.error(f"Error fetching conversations for user {user_id}: {e}")
            return []

    def get_conversation_messages(
        self, user_id: str, conversation_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            limit: Maximum number of messages to return (default: 50)

        Returns:
            List of messages (most recent last) with ISO format timestamps
        """
        try:
            messages = self.get_conversation_history(user_id, conversation_id)

            # Return last N messages
            if len(messages) > limit:
                messages = messages[-limit:]

            # Convert Firestore timestamps to ISO format strings
            formatted_messages = []
            for msg in messages:
                formatted_msg = {
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "timestamp": msg.get("timestamp").isoformat() if hasattr(msg.get("timestamp"), 'isoformat') else msg.get("timestamp"),
                    "metadata": msg.get("metadata", {})
                }
                formatted_messages.append(formatted_msg)

            return formatted_messages

        except Exception as e:
            logger.error(f"Error fetching messages for conversation {conversation_id}: {e}")
            return []

    def is_new_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Check if a conversation is new (has no messages yet).

        Args:
            user_id: User ID
            conversation_id: Conversation ID

        Returns:
            True if conversation is new, False otherwise
        """
        conv_ref = self.get_conversation_ref(user_id, conversation_id)
        doc = conv_ref.get()
        return not doc.exists

    def _get_conversation_preview(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get a preview of the conversation (first user message).

        Args:
            messages: List of messages

        Returns:
            Preview text (truncated to 100 chars)
        """
        if not messages:
            return "Empty conversation"

        # Find first user message
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if len(content) > 100:
                    return content[:97] + "..."
                return content

        # Fallback to first message
        if messages:
            content = messages[0].get("content", "Empty conversation")
            if len(content) > 100:
                return content[:97] + "..."
            return content

        return "Empty conversation"


# Global instance
firebase_client = FirebaseClient()
