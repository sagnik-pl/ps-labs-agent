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
from utils.profile_defaults import (
    get_default_profile,
    validate_business_profile,
    validate_goals,
    validate_preferences,
    format_profile_for_prompt,
)
from utils.encryption import (
    generate_dek,
    encrypt_message,
    decrypt_message,
    encode_key_for_storage,
    decode_key_from_storage,
)
from utils.kms_client import get_kms_client

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

    def get_encryption_ref(self, user_id: str):
        """Get Firestore reference to user's encryption key."""
        return self.db.collection("conversations").document(user_id).collection(
            "encryption"
        ).document("key")

    def get_or_create_user_dek(self, user_id: str) -> bytes:
        """
        Get user's Data Encryption Key (DEK), creating if it doesn't exist.

        The DEK is encrypted with AWS KMS master key and stored in Firebase.
        This method fetches the encrypted DEK, decrypts it with KMS, and returns
        the plaintext DEK for use in message encryption/decryption.

        Args:
            user_id: User's Firebase Auth ID

        Returns:
            bytes: 32-byte decrypted DEK ready for use

        Raises:
            Exception: If encryption is disabled or KMS operations fail
        """
        from config.settings import settings

        if not settings.encryption_enabled:
            raise Exception("Encryption is disabled - cannot get DEK")

        try:
            # Check if user already has a DEK
            encryption_ref = self.get_encryption_ref(user_id)
            doc = encryption_ref.get()

            if doc.exists:
                # Decrypt existing DEK
                logger.debug(f"Fetching existing DEK for user {user_id[:8]}...")
                encrypted_dek = doc.to_dict().get("encrypted_dek")

                if not encrypted_dek:
                    raise Exception("User encryption doc exists but encrypted_dek field is missing")

                # Decrypt with KMS
                kms = get_kms_client()
                dek = kms.decrypt_dek(encrypted_dek)

                logger.debug(f"✅ DEK decrypted for user {user_id[:8]}...")
                return dek

            else:
                # Generate new DEK for user
                logger.info(f"Generating new DEK for user {user_id[:8]}...")

                dek = generate_dek()

                # Encrypt with KMS
                kms = get_kms_client()
                encrypted_dek = kms.encrypt_dek(dek)

                # Store in Firebase
                from datetime import datetime, timezone
                encryption_ref.set({
                    "user_id": user_id,
                    "encrypted_dek": encrypted_dek,
                    "created_at": datetime.now(timezone.utc),
                    "algorithm": "AES-256-GCM",
                    "kms_key_version": "v1"
                })

                logger.info(f"✅ New DEK created and stored for user {user_id[:8]}...")
                return dek

        except Exception as e:
            logger.error(f"❌ Failed to get/create DEK for user {user_id[:8]}: {e}")
            raise

    def get_conversation_history(
        self, user_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history from Firestore.

        Automatically decrypts encrypted messages if encryption is enabled.
        Handles mixed encrypted/plaintext messages for backward compatibility.

        Args:
            user_id: User's Firebase Auth ID
            conversation_id: Conversation UUID

        Returns:
            List of message dicts with decrypted content
        """
        from config.settings import settings

        conv_ref = self.get_conversation_ref(user_id, conversation_id)
        doc = conv_ref.get()

        if not doc.exists:
            return []

        data = doc.to_dict()
        messages = data.get("messages", [])

        # If encryption is disabled, return messages as-is
        if not settings.encryption_enabled:
            return messages

        # Decrypt encrypted messages
        try:
            dek = None  # Lazy-load DEK only if needed

            decrypted_messages = []
            for msg in messages:
                # Check if message is encrypted
                if msg.get("encrypted", False):
                    try:
                        # Lazy-load DEK on first encrypted message
                        if dek is None:
                            dek = self.get_or_create_user_dek(user_id)

                        # Decrypt message content
                        encrypted_data = {
                            "ciphertext": msg["content"],
                            "nonce": msg["nonce"],
                            "version": msg.get("encryption_version", 1),
                            "algorithm": msg.get("algorithm", "AES-256-GCM")
                        }
                        plaintext = decrypt_message(encrypted_data, dek)

                        # Return decrypted message (remove encryption metadata)
                        decrypted_msg = {
                            "role": msg["role"],
                            "content": plaintext,
                            "timestamp": msg["timestamp"],
                            "metadata": msg.get("metadata", {})
                        }
                        decrypted_messages.append(decrypted_msg)

                    except Exception as e:
                        logger.error(f"Failed to decrypt message: {e}")
                        # Return placeholder for failed decryption
                        decrypted_messages.append({
                            "role": msg.get("role", "unknown"),
                            "content": "[Decryption failed]",
                            "timestamp": msg.get("timestamp"),
                            "metadata": {"decryption_error": str(e)}
                        })
                else:
                    # Plaintext message (backward compatibility)
                    decrypted_messages.append(msg)

            return decrypted_messages

        except Exception as e:
            logger.error(f"Error processing conversation history: {e}")
            # Return plaintext messages if decryption setup fails
            return messages

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

            # Encrypt message if encryption is enabled
            from config.settings import settings

            if settings.encryption_enabled:
                try:
                    # Get user's DEK
                    dek = self.get_or_create_user_dek(user_id)

                    # Encrypt message content
                    encrypted_data = encrypt_message(content, dek)

                    # Create encrypted message
                    message = {
                        "role": role,
                        "content": encrypted_data['ciphertext'],
                        "encrypted": True,
                        "nonce": encrypted_data['nonce'],
                        "encryption_version": encrypted_data['version'],
                        "algorithm": encrypted_data['algorithm'],
                        "timestamp": now,
                        "metadata": metadata or {},
                    }

                    logger.debug(f"✅ Message encrypted for user {user_id[:8]}...")

                except Exception as e:
                    logger.error(f"❌ Encryption failed for user {user_id[:8]}: {e}")
                    # Fall back to plaintext if encryption fails
                    message = {
                        "role": role,
                        "content": content,
                        "encrypted": False,
                        "timestamp": now,
                        "metadata": metadata or {},
                    }
            else:
                # Store plaintext if encryption is disabled
                message = {
                    "role": role,
                    "content": content,
                    "encrypted": False,
                    "timestamp": now,
                    "metadata": metadata or {},
                }

            # Create last_message preview (first 50 chars of plaintext)
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
        """
        Get a compressed summary of conversation context for agent use.

        Only includes user queries (full) and assistant responses (truncated to 200 chars).
        This prevents token explosion from large data responses while preserving conversational context.

        Returns:
            Formatted context string with last 10 message turns (compressed)
        """
        messages = self.get_conversation_history(user_id, conversation_id)

        if not messages:
            return "No previous conversation history."

        # Format last N messages for context (increased from 5 to 10 due to compression)
        context_messages = messages[-10:]  # Last 10 messages (user + assistant pairs)
        formatted = []

        for msg in context_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                # Keep full user query (users don't write essays)
                formatted.append(f"User: {content}")
            elif role == "assistant":
                # Truncate assistant response to first 200 chars (skip data dumps)
                # Assistant responses often contain large SQL results, data tables, etc.
                summary = content[:200] + "..." if len(content) > 200 else content
                formatted.append(f"Assistant: {summary}")
            else:
                # Fallback for any other role
                summary = content[:200] + "..." if len(content) > 200 else content
                formatted.append(f"{role}: {summary}")

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

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Delete a conversation permanently from Firestore.

        Args:
            user_id: User ID
            conversation_id: Conversation ID

        Returns:
            True if conversation was deleted, False if it didn't exist

        Raises:
            Exception: If deletion fails
        """
        try:
            conv_ref = self.get_conversation_ref(user_id, conversation_id)
            doc = conv_ref.get()

            if not doc.exists:
                logger.warning(f"Cannot delete non-existent conversation: {conversation_id[:12]}... for user {user_id[:8]}...")
                return False

            # Delete the conversation document
            conv_ref.delete()
            logger.info(f"✅ Deleted conversation {conversation_id[:12]}... for user {user_id[:8]}...")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting conversation {conversation_id[:12]}...: {e}")
            raise Exception(f"Failed to delete conversation: {str(e)}")

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

    # ========== User Profile Methods ==========

    def get_profile_ref(self, user_id: str):
        """Get Firestore reference to user's profile collection."""
        return self.db.collection("conversations").document(user_id).collection("profile")

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch complete user profile from Firestore or return defaults.

        Args:
            user_id: User ID

        Returns:
            Complete profile dictionary with all 4 sections (business_profile, goals, preferences, learned_context)
        """
        try:
            profile_ref = self.get_profile_ref(user_id)
            profile_data = {}

            # Fetch all 4 profile sections
            sections = ["business_profile", "goals", "preferences", "learned_context"]
            for section in sections:
                doc = profile_ref.document(section).get()
                if doc.exists:
                    profile_data[section] = doc.to_dict()
                else:
                    # Section doesn't exist, use defaults
                    profile_data[section] = None

            # If no profile exists at all, return complete defaults
            if all(v is None for v in profile_data.values()):
                logger.info(f"No profile found for user {user_id[:8]}..., returning defaults")
                return get_default_profile()

            # Merge with defaults for any missing sections
            default_profile = get_default_profile()
            for section in sections:
                if profile_data[section] is None:
                    profile_data[section] = default_profile[section]

            logger.info(f"✅ Fetched profile for user {user_id[:8]}...")
            return profile_data

        except Exception as e:
            logger.error(f"❌ Error fetching profile for user {user_id}: {str(e)}")
            # Return defaults on error
            return get_default_profile()

    def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """
        Create or update complete user profile with validation.

        Args:
            user_id: User ID
            profile_data: Profile data dictionary containing one or more sections
                         (business_profile, goals, preferences, learned_context)

        Raises:
            ValueError: If validation fails
        """
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            profile_ref = self.get_profile_ref(user_id)

            # Validate and save each section
            if "business_profile" in profile_data:
                validated = validate_business_profile(profile_data["business_profile"])
                profile_ref.document("business_profile").set(validated)
                logger.info(f"✅ Saved business_profile for user {user_id[:8]}...")

            if "goals" in profile_data:
                validated = validate_goals(profile_data["goals"])
                profile_ref.document("goals").set(validated)
                logger.info(f"✅ Saved goals for user {user_id[:8]}...")

            if "preferences" in profile_data:
                validated = validate_preferences(profile_data["preferences"])
                profile_ref.document("preferences").set(validated)
                logger.info(f"✅ Saved preferences for user {user_id[:8]}...")

            if "learned_context" in profile_data:
                # Learned context doesn't need validation
                learned = profile_data["learned_context"]
                learned["updated_at"] = now
                if "created_at" not in learned or learned["created_at"] is None:
                    learned["created_at"] = now
                profile_ref.document("learned_context").set(learned)
                logger.info(f"✅ Saved learned_context for user {user_id[:8]}...")

            # Update user document's last_updated timestamp
            user_doc_ref = self.get_user_doc_ref(user_id)
            user_doc_ref.update({"last_updated": now})

        except ValueError as e:
            logger.error(f"❌ Validation error saving profile for user {user_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Error saving profile for user {user_id}: {str(e)}")
            raise

    def update_profile_section(self, user_id: str, section: str, data: Dict[str, Any]):
        """
        Update a specific section of user profile (partial update).

        Args:
            user_id: User ID
            section: Section name ('business_profile', 'goals', 'preferences', 'learned_context')
            data: Data to update in the section

        Raises:
            ValueError: If section name is invalid or validation fails
        """
        valid_sections = ["business_profile", "goals", "preferences", "learned_context"]
        if section not in valid_sections:
            raise ValueError(f"Invalid section: {section}. Must be one of {valid_sections}")

        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            profile_ref = self.get_profile_ref(user_id)

            # Fetch existing data for this section
            doc = profile_ref.document(section).get()
            if doc.exists:
                existing_data = doc.to_dict()
            else:
                # No existing data, start with defaults
                default_profile = get_default_profile()
                existing_data = default_profile[section]

            # Merge with new data
            merged_data = {**existing_data, **data}
            merged_data["updated_at"] = now

            # Validate based on section type
            if section == "business_profile":
                validated = validate_business_profile(merged_data)
            elif section == "goals":
                validated = validate_goals(merged_data)
            elif section == "preferences":
                validated = validate_preferences(merged_data)
            else:  # learned_context
                validated = merged_data

            # Save to Firestore
            profile_ref.document(section).set(validated)
            logger.info(f"✅ Updated {section} for user {user_id[:8]}...")

            # Update user document's last_updated timestamp
            user_doc_ref = self.get_user_doc_ref(user_id)
            user_doc_ref.update({"last_updated": now})

        except ValueError as e:
            logger.error(f"❌ Validation error updating {section} for user {user_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Error updating {section} for user {user_id}: {str(e)}")
            raise

    def get_profile_context_summary(self, user_id: str) -> str:
        """
        Get formatted profile context string for agent prompt injection.

        Args:
            user_id: User ID

        Returns:
            Formatted string like: "User Profile: Business: BrandName | Category: Fashion | ..."
        """
        try:
            profile = self.get_user_profile(user_id)
            return format_profile_for_prompt(profile)
        except Exception as e:
            logger.error(f"❌ Error formatting profile context for user {user_id}: {str(e)}")
            return "No profile information available."

    def update_learned_context(self, user_id: str, insights: Dict[str, Any]):
        """
        Append learned insights to user's learned_context (incremental learning).

        Args:
            user_id: User ID
            insights: Dictionary with keys like 'common_questions', 'pain_points',
                     'successful_actions', 'channel_focus'

        Example:
            update_learned_context(user_id, {
                "common_questions": ["How do I improve engagement?"],
                "pain_points": ["Low conversion rate"],
                "channel_focus": {"instagram": 80}
            })
        """
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            profile_ref = self.get_profile_ref(user_id)

            # Fetch existing learned_context
            doc = profile_ref.document("learned_context").get()
            if doc.exists:
                learned = doc.to_dict()
            else:
                # Initialize with defaults
                from utils.profile_defaults import DEFAULT_LEARNED_CONTEXT
                learned = DEFAULT_LEARNED_CONTEXT.copy()
                learned["created_at"] = now

            # Append new insights (don't overwrite, accumulate)
            if "common_questions" in insights:
                existing_questions = learned.get("common_questions", [])
                new_questions = insights["common_questions"]
                # Append and deduplicate
                learned["common_questions"] = list(set(existing_questions + new_questions))

            if "pain_points" in insights:
                existing_pain_points = learned.get("pain_points", [])
                new_pain_points = insights["pain_points"]
                learned["pain_points"] = list(set(existing_pain_points + new_pain_points))

            if "successful_actions" in insights:
                existing_actions = learned.get("successful_actions", [])
                new_actions = insights["successful_actions"]
                learned["successful_actions"] = list(set(existing_actions + new_actions))

            if "channel_focus" in insights:
                # Merge channel focus percentages (average if overlapping)
                existing_focus = learned.get("channel_focus", {})
                new_focus = insights["channel_focus"]
                for channel, percentage in new_focus.items():
                    if channel in existing_focus:
                        # Average the percentages
                        existing_focus[channel] = (existing_focus[channel] + percentage) / 2
                    else:
                        existing_focus[channel] = percentage
                learned["channel_focus"] = existing_focus

            learned["updated_at"] = now

            # Save to Firestore
            profile_ref.document("learned_context").set(learned)
            logger.info(f"✅ Updated learned_context for user {user_id[:8]}...")

        except Exception as e:
            logger.error(f"❌ Error updating learned_context for user {user_id}: {str(e)}")
            raise


# Global instance
firebase_client = FirebaseClient()
