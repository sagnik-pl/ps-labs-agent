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

    # Track response with detailed timing
    completed = False
    final_response = None
    metadata = None
    progress_nodes = []
    start_time = datetime.now()
    stage_times = {}  # Track time per stage

    # Receive messages
    while not completed:
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=600)  # 10 minute timeout
            data = json.loads(message)

            msg_type = data.get("type")
            timestamp = data.get("timestamp", "")

            if msg_type == "started":
                print_info(f"[{timestamp[:19]}] Started processing query")
                print_info(f"Start time: {start_time.strftime('%H:%M:%S.%f')[:-3]}")

            elif msg_type == "progress":
                # Progress data is nested in "data" key
                progress_data = data.get("data", {})
                node = progress_data.get("stage", "unknown")
                progress_pct = progress_data.get("progress", 0)
                retry = data.get("retry_count", 0)  # retry_count is at root level if present
                progress_nodes.append(node)

                # Track stage start time
                if node not in stage_times:
                    stage_times[node] = datetime.now()

                # Calculate elapsed time since query start
                elapsed = (datetime.now() - start_time).total_seconds()

                retry_str = f" (retry {retry})" if retry > 0 else ""
                print(f"  ⏳ [{timestamp[:19]}] [{elapsed:.2f}s elapsed] Progress: {progress_pct}% - {Colors.BOLD}{node}{Colors.END}{retry_str}")

            elif msg_type == "completed":
                # Completed data is nested in "data" key (matching frontend behavior)
                completed_data = data.get("data", {})
                final_response = completed_data.get("response", "")
                metadata = completed_data.get("metadata", {})

                # Calculate total execution time
                end_time = datetime.now()
                total_time = (end_time - start_time).total_seconds()

                print()
                print(f"  {Colors.GREEN}{Colors.BOLD}{'='*76}{Colors.END}")
                print_success(f"[{timestamp[:19]}] Query Completed Successfully!")
                print(f"  {Colors.GREEN}⏱️  Total Execution Time: {Colors.BOLD}{total_time:.2f}s{Colors.END}")
                print(f"  {Colors.GREEN}{Colors.BOLD}{'='*76}{Colors.END}")
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

                # Calculate elapsed time since query start and stage start
                elapsed_total = (datetime.now() - start_time).total_seconds()
                stage_start = stage_times.get(node, start_time)
                elapsed_stage = (datetime.now() - stage_start).total_seconds()

                print()
                print(f"  {Colors.CYAN}{Colors.BOLD}{'='*76}{Colors.END}")
                print(f"  {Colors.CYAN}{Colors.BOLD}🔍 DEBUG - {node.upper()}{Colors.END}")
                print(f"  {Colors.CYAN}⏱️  Total Elapsed: {elapsed_total:.2f}s | Stage Time: {elapsed_stage:.2f}s{Colors.END}")
                print(f"  {Colors.CYAN}{Colors.BOLD}{'='*76}{Colors.END}")

                if node == "planner":
                    exec_plan = debug_data.get("execution_plan", {})
                    routing = debug_data.get("routing_decision", {})
                    classification = debug_data.get("classification", {})
                    decomposition = debug_data.get("decomposition", {})

                    if exec_plan:
                        print(f"     {Colors.YELLOW}📋 Execution Plan:{Colors.END}")
                        print(f"       Type: {exec_plan.get('type', 'N/A')}")
                        if exec_plan.get('platforms'):
                            print(f"       Platforms: {exec_plan.get('platforms')}")
                        if exec_plan.get('metrics'):
                            print(f"       Metrics: {exec_plan.get('metrics')}")
                        if exec_plan.get('time_period'):
                            print(f"       Time Period: {exec_plan.get('time_period')}")

                    # Show query classification (single-intent vs multi-intent)
                    if classification:
                        query_type = classification.get('type', 'N/A')
                        is_multi_intent = query_type == 'multi_intent'

                        print()
                        print(f"     {Colors.YELLOW}{'─'*68}{Colors.END}")
                        print(f"     {Colors.YELLOW}{Colors.BOLD}🔍 QUERY CLASSIFICATION{Colors.END}")
                        print(f"     {Colors.YELLOW}{'─'*68}{Colors.END}")

                        # Highlight multi-intent in GREEN, single-intent in standard
                        type_color = Colors.GREEN if is_multi_intent else Colors.YELLOW
                        type_label = f"{type_color}{Colors.BOLD}{query_type.upper()}{Colors.END}"
                        print(f"       Intent Type: {type_label}")
                        print(f"       Complexity: {classification.get('complexity', 'N/A')}")
                        print(f"       Requires Decomposition: {Colors.BOLD}{classification.get('requires_decomposition', False)}{Colors.END}")

                        if classification.get('reasoning'):
                            print(f"       Reasoning: {classification.get('reasoning')[:250]}")

                    # Show decomposition details (CRITICAL for multi-intent queries)
                    if decomposition and decomposition.get('sub_queries'):
                        sub_queries = decomposition.get('sub_queries', [])
                        original_goal = decomposition.get('original_goal', 'N/A')

                        print()
                        print(f"     {Colors.GREEN}{Colors.BOLD}{'='*68}{Colors.END}")
                        print(f"     {Colors.GREEN}{Colors.BOLD}🎯 MULTI-INTENT QUERY BREAKDOWN{Colors.END}")
                        print(f"     {Colors.GREEN}{Colors.BOLD}{'='*68}{Colors.END}")
                        print()
                        print(f"     {Colors.GREEN}{Colors.BOLD}Original Goal:{Colors.END}")
                        print(f"     {Colors.GREEN}» {original_goal}{Colors.END}")
                        print()
                        print(f"     {Colors.GREEN}{Colors.BOLD}Decomposed into {len(sub_queries)} simpler question(s):{Colors.END}")
                        print()

                        for idx, sq in enumerate(sub_queries, 1):
                            sq_id = sq.get('id', 'N/A')
                            question = sq.get('question', 'N/A')
                            intent = sq.get('intent', 'N/A')
                            deps = sq.get('dependencies', [])
                            exec_order = sq.get('execution_order', 0)

                            print(f"     {Colors.CYAN}{'─'*68}{Colors.END}")
                            print(f"     {Colors.BOLD}{Colors.CYAN}Question {idx}: {sq_id}{Colors.END}")
                            print(f"     {Colors.CYAN}{'─'*68}{Colors.END}")
                            print(f"       {Colors.BOLD}❓ Query:{Colors.END} {question}")
                            print(f"       {Colors.BOLD}🎯 Intent:{Colors.END} {Colors.GREEN}{intent}{Colors.END}")
                            print(f"       {Colors.BOLD}📋 Execution Order:{Colors.END} {exec_order}")
                            if deps:
                                print(f"       {Colors.BOLD}🔗 Dependencies:{Colors.END} {', '.join(deps)}")
                            print()

                        print(f"     {Colors.GREEN}{Colors.BOLD}{'='*68}{Colors.END}")
                        print()

                    if routing:
                        print(f"     {Colors.YELLOW}🔀 Routing Decision:{Colors.END}")
                        print(f"       Agent: {routing.get('agent', 'N/A')}")
                        print(f"       Confidence: {routing.get('confidence', 'N/A')}")

                elif node == "sql_generator":
                    sql = debug_data.get("generated_sql", "")
                    retry = debug_data.get("retry_count", 0)
                    retry_str = f" (retry {retry})" if retry > 0 else ""
                    used_template = debug_data.get("used_template", None)
                    template_name = debug_data.get("template_name", None)
                    metrics_used = debug_data.get("metrics_used", [])
                    tables_used = debug_data.get("tables_filtered", [])

                    print(f"     {Colors.YELLOW}📝 SQL Generation Details:{Colors.END}")

                    # Show template usage (performance optimization)
                    if used_template:
                        print(f"       {Colors.GREEN}⚡ Fast Path: Used Template '{template_name}'{Colors.END}")
                        print(f"         (200-500ms faster than LLM generation)")

                    # Show metrics system improvements
                    if metrics_used:
                        print(f"       {Colors.CYAN}📊 Dual-Mode Metrics Used:{Colors.END}")
                        for metric in metrics_used[:3]:
                            print(f"         • {metric} (Python + SQL)")

                    # Show tables filtered (semantic layer)
                    if tables_used:
                        print(f"       {Colors.CYAN}🗄️  Tables Selected by Semantic Layer:{Colors.END}")
                        for table in tables_used[:5]:
                            print(f"         • {table}")

                    print()
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
                    # Enhanced multi-intent sub-query breakdown with full details
                    sub_results = debug_data.get("sub_query_results", {})
                    original_goal = debug_data.get("original_goal", "")
                    num_sub_queries = len(sub_results)

                    print(f"     {Colors.GREEN}{Colors.BOLD}🔄 MULTI-INTENT EXECUTION RESULTS:{Colors.END}")
                    print(f"     {Colors.GREEN}Original Goal: {original_goal}{Colors.END}")
                    print(f"     {Colors.GREEN}Total Sub-queries: {num_sub_queries}{Colors.END}")
                    print()

                    for idx, (sq_id, result) in enumerate(sub_results.items(), 1):
                        status_icon = "✅" if result.get("execution_status") == "success" else "❌"
                        exec_status = result.get("execution_status", "unknown")

                        print(f"     {Colors.CYAN}{'─'*72}{Colors.END}")
                        print(f"     {status_icon} {Colors.BOLD}{Colors.CYAN}Sub-Query {idx}/{num_sub_queries}: {sq_id}{Colors.END}")
                        print(f"     {Colors.CYAN}{'─'*72}{Colors.END}")

                        print(f"       {Colors.YELLOW}Question:{Colors.END} {result.get('question', 'N/A')}")
                        print(f"       {Colors.YELLOW}Intent:{Colors.END} {result.get('intent', 'N/A')}")
                        print(f"       {Colors.YELLOW}Status:{Colors.END} {exec_status}")

                        # Show SQL query (CRITICAL for debugging)
                        sql = result.get('sql', 'N/A')
                        if sql and sql != 'N/A':
                            print(f"       {Colors.YELLOW}Generated SQL:{Colors.END}")
                            if len(sql) < 400:
                                print(f"       ```sql")
                                for line in sql.split('\n'):
                                    print(f"       {line}")
                                print(f"       ```")
                            else:
                                # Show first few lines for long queries
                                lines = sql.split('\n')
                                print(f"       ```sql")
                                for line in lines[:10]:
                                    print(f"       {line}")
                                print(f"       ... (truncated, {len(lines)} total lines)")
                                print(f"       ```")

                        # Show data snapshot (CRITICAL for understanding results)
                        data = result.get('data', 'No data')
                        print(f"       {Colors.YELLOW}Data Snapshot:{Colors.END}")
                        if isinstance(data, str):
                            if len(data) < 300:
                                print(f"       {data}")
                            else:
                                print(f"       {data[:300]}...")
                                print(f"       (Total length: {len(data)} characters)")
                        elif isinstance(data, dict):
                            # Show structured data
                            try:
                                data_str = json.dumps(data, indent=2)
                                if len(data_str) < 300:
                                    print(f"       {data_str}")
                                else:
                                    print(f"       {data_str[:300]}...")
                            except:
                                print(f"       {str(data)[:300]}...")
                        else:
                            print(f"       {str(data)[:300]}")

                        # Show error if failed
                        if exec_status != "success" and result.get('error'):
                            print(f"       {Colors.RED}Error:{Colors.END} {result.get('error')}")

                        print()

                elif node == "sql_executor":
                    row_count = debug_data.get("row_count", 0)
                    columns = debug_data.get("columns", [])
                    sample_rows = debug_data.get("sample_rows", [])
                    exec_time = debug_data.get("execution_time_ms", 0)
                    query_id = debug_data.get("query_id", "N/A")

                    print(f"     {Colors.YELLOW}📊 Query Execution Results:{Colors.END}")
                    print(f"       Athena Query ID: {query_id}")
                    print(f"       Rows Returned: {Colors.BOLD}{row_count}{Colors.END}")
                    print(f"       Columns: {len(columns)} ({', '.join(columns[:5])}{'...' if len(columns) > 5 else ''})")
                    print(f"       Execution Time: {Colors.BOLD}{exec_time}ms{Colors.END}")

                    # Performance indicator
                    if exec_time < 1000:
                        perf_indicator = f"{Colors.GREEN}⚡ Fast{Colors.END}"
                    elif exec_time < 5000:
                        perf_indicator = f"{Colors.YELLOW}⏱️  Normal{Colors.END}"
                    else:
                        perf_indicator = f"{Colors.RED}🐌 Slow{Colors.END}"
                    print(f"       Performance: {perf_indicator}")

                    if sample_rows and row_count > 0:
                        print(f"     {Colors.YELLOW}📋 Sample Data (first 5 rows):{Colors.END}")
                        for i, row in enumerate(sample_rows[:5], 1):
                            print(f"       Row {i}: {row}")
                        if row_count > 5:
                            print(f"       ... ({row_count - 5} more rows not shown)")
                    elif row_count == 0:
                        print(f"     {Colors.RED}⚠️  No data returned{Colors.END}")

                elif node == "data_interpreter":
                    interpretation = debug_data.get("interpretation", "")
                    interpretation_len = debug_data.get("interpretation_length", 0)
                    knowledge_bases = debug_data.get("knowledge_bases_used", [])
                    is_multi_intent = debug_data.get("is_multi_intent", False)
                    sub_query_count = debug_data.get("sub_query_count", 0)
                    word_count = len(interpretation.split()) if interpretation else 0

                    print(f"     {Colors.YELLOW}💡 Data Interpretation Generated:{Colors.END}")
                    print(f"       Length: {interpretation_len} characters ({word_count} words)")

                    # Show knowledge base improvements
                    if knowledge_bases:
                        print(f"     {Colors.GREEN}✨ Knowledge Bases Used ({len(knowledge_bases)}):{Colors.END}")
                        for kb in knowledge_bases:
                            print(f"       • {kb}")

                    # Show multi-intent handling
                    if is_multi_intent:
                        print(f"     {Colors.GREEN}🔄 Multi-Intent Synthesis Applied:{Colors.END}")
                        print(f"       Sub-queries Synthesized: {sub_query_count}")
                        print(f"       Individual SQL + results shown ✓")
                        print(f"       5-point synthesis requirements applied ✓")
                        print(f"       Cross-referencing and unified narrative ✓")

                    # Show interpretation preview (first 500 chars for better context)
                    print(f"     {Colors.YELLOW}📄 Interpretation Preview:{Colors.END}")
                    preview = interpretation[:500] + ("..." if len(interpretation) > 500 else "")
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
            print_error("Timeout waiting for response (600s / 10 minutes)")
            return
        except Exception as e:
            print_error(f"Error receiving message: {e}")
            return

    # Display final response with timing summary
    print()
    print_header("FINAL RESPONSE")
    print(final_response)

    # Display execution time breakdown
    print()
    print_header("EXECUTION TIME BREAKDOWN")
    if stage_times:
        print_section("Time spent in each stage:")
        total_time = (datetime.now() - start_time).total_seconds()
        for stage, stage_start in stage_times.items():
            # Calculate approximate time (from stage start to next stage or end)
            print(f"  • {stage}: Started at +{(stage_start - start_time).total_seconds():.2f}s")
        print(f"\n  {Colors.BOLD}Total: {total_time:.2f}s{Colors.END}")

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
