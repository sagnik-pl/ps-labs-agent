"""
Custom Firestore-based checkpointer for LangGraph state persistence.
"""
from typing import Optional, Dict, Any
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
from utils.firebase_client import firebase_client
import pickle
import base64


class FirestoreCheckpointer(BaseCheckpointSaver):
    """
    Checkpointer that stores LangGraph state in Firestore.

    This allows conversation state to persist across sessions
    and be shared between different instances of the application.
    """

    def __init__(self):
        """Initialize Firestore checkpointer."""
        super().__init__()
        self.db = firebase_client.db

    def _get_checkpoint_path(
        self, thread_id: str, checkpoint_id: Optional[str] = None
    ) -> str:
        """
        Get Firestore document path for checkpoint.

        Args:
            thread_id: Conversation/thread ID
            checkpoint_id: Optional specific checkpoint ID

        Returns:
            Firestore document path
        """
        base_path = f"checkpoints/{thread_id}"
        if checkpoint_id:
            return f"{base_path}/states/{checkpoint_id}"
        return f"{base_path}/latest/state"

    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save checkpoint to Firestore.

        Args:
            config: Checkpoint configuration
            checkpoint: Checkpoint data to save
            metadata: Optional metadata
        """
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return

            # Serialize checkpoint
            serialized = base64.b64encode(pickle.dumps(checkpoint)).decode("utf-8")

            # Prepare document data
            doc_data = {
                "checkpoint": serialized,
                "metadata": metadata or {},
                "timestamp": firebase_client.firestore.SERVER_TIMESTAMP,
            }

            # Save to Firestore
            doc_path = self._get_checkpoint_path(thread_id)
            self.db.document(doc_path).set(doc_data)

        except Exception as e:
            print(f"Error saving checkpoint to Firestore: {e}")

    def get(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """
        Retrieve checkpoint from Firestore.

        Args:
            config: Checkpoint configuration

        Returns:
            Checkpoint data or None if not found
        """
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return None

            # Retrieve from Firestore
            doc_path = self._get_checkpoint_path(thread_id)
            doc = self.db.document(doc_path).get()

            if not doc.exists:
                return None

            # Deserialize checkpoint
            data = doc.to_dict()
            serialized = data.get("checkpoint")
            if not serialized:
                return None

            checkpoint = pickle.loads(base64.b64decode(serialized))
            return checkpoint

        except Exception as e:
            print(f"Error retrieving checkpoint from Firestore: {e}")
            return None

    def list(
        self, config: Dict[str, Any], limit: Optional[int] = None
    ) -> list[Checkpoint]:
        """
        List checkpoints for a thread.

        Args:
            config: Checkpoint configuration
            limit: Optional limit on number of checkpoints

        Returns:
            List of checkpoints
        """
        # For simplicity, we only keep the latest checkpoint
        # This can be extended to store multiple checkpoints per thread
        checkpoint = self.get(config)
        return [checkpoint] if checkpoint else []
