"""
Firebase client utilities for conversation context management.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Any, Optional
from config.settings import settings
import boto3
import json


class FirebaseClient:
    """Firebase client for managing conversation context."""

    def __init__(self):
        # Fetch Firebase credentials from AWS Secrets Manager
        secret_name = settings.firebase_secret_name
        region_name = settings.aws_region

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
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            secret_string = get_secret_value_response['SecretString']
            firebase_creds = json.loads(secret_string)
        except Exception as e:
            raise Exception(f"Error retrieving Firebase credentials from Secrets Manager: {str(e)}")

        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

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
    ):
        """Save a message to conversation history."""
        conv_ref = self.get_conversation_ref(user_id, conversation_id)
        doc = conv_ref.get()

        message = {
            "role": role,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "metadata": metadata or {},
        }

        if doc.exists:
            conv_ref.update({"messages": firestore.ArrayUnion([message])})
        else:
            conv_ref.set(
                {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "messages": [message],
                }
            )

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


# Global instance
firebase_client = FirebaseClient()
