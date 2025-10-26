#!/usr/bin/env python3
"""
Interactive WebSocket test script for semantic layer iteration.

This script connects to the production backend and sends test queries,
displaying full semantic layer routing decisions and agent execution details.

Features:
- Conversation context handling (new vs existing conversations)
- Real-time progress streaming
- Semantic layer insight extraction
- Interactive query input for rapid iteration
"""
import asyncio
import websockets
import json
import uuid
import requests
import ssl
from datetime import datetime
from typing import Dict, List, Optional

# Production backend URLs
BACKEND_URL = "ps-labs-agent-backend-production.up.railway.app"
WS_URL = f"wss://{BACKEND_URL}"
HTTP_URL = f"https://{BACKEND_URL}"

# Test user ID (has existing data)
TEST_USER_ID = "45up1lHMF2N4SwAJc6iMEOdLg9y1"


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_section(title: str, content: str = None):
    """Print a section with optional content."""
    print(f"{Colors.CYAN}{Colors.BOLD}{title}{Colors.END}")
    if content:
        print(f"{content}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def get_user_conversations() -> List[Dict]:
    """Fetch all conversations for the test user."""
    try:
        response = requests.get(f"{HTTP_URL}/conversations/{TEST_USER_ID}")
        if response.status_code == 200:
            data = response.json()
            return data.get('conversations', [])
        else:
            print_error(f"Failed to fetch conversations: {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Error fetching conversations: {e}")
        return []


def select_conversation_mode() -> tuple[str, bool]:
    """
    Let user select conversation mode.

    Returns:
        tuple: (conversation_id, is_new)
    """
    print_header("SELECT CONVERSATION MODE")

    # Fetch existing conversations
    conversations = get_user_conversations()

    if conversations:
        print_section(f"Found {len(conversations)} existing conversations:")
        for i, conv in enumerate(conversations[:10], 1):  # Show max 10
            title = conv.get('title', 'Untitled')
            msg_count = conv.get('message_count', 0)
            updated = conv.get('updated_at', 'Unknown')
            print(f"  {i}. {title} ({msg_count} messages) - Updated: {updated[:19]}")

        print()
        print_info("Options:")
        print("  N - Start NEW conversation")
        print("  1-10 - Continue existing conversation")
        print()

        choice = input(f"{Colors.BOLD}Select option: {Colors.END}").strip().upper()

        if choice == 'N':
            new_conv_id = str(uuid.uuid4())
            print_success(f"Starting new conversation: {new_conv_id[:12]}...")
            return new_conv_id, True
        else:
            try:
                index = int(choice) - 1
                if 0 <= index < len(conversations):
                    selected_conv = conversations[index]
                    conv_id = selected_conv['conversation_id']
                    print_success(f"Continuing conversation: {selected_conv.get('title')}")
                    return conv_id, False
                else:
                    print_warning("Invalid selection, starting new conversation")
                    new_conv_id = str(uuid.uuid4())
                    return new_conv_id, True
            except ValueError:
                print_warning("Invalid input, starting new conversation")
                new_conv_id = str(uuid.uuid4())
                return new_conv_id, True
    else:
        print_info("No existing conversations found. Starting new conversation.")
        new_conv_id = str(uuid.uuid4())
        return new_conv_id, True


async def send_query_and_display_response(
    websocket: websockets.WebSocketClientProtocol,
    query: str,
    conversation_id: str
):
    """
    Send a query and display the full response with semantic layer insights.

    Args:
        websocket: Active WebSocket connection
        query: User's query
        conversation_id: Conversation ID
    """
    print_header(f"QUERY: {query}")

    # Send query with debug_mode enabled
    message_to_send = {
        "type": "query",
        "query": query,
        "conversation_id": conversation_id,
        "debug_mode": True  # Enable debug output
    }

    print_info(f"Sending message: {json.dumps(message_to_send, indent=2)}")
    await websocket.send(json.dumps(message_to_send))

    print_section("Backend Response Stream:")
    print()

    # Track response
    completed = False
    final_response = None
    metadata = None
    progress_nodes = []

    # Receive messages
    while not completed:
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=60)
            data = json.loads(message)

            msg_type = data.get("type")
            timestamp = data.get("timestamp", "")

            if msg_type == "started":
                print_info(f"[{timestamp[:19]}] Started processing query")

            elif msg_type == "progress":
                # Progress data is nested in "data" key
                progress_data = data.get("data", {})
                node = progress_data.get("stage", "unknown")
                progress_pct = progress_data.get("progress", 0)
                retry = data.get("retry_count", 0)  # retry_count is at root level if present
                progress_nodes.append(node)

                retry_str = f" (retry {retry})" if retry > 0 else ""
                print(f"  ⏳ [{timestamp[:19]}] Progress: {progress_pct}% - {Colors.BOLD}{node}{Colors.END}{retry_str}")

            elif msg_type == "completed":
                # Completed data is nested in "data" key (matching frontend behavior)
                completed_data = data.get("data", {})
                final_response = completed_data.get("response", "")
                metadata = completed_data.get("metadata", {})
                print_success(f"[{timestamp[:19]}] Completed!")
                completed = True

            elif msg_type == "error":
                # Error data is nested in "data" key
                error_data = data.get("data", {})
                error_msg = error_data.get("error", "Unknown error")
                details = error_data.get("details", "")
                print_error(f"[{timestamp[:19]}] Error: {error_msg}")
                if details:
                    print(f"  Details: {details}")
                return

            elif msg_type == "conversation_metadata":
                # Conversation metadata is nested in "data" key
                metadata_data = data.get("data", {})
                title = metadata_data.get("title", "Untitled")
                date = metadata_data.get("date", "")
                print_info(f"New conversation: '{title}' ({date})")

            elif msg_type == "debug":
                # Debug information from backend
                debug_data = data.get("data", {})
                node = data.get("node", "unknown")

                print()
                print(f"  {Colors.CYAN}{Colors.BOLD}🔍 DEBUG - {node}{Colors.END}")

                if node == "planner":
                    exec_plan = debug_data.get("execution_plan", {})
                    routing = debug_data.get("routing_decision", {})

                    if exec_plan:
                        print(f"     {Colors.YELLOW}Execution Plan:{Colors.END}")
                        print(f"       Type: {exec_plan.get('type', 'N/A')}")
                        if exec_plan.get('platforms'):
                            print(f"       Platforms: {exec_plan.get('platforms')}")
                        if exec_plan.get('metrics'):
                            print(f"       Metrics: {exec_plan.get('metrics')}")

                    if routing:
                        print(f"     {Colors.YELLOW}Routing:{Colors.END}")
                        print(f"       Agent: {routing.get('agent', 'N/A')}")
                        print(f"       Confidence: {routing.get('confidence', 'N/A')}")

                elif node == "sql_generator":
                    sql = debug_data.get("generated_sql", "")
                    retry = debug_data.get("retry_count", 0)
                    retry_str = f" (retry {retry})" if retry > 0 else ""

                    print(f"     {Colors.YELLOW}Generated SQL{retry_str}:{Colors.END}")
                    print(f"     ```sql")
                    for line in sql.split('\n'):
                        print(f"     {line}")
                    print(f"     ```")

                elif node == "sql_validator":
                    is_valid = debug_data.get("is_valid", False)
                    feedback = debug_data.get("feedback", "")
                    score = debug_data.get("validation_score", 0)
                    next_step = debug_data.get("next_step", "")

                    status = f"{Colors.GREEN}✅ VALID{Colors.END}" if is_valid else f"{Colors.RED}❌ INVALID{Colors.END}"
                    print(f"     Validation: {status} (score: {score}/100)")
                    if feedback:
                        print(f"     {Colors.YELLOW}Feedback:{Colors.END} {feedback}")
                    if next_step:
                        print(f"     {Colors.YELLOW}Next:{Colors.END} {next_step}")

                elif node == "sql_executor":
                    row_count = debug_data.get("row_count", 0)
                    columns = debug_data.get("columns", [])
                    sample_rows = debug_data.get("sample_rows", [])
                    exec_time = debug_data.get("execution_time_ms", 0)

                    print(f"     {Colors.YELLOW}Query Results:{Colors.END}")
                    print(f"       Rows: {row_count}")
                    print(f"       Columns: {columns}")
                    print(f"       Execution time: {exec_time}ms")

                    if sample_rows:
                        print(f"     {Colors.YELLOW}Sample Data (first 3 rows):{Colors.END}")
                        for i, row in enumerate(sample_rows, 1):
                            print(f"       Row {i}: {row}")

                elif node == "data_interpreter":
                    interpretation = debug_data.get("interpretation", "")
                    interpretation_len = debug_data.get("interpretation_length", 0)

                    print(f"     {Colors.YELLOW}Interpretation ({interpretation_len} chars):{Colors.END}")
                    # Show first 300 characters as preview
                    preview = interpretation[:300] + ("..." if len(interpretation) > 300 else "")
                    for line in preview.split('\n'):
                        print(f"       {line}")

                elif node == "interpretation_validator":
                    is_valid = debug_data.get("is_valid", False)
                    feedback = debug_data.get("feedback", "")
                    score = debug_data.get("validation_score", 0)
                    next_step = debug_data.get("next_step", "")

                    status = f"{Colors.GREEN}✅ VALID{Colors.END}" if is_valid else f"{Colors.RED}❌ INVALID{Colors.END}"
                    print(f"     Validation: {status} (score: {score}/100)")
                    if feedback:
                        print(f"     {Colors.YELLOW}Feedback:{Colors.END} {feedback}")
                    if next_step:
                        print(f"     {Colors.YELLOW}Next:{Colors.END} {next_step}")

            else:
                # Unknown message type - show full data for debugging
                print_warning(f"Unknown message type: {msg_type}")
                print(f"  Full data: {json.dumps(data, indent=2)}")

        except asyncio.TimeoutError:
            print_error("Timeout waiting for response (60s)")
            return
        except Exception as e:
            print_error(f"Error receiving message: {e}")
            return

    # Display final response
    print()
    print_header("FINAL RESPONSE")
    print(final_response)

    # Display semantic layer insights
    if metadata:
        print()
        print_header("SEMANTIC LAYER INSIGHTS")

        # Execution plan
        if "execution_plan" in metadata:
            plan = metadata["execution_plan"]
            print_section("Execution Plan:")
            print(f"  Type: {plan.get('type', 'N/A')}")

            if plan.get('type') == 'out_of_scope':
                print(f"  Reason: Out of scope")
                print(f"  Missing platforms: {plan.get('missing_platforms', [])}")
                print(f"  Available platforms: {plan.get('available_platforms', [])}")

            elif plan.get('type') == 'needs_clarification':
                print(f"  Reason: Ambiguous query")
                print(f"  Ambiguous terms: {plan.get('ambiguous_terms', [])}")
                print(f"  Options provided: {len(plan.get('options', {}))}")

            elif plan.get('type') == 'comparison':
                print(f"  Comparison query detected")
                print(f"  Entities: {plan.get('entities', [])}")

            elif plan.get('type') == 'data_analytics':
                print(f"  Data analytics query")
                platforms = plan.get('platforms', [])
                metrics = plan.get('metrics', [])
                time_period = plan.get('time_period', {})
                print(f"  Platforms: {platforms}")
                print(f"  Metrics: {metrics}")
                print(f"  Time period: {time_period}")

        # Routing decision
        if "routing_decision" in metadata:
            routing = metadata["routing_decision"]
            if routing:  # Only display if routing is not None
                print()
                print_section("Routing Decision:")
                print(f"  Agent: {routing.get('agent', 'N/A')}")
                print(f"  Confidence: {routing.get('confidence', 'N/A')}")

        # SQL information
        if "sql_query" in metadata:
            print()
            print_section("SQL Query:")
            print(f"  {metadata['sql_query']}")

        # Data interpretation info
        if "interpretation_summary" in metadata:
            print()
            print_section("Interpretation Summary:")
            print(f"  {metadata['interpretation_summary']}")

        # Node execution path
        if progress_nodes:
            print()
            print_section("Execution Path:")
            print(f"  {' → '.join(progress_nodes)}")


async def interactive_test_loop():
    """
    Main interactive loop for testing queries.
    """
    print_header("SEMANTIC LAYER INTERACTIVE TESTER")
    print_info(f"Test User ID: {TEST_USER_ID[:12]}...")
    print_info(f"Backend: {BACKEND_URL}")

    # Select conversation mode
    conversation_id, is_new = select_conversation_mode()

    # Create session ID for WebSocket
    session_id = str(uuid.uuid4())

    # Connect to WebSocket
    ws_url = f"{WS_URL}/ws/{TEST_USER_ID}/{session_id}"
    print()
    print_info(f"Connecting to WebSocket...")

    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(ws_url, ssl=ssl_context) as websocket:
            print_success("Connected to WebSocket!")

            # Interactive query loop
            while True:
                print()
                print(f"{Colors.BOLD}{'─'*80}{Colors.END}")
                query = input(f"{Colors.BOLD}Enter query (or 'quit' to exit): {Colors.END}").strip()

                if query.lower() in ['quit', 'exit', 'q']:
                    print_info("Exiting...")
                    break

                if not query:
                    print_warning("Empty query, skipping")
                    continue

                # Send query and display response
                await send_query_and_display_response(websocket, query, conversation_id)

    except Exception as e:
        print_error(f"WebSocket connection failed: {e}")
        import traceback
        print(traceback.format_exc())


def main():
    """Main entry point."""
    try:
        asyncio.run(interactive_test_loop())
    except KeyboardInterrupt:
        print()
        print_info("Interrupted by user")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
