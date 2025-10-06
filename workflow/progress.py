"""
Progress tracking and user-friendly status messages.
"""

# Progress stages for user-facing display
PROGRESS_STAGES = {
    "planner": {
        "message": "Planning Task...",
        "description": "Understanding your query and creating an execution plan",
        "emoji": "🤔"
    },
    "router": {
        "message": "Planning Task...",
        "description": "Routing to appropriate systems",
        "emoji": "🤔"
    },
    "sql_generator": {
        "message": "Fetching Data...",
        "description": "Preparing data retrieval",
        "emoji": "📊"
    },
    "sql_validator": {
        "message": "Validating Data...",
        "description": "Ensuring data quality",
        "emoji": "✓"
    },
    "sql_executor": {
        "message": "Fetching Data...",
        "description": "Retrieving your data",
        "emoji": "📊"
    },
    "data_interpreter": {
        "message": "Interpreting Data...",
        "description": "Analyzing data with e-commerce insights",
        "emoji": "🧠"
    },
    "interpretation_validator": {
        "message": "Interpreting Data...",
        "description": "Ensuring quality insights",
        "emoji": "🧠"
    },
    "interpreter": {
        "message": "Finalizing Response...",
        "description": "Preparing your insights",
        "emoji": "✨"
    }
}

# Simplified progress flow for user display
USER_PROGRESS_FLOW = [
    "Planning Task...",
    "Fetching Data...",
    "Validating Data...",
    "Interpreting Data...",
    "Finalizing Response..."
]


def get_progress_message(node_name: str, include_emoji: bool = False) -> str:
    """
    Get user-friendly progress message for a workflow node.

    Args:
        node_name: Name of the workflow node
        include_emoji: Whether to include emoji in message

    Returns:
        User-friendly progress message
    """
    stage = PROGRESS_STAGES.get(node_name, {
        "message": "Processing...",
        "emoji": "⚙️"
    })

    if include_emoji:
        return f"{stage['emoji']} {stage['message']}"
    return stage["message"]


def get_progress_description(node_name: str) -> str:
    """
    Get detailed description of what's happening in this stage.

    Args:
        node_name: Name of the workflow node

    Returns:
        Detailed description
    """
    stage = PROGRESS_STAGES.get(node_name, {})
    return stage.get("description", "Processing your request")


def get_progress_percentage(node_name: str) -> int:
    """
    Get approximate progress percentage for a workflow node.

    Args:
        node_name: Name of the workflow node

    Returns:
        Progress percentage (0-100)
    """
    progress_map = {
        "planner": 10,
        "router": 15,
        "sql_generator": 30,
        "sql_validator": 40,
        "sql_executor": 50,
        "data_interpreter": 75,
        "interpretation_validator": 85,
        "interpreter": 95
    }
    return progress_map.get(node_name, 0)


# WebSocket event types for streaming
class ProgressEvent:
    """Progress event for WebSocket streaming."""

    STARTED = "started"
    PROGRESS = "progress"
    DATA_CHUNK = "data_chunk"
    COMPLETED = "completed"
    ERROR = "error"
    CONVERSATION_METADATA = "conversation_metadata"

    @staticmethod
    def create_event(event_type: str, data: dict) -> dict:
        """Create a progress event for streaming."""
        return {
            "type": event_type,
            "timestamp": None,  # Will be set by backend
            "data": data
        }

    @staticmethod
    def started(query: str) -> dict:
        """Create a 'started' event."""
        return ProgressEvent.create_event(
            ProgressEvent.STARTED,
            {
                "message": "Planning Task...",
                "query": query,
                "progress": 0
            }
        )

    @staticmethod
    def progress(node_name: str, retry_count: int = 0) -> dict:
        """Create a 'progress' event."""
        message = get_progress_message(node_name)

        # Add retry info if applicable
        if retry_count > 0:
            message = f"{message} (Attempt {retry_count + 1})"

        return ProgressEvent.create_event(
            ProgressEvent.PROGRESS,
            {
                "message": message,
                "description": get_progress_description(node_name),
                "progress": get_progress_percentage(node_name),
                "stage": node_name
            }
        )

    @staticmethod
    def data_chunk(chunk: str) -> dict:
        """Create a 'data_chunk' event for streaming responses."""
        return ProgressEvent.create_event(
            ProgressEvent.DATA_CHUNK,
            {
                "chunk": chunk
            }
        )

    @staticmethod
    def completed(response: str, metadata: dict = None) -> dict:
        """Create a 'completed' event."""
        return ProgressEvent.create_event(
            ProgressEvent.COMPLETED,
            {
                "message": "Complete!",
                "response": response,
                "progress": 100,
                "metadata": metadata or {}
            }
        )

    @staticmethod
    def error(error_message: str, details: str = None) -> dict:
        """Create an 'error' event."""
        return ProgressEvent.create_event(
            ProgressEvent.ERROR,
            {
                "message": "Error occurred",
                "error": error_message,
                "details": details
            }
        )

    @staticmethod
    def conversation_metadata(title: str, date: str, conversation_id: str) -> dict:
        """Create a 'conversation_metadata' event."""
        return ProgressEvent.create_event(
            ProgressEvent.CONVERSATION_METADATA,
            {
                "title": title,
                "date": date,
                "conversation_id": conversation_id
            }
        )
