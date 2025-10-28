#!/usr/bin/env python3
"""
Interactive WebSocket test script for semantic layer iteration.

This script connects to the production backend and sends test queries,
displaying full semantic layer routing decisions and workflow node execution details.

Features:
- Conversation context handling (new vs existing conversations)
- Real-time progress streaming
- Semantic layer insight extraction
- Interactive query input for rapid iteration

🚀 LATEST DEPLOYMENT (Main Branch):
✨ MODEL UPGRADES:
   - GPT-5 (gpt-5-2025-08-07) for sql_generator_node - Better SQL reasoning
   - GPT-5 (gpt-5-2025-08-07) for data_interpreter_node - Enhanced insights
   - GPT-5 Mini (gpt-5-mini-2025-08-07) for 7 other nodes - Cost efficient
   - Lazy loading: LLM instances load on first use (fast startup)

✨ WORKFLOW NODES (12 Total):
   1. planner_node - Creates execution plan
   2. router_node - Routes to appropriate path
   3. multi_intent_executor_node - Handles multi-intent queries
   4. query_assessment_node - Assesses data availability
   5. sql_generator_node - Generates SQL (GPT-5)
   6. sql_validator_node - Validates SQL correctness
   7. sql_corrector_node - Fixes SQL errors
   8. sql_executor_node - Executes queries on Athena
   9. data_interpreter_node - Interprets results (GPT-5)
   10. interpretation_validator_node - Validates interpretation
   11. output_formatter_node - Formats output
   12. interpreter_node - Final routing/output

✨ IMPROVEMENTS:
   - Lazy loading prevents startup blocking
   - Premium GPT-5 models for critical quality nodes
   - 11 knowledge bases for data interpretation
   - Multi-intent synthesis with sub-query visibility
   - Dual-mode metrics system (Python + SQL)
   - Template fast-path for common queries
   - Semantic column validation
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
            message = await asyncio.wait_for(websocket.recv(), timeout=180)
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
                    used_template = debug_data.get("used_template", None)
                    template_name = debug_data.get("template_name", None)
                    metrics_used = debug_data.get("metrics_used", [])

                    # Show template usage (performance optimization)
                    if used_template:
                        print(f"     {Colors.GREEN}⚡ Fast Path: Used Template '{template_name}'{Colors.END}")
                        print(f"       (200-500ms faster than LLM generation)")

                    # Show metrics system improvements
                    if metrics_used:
                        print(f"     {Colors.CYAN}📊 Dual-Mode Metrics Used:{Colors.END}")
                        for metric in metrics_used[:3]:
                            print(f"       • {metric} (Python + SQL)")

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
                    complexity = debug_data.get("complexity_score", None)
                    column_suggestions = debug_data.get("column_suggestions", {})
                    semantic_errors = debug_data.get("semantic_errors", [])

                    status = f"{Colors.GREEN}✅ VALID{Colors.END}" if is_valid else f"{Colors.RED}❌ INVALID{Colors.END}"
                    print(f"     Validation: {status} (score: {score}/100)")

                    # Show complexity analysis
                    if complexity is not None:
                        complexity_color = Colors.GREEN if complexity <= 5 else Colors.YELLOW if complexity <= 7 else Colors.RED
                        print(f"     {complexity_color}Complexity Score: {complexity}/10{Colors.END}")

                    # Show semantic column validation improvements
                    if column_suggestions:
                        print(f"     {Colors.CYAN}📋 Column Suggestions (Semantic Validation):{Colors.END}")
                        for wrong, correct in list(column_suggestions.items())[:3]:
                            print(f"       '{wrong}' → '{correct}'")

                    if semantic_errors:
                        print(f"     {Colors.YELLOW}⚠️  Semantic Errors Detected:{Colors.END}")
                        for error in semantic_errors[:2]:
                            print(f"       • {error}")

                    if feedback:
                        print(f"     {Colors.YELLOW}Feedback:{Colors.END} {feedback[:200]}")
                    if next_step:
                        print(f"     {Colors.YELLOW}Next:{Colors.END} {next_step}")

                elif node == "multi_intent_executor":
                    # NEW: Show multi-intent sub-query breakdown
                    sub_results = debug_data.get("sub_query_results", {})
                    original_goal = debug_data.get("original_goal", "")
                    num_sub_queries = len(sub_results)

                    print(f"     {Colors.YELLOW}Multi-Intent Execution:{Colors.END}")
                    print(f"       Original Goal: {original_goal}")
                    print(f"       Sub-queries: {num_sub_queries}")
                    print()

                    for sq_id, result in sub_results.items():
                        status_icon = "✅" if result.get("execution_status") == "success" else "❌"
                        print(f"       {status_icon} {Colors.BOLD}{sq_id}{Colors.END}: {result.get('question', 'N/A')}")
                        print(f"          Intent: {result.get('intent', 'N/A')}")

                        sql = result.get('sql', 'N/A')
                        if sql and sql != 'N/A' and len(sql) < 200:
                            print(f"          SQL: {sql}")
                        elif sql and sql != 'N/A':
                            print(f"          SQL: {sql[:100]}... (truncated)")

                        data = result.get('data', 'No data')
                        if isinstance(data, str) and len(data) < 150:
                            print(f"          Data: {data}")
                        elif isinstance(data, str):
                            print(f"          Data: {data[:150]}... (truncated)")
                        print()

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
                    knowledge_bases = debug_data.get("knowledge_bases_used", [])
                    is_multi_intent = debug_data.get("is_multi_intent", False)
                    sub_query_count = debug_data.get("sub_query_count", 0)

                    print(f"     {Colors.YELLOW}Interpretation ({interpretation_len} chars):{Colors.END}")

                    # Show knowledge base improvements
                    if knowledge_bases:
                        print(f"     {Colors.GREEN}✨ Knowledge Bases Used ({len(knowledge_bases)}):{Colors.END}")
                        for kb in knowledge_bases:
                            print(f"       • {kb}")

                    # Show multi-intent handling
                    if is_multi_intent:
                        print(f"     {Colors.GREEN}🔄 Multi-Intent Query Detected:{Colors.END}")
                        print(f"       Sub-queries: {sub_query_count}")
                        print(f"       Individual SQL + results shown ✓")
                        print(f"       Synthesis requirements applied ✓")

                    # Show first 300 characters as preview
                    preview = interpretation[:300] + ("..." if len(interpretation) > 300 else "")
                    for line in preview.split('\n'):
                        print(f"       {line}")

                elif node == "interpretation_validator":
                    is_valid = debug_data.get("is_valid", False)
                    feedback = debug_data.get("feedback", "")
                    score = debug_data.get("validation_score", 0)
                    next_step = debug_data.get("next_step", "")
                    criteria_passed = debug_data.get("criteria_passed", [])
                    criteria_failed = debug_data.get("criteria_failed", [])
                    is_multi_intent = debug_data.get("is_multi_intent", False)
                    synthesis_quality = debug_data.get("synthesis_quality", None)

                    status = f"{Colors.GREEN}✅ VALID{Colors.END}" if is_valid else f"{Colors.RED}❌ INVALID{Colors.END}"
                    print(f"     Validation: {status} (score: {score}/100)")

                    # Show priority-based validation
                    if criteria_passed:
                        print(f"     {Colors.GREEN}✓ Criteria Passed:{Colors.END}")
                        for i, criterion in enumerate(criteria_passed[:3], 1):
                            marker = "⭐" if i == 1 else "✓"
                            print(f"       {marker} {criterion}")

                    if criteria_failed:
                        print(f"     {Colors.RED}✗ Criteria Failed:{Colors.END}")
                        for criterion in criteria_failed:
                            print(f"       ✗ {criterion}")

                    # Show multi-intent synthesis validation
                    if is_multi_intent and synthesis_quality:
                        print(f"     {Colors.CYAN}🔗 Multi-Intent Synthesis Quality:{Colors.END}")
                        print(f"       Stitching: {synthesis_quality.get('stitching', 'N/A')}")
                        print(f"       Cross-referencing: {synthesis_quality.get('cross_referencing', 'N/A')}")
                        print(f"       Unified narrative: {synthesis_quality.get('unified_narrative', 'N/A')}")

                    if feedback:
                        print(f"     {Colors.YELLOW}Feedback:{Colors.END} {feedback[:200]}")
                    if next_step:
                        print(f"     {Colors.YELLOW}Next:{Colors.END} {next_step}")

            else:
                # Unknown message type - show full data for debugging
                print_warning(f"Unknown message type: {msg_type}")
                print(f"  Full data: {json.dumps(data, indent=2)}")

        except asyncio.TimeoutError:
            print_error("Timeout waiting for response (180s)")
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

        # NEW: Display improvement highlights
        print()
        print_section(f"{Colors.GREEN}✨ Improvement Highlights:{Colors.END}")

        improvements_shown = []

        # Check for knowledge base usage
        if "knowledge_bases_count" in metadata:
            kb_count = metadata["knowledge_bases_count"]
            improvements_shown.append(f"  ✓ Used {kb_count} knowledge bases (was 7)")

        # Check for multi-intent handling
        if "is_multi_intent" in metadata and metadata["is_multi_intent"]:
            improvements_shown.append(f"  ✓ Multi-intent synthesis with individual SQL visibility")

        # Check for template usage
        if "used_template" in metadata and metadata["used_template"]:
            improvements_shown.append(f"  ✓ Fast-path template used (200-500ms saved)")

        # Check for metrics usage
        if "metrics_used" in metadata and metadata["metrics_used"]:
            metrics_count = len(metadata["metrics_used"])
            improvements_shown.append(f"  ✓ Dual-mode metrics: {metrics_count} metric(s)")

        # Check for validation improvements
        if "validation_improvements" in metadata:
            improvements_shown.append(f"  ✓ Priority-based validation applied")

        # Check for semantic validation
        if "semantic_validation" in metadata and metadata["semantic_validation"]:
            improvements_shown.append(f"  ✓ Semantic column validation performed")

        if improvements_shown:
            for improvement in improvements_shown:
                print(improvement)
        else:
            print(f"  {Colors.YELLOW}No specific improvements detected in this query{Colors.END}")
            print(f"  {Colors.YELLOW}(Try multi-intent queries or metric calculations){Colors.END}")


async def interactive_test_loop():
    """
    Main interactive loop for testing queries.
    """
    print_header("SEMANTIC LAYER INTERACTIVE TESTER")
    print_info(f"Test User ID: {TEST_USER_ID[:12]}...")
    print_info(f"Backend: {BACKEND_URL}")

    # Display recent improvements
    print()
    print_section("✨ Recent Improvements:")
    print(f"  {Colors.GREEN}1. DATA INTERPRETER NODE:{Colors.END}")
    print(f"     • 11 knowledge bases (was 7) - 57% more domain knowledge")
    print(f"     • Multi-intent: Shows individual SQL + data before synthesis")
    print(f"     • 5-point synthesis requirements for cohesive narratives")
    print()
    print(f"  {Colors.GREEN}2. INTERPRETATION VALIDATOR NODE:{Colors.END}")
    print(f"     • Priority-based criteria: 'Answers Question' is #1 (most critical)")
    print(f"     • Multi-intent synthesis quality validation (Criterion #9)")
    print(f"     • Checks stitching, cross-referencing, unified recommendations")
    print()
    print(f"  {Colors.GREEN}3. METRICS SYSTEM:{Colors.END}")
    print(f"     • Dual-mode Python metrics (Python + SQL from same definition)")
    print(f"     • Type-safe SQL with NULLIF and CAST protection")
    print(f"     • 9 metrics: engagement_rate, frequency, ROAS, CAC, etc.")
    print()
    print(f"  {Colors.GREEN}4. SQL GENERATION & VALIDATION:{Colors.END}")
    print(f"     • Template matching (200-500ms faster)")
    print(f"     • Semantic column validation with correction suggestions")
    print(f"     • Complexity analysis (0-10 score)")
    print()

    # Suggested test queries
    print_section(f"{Colors.CYAN}💡 Suggested Test Queries:{Colors.END}")
    print(f"  {Colors.YELLOW}Multi-Intent:{Colors.END}")
    print(f"     • 'How's my Instagram performance and what should I improve?'")
    print(f"     • 'Show my engagement rate and posting frequency'")
    print()
    print(f"  {Colors.YELLOW}Metrics Calculation:{Colors.END}")
    print(f"     • 'Calculate my engagement rate for last 30 days'")
    print(f"     • 'What's my conversion rate on the website?'")
    print()
    print(f"  {Colors.YELLOW}Template Fast-Path:{Colors.END}")
    print(f"     • 'Show my top performing posts'")
    print(f"     • 'What are my best selling products?'")
    print()
    print(f"  {Colors.YELLOW}Knowledge Base Usage:{Colors.END}")
    print(f"     • 'How can I improve my Instagram reach?'")
    print(f"     • 'Analyze my social media strategy'")
    print()

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
