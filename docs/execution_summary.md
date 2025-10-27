# Execution Flow Summary

**Example Query**: "Hows the instagram performance in the last 30 days"

This document traces the complete execution flow from receiving a user message to returning the final response.

---

## 1. WebSocket Connection & Message Receipt

**File**: `./api_websocket.py`

### 1.1 WebSocket Connection Established
- **Line 127-136**: `websocket_endpoint()` - FastAPI WebSocket endpoint accepts connection
- **Line 136**: `manager.connect()` - Registers WebSocket connection with session_id
- Creates connection for real-time bidirectional communication

### 1.2 Message Received
- **Line 139-141**: Receive JSON message from client via `websocket.receive_json()`
- **Line 143-149**: Extract message components:
  - `query` - User's question ("Hows the instagram performance in the last 30 days")
  - `conversation_id` - Thread identifier for context tracking
  - `debug_mode` - Optional flag for detailed progress streaming

### 1.3 Send "Started" Event
- **Line 163-169**: Send progress event to frontend
- Creates immediate user feedback that query is being processed

---

## 2. Query Processing Initialization

**File**: `./api_websocket.py`

### 2.1 Check if New Conversation
- **Line 211**: `firebase_client.is_new_conversation()` - Check if conversation exists
- Determines if we need to generate a title

### 2.2 Generate Conversation Title (if new)
- **Line 218**: `generate_conversation_title(query)`
- **File**: `./utils/title_generator.py`
- Uses GPT-4o-mini to create 2-4 word title from query
- Sends `conversation_metadata` event to frontend with title & date

### 2.3 Load Conversation Context
- **Line 240**: `firebase_client.get_context_summary(user_id, conversation_id)`
- **File**: `./utils/firebase_client.py`
- Retrieves last 10 messages from Firestore
- Summarizes conversation history for LLM context

### 2.4 Load User Profile
- **Line 249**: `firebase_client.get_user_profile(user_id)`
- **File**: `./utils/firebase_client.py`
- Loads business profile, goals, preferences from Firestore
- Contains brand info, target audience, KPIs for personalization

### 2.5 Save User Message to Firestore
- **Line 258**: `firebase_client.save_message(user_id, conversation_id, "user", query)`
- Persists message for conversation history
- Includes conversation title if new conversation

---

## 3. Workflow Initialization

**File**: `./api_websocket.py`

### 3.1 Prepare Initial State
- **Line 270-283**: Build `initial_state` dictionary containing:
  - `user_id` - For data isolation (CRITICAL security)
  - `conversation_id` - For context tracking
  - `user_profile` - Business profile for personalization
  - `query` - User's question
  - `context` - Conversation history summary
  - `messages` - LangChain message list
  - `agent_results`, `metadata` - Empty dicts for results
  - `retry_count`, `interpretation_retry_count`, `sql_retry_count` - Retry counters

### 3.2 Create Workflow
- **Line 286**: `workflow = create_agent_workflow()`
- **File**: `./workflow/graph.py`
- **Line 11**: `create_agent_workflow()` - Constructs LangGraph StateGraph
- Builds DAG (Directed Acyclic Graph) of processing nodes

### 3.3 Configure Checkpointing
- **Line 289-293**: Setup config with `thread_id` for state persistence
- Allows resuming interrupted workflows

---

## 4. Workflow Execution - Node Streaming

**File**: `./api_websocket.py`

### 4.1 Stream Workflow Events
- **Line 301**: `workflow.astream(initial_state, config=config)`
- Executes workflow graph node-by-node
- Yields events for each node completion

### 4.2 Process Each Node Event
- **Line 308-329**: For each node completion:
  - Extract node name and output state
  - Send progress update via WebSocket
  - Extract retry counts for display
  - Log node execution

### 4.3 Send Debug Information (if enabled)
- **Line 332-375**: For specific nodes, send detailed debug data:
  - **planner**: execution_plan, routing_decision
  - **sql_generator**: generated SQL, retry count
  - **sql_validator**: validation results, feedback
  - **sql_executor**: query results, row count
  - **data_interpreter**: interpretation length
  - **interpretation_validator**: validation score

---

## 5. PLANNER NODE - Query Analysis & Routing

**File**: `./workflow/nodes.py`

### 5.1 Import Semantic Layer Utilities
- **Line 42**: Import semantic layer detection functions
- **Line 43**: Import query splitter for comparison queries

### 5.2 Check 0: Data Inquiry Detection
- **Line 51**: `detect_data_inquiry_query(query)` - Checks if asking ABOUT data
- **File**: `./utils/semantic_layer.py` (not shown, but referenced)
- Examples: "what data do you have?", "do you track Instagram?"
- **If inquiry detected**: Return informative message, END workflow early
- **Line 56-66**: Return state with `next_step: "END"`, skips rest of workflow

### 5.3 Check 1: Out-of-Scope Data Detection
- **Line 70**: `check_data_availability(query)` - Validates data platform exists
- **File**: `./utils/semantic_layer.py`
- Checks if asking for TikTok, YouTube, or other unavailable platforms
- **If unavailable**: Return helpful message suggesting available platforms
- **Line 75-86**: Return with `next_step: "END"`, provide alternative suggestions

### 5.4 Check 2: Ambiguous Query Detection
- **Line 90**: `detect_ambiguous_query(query)` - Checks for vague terms
- Examples: "performance", "engagement" without specifying platform/metric
- **If ambiguous**: Generate clarification question with options
- **Line 105-117**: Format options, return with `next_step: "END"`

### 5.5 Check 3: Comparison Query Detection
- **Line 121**: `detect_comparison_query(query)` - Detects "X vs Y" patterns
- Examples: "last week vs this week", "posts vs reels"
- **If comparison detected**:
  - **Line 127**: Split into parallel sub-queries
  - **Line 136-147**: Return `next_step: "parallel_execute"`
  - Routes to parallel execution for speedup

### 5.6 Format User Profile Context
- **Line 153-156**: `format_profile_for_prompt(user_profile)`
- **File**: `./utils/profile_defaults.py`
- Converts profile dict to readable text for LLM injection

### 5.7 Generate Execution Plan
- **Line 159**: Load planner prompt from prompt manager
- **File**: `./prompts/prompt_manager.py`
- **Line 169**: Invoke GPT-4o with query + context + profile
- **Line 172**: Parse JSON response with execution steps

### 5.8 Return Plan
- **Line 189-193**: Return plan with `next_step: "router"`
- Plan includes: steps, agents needed, complexity estimate

---

## 6. ROUTER NODE - Agent Selection

**File**: `./workflow/nodes.py`

### 6.1 Extract Plan
- **Line 205**: Get execution plan from state
- **Line 209**: Extract first step from plan

### 6.2 Determine Primary Agent
- **Line 218-224**: Map agent name to node name
- For data queries: route to `data_analytics_agent`
- Currently only one agent, but designed for expansion

### 6.3 Return Routing Decision
- **Line 227-231**: Return with:
  - `current_agent` - Selected agent name
  - `next_step` - Next node to execute (e.g., "data_analytics_agent")

**Note**: Currently routes to SQL generator directly for data analytics

---

## 7. SQL GENERATOR NODE - Query Translation

**File**: `./workflow/nodes.py`

### 7.1 Import SQL Tools & Templates
- **Line 608**: Import Athena tools (list_tables, table_schema)
- **Line 609**: Import semantic_layer for schema info
- **Line 610**: Import sql_templates for optimized queries

### 7.2 STEP 1: Try Template Matching (Performance Optimization)
- **Line 621**: `suggest_template(query)` - Check if query matches pre-built template
- **File**: `./utils/sql_templates.py`
- Templates are hand-optimized SQL for common queries
- **Examples**: "top posts by engagement", "follower growth", "content performance"

### 7.3 If Template Found:
- **Line 629**: Get template metadata with parameters
- **Line 636-650**: Extract parameters from query text:
  - **Time period**: Regex search for "30 days", "7 days", "last week"
  - **Limit**: Extract "top 5", "first 10"
- **Line 653**: Generate SQL from template with parameters
- **Line 656-664**: If successful, return validated SQL immediately
  - **BENEFIT**: Faster (no LLM call), more reliable (tested SQL)

### 7.4 STEP 2: LLM-Based SQL Generation (Fallback)
- **Line 673**: `list_tables_tool.invoke({"user_id": user_id})`
- Gets available tables for this user from AWS Glue Catalog

### 7.5 Get Enhanced Schema Information
- **Line 678-688**: For Instagram queries:
  - **Line 681**: `semantic_layer.get_schema_for_sql_gen(table_name)`
    - **File**: `./config/semantic_layer/schemas.yaml`
    - Provides column descriptions, types, notes
    - Example: "saved" column (not "saves" - common mistake)
  - **Line 684**: `table_schema_tool.invoke()` - Get Athena schema
  - Combines both for comprehensive context

### 7.6 Add Pattern Hints
- **Line 693-702**: If template was found but couldn't use:
  - Include pattern structure as example
  - Helps LLM generate similar query

### 7.7 Generate SQL with LLM
- **Line 705**: Load sql_generator prompt from prompt manager
- **Prompt includes**:
  - User query
  - user_id (for filter enforcement)
  - Table schemas with descriptions
  - Validation feedback (if retry)
  - Pattern hints (if available)
- **Line 716**: Invoke GPT-4o to generate SQL

### 7.8 Clean SQL Response
- **Line 719-724**: Remove markdown code fences (```sql)
- Extract pure SQL text

### 7.9 Return Generated SQL
- **Line 726-730**: Return state with:
  - `generated_sql` - SQL query string
  - `table_schemas` - Schema info used
  - Optional: `used_template`, `template_params` (if from template)

---

## 8. SQL VALIDATOR NODE - Query Verification

**File**: `./workflow/nodes.py`

### 8.1 Import Validation Utilities
- **Line 750**: Import semantic_layer for column validation
- **Line 751-756**: Import sql_analyzer utilities:
  - `calculate_complexity` - Analyze query performance impact
  - `check_required_filters` - Ensure user_id, required filters
  - `get_optimization_hints` - Suggest improvements
  - `validate_syntax_basic` - Basic SQL syntax check
  - **File**: `./utils/sql_analyzer.py`

### 8.2 STEP 1: Basic Syntax Validation
- **Line 768**: `validate_syntax_basic(generated_sql)`
- Checks for:
  - Balanced parentheses
  - SQL keywords present (SELECT, FROM)
  - No obvious syntax errors
- **If fails**: Return immediately with `next_step: "retry_sql"`
- **Line 771-781**: Return feedback to sql_generator for fix

### 8.3 STEP 2: Complexity Analysis
- **Line 784**: `calculate_complexity(generated_sql)`
- **File**: `./utils/sql_analyzer.py`
- Scores query on scale 0-10 based on:
  - Number of JOINs
  - Subqueries
  - Aggregations
  - Window functions
  - CASE statements
- **Line 785**: `get_optimization_hints()`
- Provides specific suggestions (add indexes, reduce joins, etc.)
- **Line 787**: Log complexity score

### 8.4 STEP 3: Required Filters Check
- **Line 791-795**: Determine primary table (instagram_media or instagram_media_insights)
- **Line 795**: `check_required_filters(generated_sql, primary_table)`
- **File**: `./utils/sql_analyzer.py`
- Checks for:
  - **user_id filter** (CRITICAL for data isolation)
  - Date range filter (performance)
  - Platform filter if needed
- **If missing**: Add to warnings

### 8.5 STEP 4: Semantic Layer Column Validation
- **Line 804-825**: For Instagram queries:
  - **Line 806**: `semantic_layer.validate_sql_columns(sql, table_name)`
  - **File**: `./utils/semantic_layer.py`
  - Cross-references SQL columns against schema definitions
  - **Common mistakes caught**:
    - "saves" � should be "saved"
    - "likes" � should be "like_count"
    - "comments" � should be "comments_count"
  - **Line 811-825**: If invalid columns found:
    - Generate suggestions dict
    - Format error message with corrections
    - Add to semantic_validation list

### 8.6 STEP 5: Compile Validation Feedback
- **Line 828-850**: Build comprehensive feedback:
  - **Line 831**: Format complexity report with score
  - **Line 835-837**: Add missing filter warnings
  - **Line 840-841**: Add column validation errors
  - **Line 844-848**: If high complexity (e7), add warning

### 8.7 LLM Validation Call
- **Line 853**: Load sql_validator prompt
- **Prompt includes**:
  - User's original query
  - Generated SQL
  - Table schemas
  - user_id requirement
  - Previous feedback + semantic feedback
- **Line 866**: Invoke GPT-4o for validation decision
- **LLM checks**:
  - Does SQL answer the query?
  - Are all columns valid?
  - Is user_id filter present?
  - Any security issues?
  - Performance concerns?

### 8.8 Parse Validation Response
- **Line 870-902**: Parse JSON response with fallback:
  - Try direct JSON parse
  - Try extracting from markdown code blocks
  - Default to "valid" if parsing fails

### 8.9 Determine Retry Decision
- **Line 905-909**: Check if retry needed:
  - SQL is invalid AND
  - retry_count < max_retries (3)
- **Line 912-917**: Add complexity data to validation result

### 8.10 Return Validation Result
- **Line 919-925**: Return state with:
  - `sql_validation` - Full validation dict with complexity
  - `sql_validation_feedback` - Feedback for retry
  - `sql_retry_count` - Incremented if retry
  - `next_step` - "retry_sql" or "execute_sql"

**If next_step is "retry_sql"**: Loop back to SQL Generator Node with feedback

---

## 9. SQL EXECUTOR NODE - Query Execution

**File**: `./workflow/nodes.py`

### 9.1 Import Execution Tools
- **Line 940**: Import athena_query_tool
- **File**: `./tools/athena_tools.py`
- Wrapper around boto3 Athena client

### 9.2 Setup Retry Configuration
- **Line 949-952**: Configure retry parameters:
  - `max_retries`: 3 attempts
  - `base_delay`: 1 second
  - Exponential backoff (1s, 2s, 4s)

### 9.3 Define Retryable Error Checker
- **Line 954-966**: `is_retryable_error()` function
- Checks error message for transient issues:
  - timeout, network errors
  - throttling, rate limits
  - connection failures
  - service exceptions

### 9.4 Retry Loop
- **Line 968**: Begin retry loop (up to 3 attempts)

### 9.5 Execute SQL Query
- **Line 974**: `athena_query_tool.invoke({"query": generated_sql, "user_id": user_id})`
- **File**: `./tools/athena_tools.py`
- **Process**:
  1. Submit query to AWS Athena
  2. Poll for completion (with timeout)
  3. Fetch results from S3
  4. Format as structured data (rows + columns)
- **Security**: user_id scoping enforced at Athena IAM level

### 9.6 Check for Success
- **Line 980-982**: Check if result is error string
- **If error**: Raise exception to trigger retry logic

### 9.7 Return Successful Result
- **Line 985-998**: Return state with:
  - `user_id` - CRITICAL: Maintained for data isolation
  - `query` - Original user query
  - `agent_results` - Dict with:
    - agent: "sql_executor"
    - result: Formatted data
    - sql_query: Executed SQL
    - status: "completed"
    - retry_count: Number of attempts
  - `raw_data` - Result string for interpretation
  - `execution_status` - "success" marker

### 9.8 Handle Errors
- **Line 1000-1067**: Exception handler:
  - **Line 1002-1008**: Log detailed error info
  - **Line 1011**: Check if error is retryable
  - **Line 1013-1019**: If retryable:
    - Calculate exponential backoff delay
    - Sleep and retry
  - **Line 1020-1067**: If not retryable or max retries:
    - **Line 1029-1046**: Categorize error type:
      - `data_not_found` - No data in S3
      - `sql_syntax` - SQL error
      - `timeout` - Query took too long
      - `permission` - Access denied
      - `transient` - Temporary issue
      - `unknown` - Other errors
    - **Line 1050-1067**: Return error state:
      - `execution_status`: "error"
      - `error_message`: User-friendly message
      - `agent_results` with error details
      - Includes helpful suggestions based on category

---

## 10. DATA INTERPRETER NODE - Result Analysis

**File**: `./workflow/nodes.py`

### 10.1 Check for Execution Errors
- **Line 367-393**: If `execution_status == "error"`:
  - **Line 375**: Format user-friendly error response
  - **Line 382-388**: Add helpful suggestions by error category
  - **Line 389-393**: Return error interpretation
  - **Mark**: `interpretation_is_error: True`
  - Skip LLM interpretation of errors

### 10.2 Format User Profile Context
- **Line 405-408**: `format_profile_for_prompt(user_profile)`
- Inject business context for personalized interpretation

### 10.3 Load Interpretation Prompt
- **Line 411**: Load data_interpreter prompt
- **Prompt variables**:
  - `query` - Original user question
  - `raw_data` - SQL execution results
  - `context` - Conversation history
  - `feedback` - Interpretation feedback (if retry)
  - `profile_context` - Business profile
  - `user_id` - For SQL examples

### 10.4 Prompt Structure (from prompts/)
The data_interpreter prompt includes:
1. **E-commerce Knowledge Base**:
   - Industry benchmarks (engagement rates, CTRs)
   - Best practices
   - Common patterns and trends
2. **Metric Definitions**:
   - From `config/semantic_layer/metrics.yaml`
   - Proper calculation formulas
   - Context on what's "good" vs "bad"
3. **Schema Knowledge**:
   - From `config/semantic_layer/schemas.yaml`
   - Column descriptions and relationships
4. **Interpretation Guidelines**:
   - Provide context and benchmarks
   - Explain WHY metrics matter
   - Give actionable recommendations
   - Use markdown formatting

### 10.5 Invoke LLM for Interpretation
- **Line 424**: Invoke GPT-4o with interpretation prompt
- LLM analyzes data with e-commerce expertise

### 10.6 Return Interpretation
- **Line 428-432**: Return state with:
  - `data_interpretation` - Rich, contextualized analysis
  - `interpretation_is_error`: False (success marker)

---

## 11. INTERPRETATION VALIDATOR NODE - Quality Check

**File**: `./workflow/nodes.py`

### 11.1 Skip Validation for Errors
- **Line 451-463**: If `interpretation_is_error == True`:
  - Skip validation (don't validate error messages)
  - Return with `is_valid: True`
  - `next_step`: "final_interpreter"

### 11.2 Load Validation Prompt
- **Line 470**: Load interpretation_validator prompt
- **Prompt variables**:
  - `query` - User's question
  - `raw_data` - Original data
  - `interpretation` - LLM's analysis

### 11.3 Prompt Validation Criteria
The validator checks if interpretation:
1. **Has proper context**: Includes benchmarks, industry standards
2. **Provides insights**: Not just data regurgitation
3. **Uses e-commerce knowledge**: References relevant concepts
4. **Fully answers query**: Addresses all parts of question
5. **Is actionable**: Includes recommendations or next steps
6. **Well-structured**: Uses markdown, clear sections

### 11.4 Invoke LLM Validator
- **Line 480**: Invoke GPT-4o for quality assessment
- Returns JSON with validation results

### 11.5 Parse Validation Response
- **Line 483-516**: Parse JSON with robust fallback:
  - Try direct JSON parse
  - Try extracting from markdown blocks
  - Default to "valid" if parsing fails

### 11.6 Determine Retry Decision
- **Line 519-523**: Check if retry needed:
  - Interpretation is invalid AND
  - retry_count < max_retries (2)
- **Lower retries than SQL (2 vs 3) since interpretation is subjective**

### 11.7 Return Validation Result
- **Line 525-530**: Return state with:
  - `interpretation_validation` - Quality scores and feedback
  - `interpretation_feedback` - Specific improvement suggestions
  - `interpretation_retry_count` - Incremented if retry
  - `next_step` - "retry_interpretation" or "output_formatter"

**If next_step is "retry_interpretation"**: Loop back to Data Interpreter with feedback

---

## 12. OUTPUT FORMATTER NODE - Response Formatting

**File**: `./workflow/nodes.py`

### 12.1 Skip Formatting for Errors
- **Line 553-561**: If `interpretation_is_error == True`:
  - Pass through interpretation as-is
  - Don't apply formatting to error messages

### 12.2 Load Formatter Prompt
- **Line 568**: Load output_formatter prompt
- **Prompt variables**:
  - `query` - User's question
  - `interpretation` - Validated interpretation
  - `raw_data` - Original data

### 12.3 Formatting Guidelines (from prompt)
The formatter structures response with:
1. **Clear sections**: Use markdown headers (##, ###)
2. **Data tables**: Format comparisons in tables
3. **Bullet points**: Key insights in bullets
4. **Visual formatting**: Bold for emphasis, proper spacing
5. **Action items**: Numbered recommendations at end
6. **Readability**: Short paragraphs, scannable layout

### 12.4 Invoke LLM Formatter
- **Line 578**: Invoke GPT-4o for formatting
- Creates polished, professional output

### 12.5 Return Formatted Output
- **Line 584-587**: Return state with:
  - `formatted_output` - Final formatted response

---

## 13. INTERPRETER NODE - Final Assembly

**File**: `./workflow/nodes.py`

### 13.1 Select Final Response
- **Line 330-336**: Choose response source:
  - **Priority 1**: `formatted_output` (if available)
  - **Priority 2**: `data_interpretation` (fallback)
  - **Priority 3**: "No response generated" (error case)

### 13.2 Build Metadata
- **Line 342-348**: Compile metadata:
  - `plan` - Execution plan
  - `routing` - Routing decision
  - `validation` - Validation results
  - `interpretation_validation` - Quality scores

### 13.3 Return Final Response
- **Line 338-348**: Return state with:
  - `final_response` - Complete user-facing response
  - `messages` - LangChain message history
  - `next_step`: "end"
  - `metadata` - Debug info

---

## 14. Response Delivery

**File**: `./api_websocket.py`

### 14.1 Extract Final Response
- **Line 392-399**: Extract final response with fallback logic:
  - Try `final_response` field
  - Try `execution_plan.message` (early exits)
  - Try `formatted_output`
  - Try `data_interpretation`
  - Last resort: "No response generated"

### 14.2 Build Response Metadata
- **Line 402-408**: Compile metadata for frontend:
  - execution_plan details
  - routing_decision
  - Any additional debug info

### 14.3 Save Response to Firestore
- **Line 418**: `firebase_client.save_message(user_id, conversation_id, "assistant", final_response)`
- Persist response for conversation history
- Includes metadata for debugging

### 14.4 Send Completed Event
- **Line 440**: `manager.send_completed(session_id, final_response, metadata)`
- **Line 98-102**: Creates WebSocket event:
  - type: "completed"
  - data: { response, metadata }
  - timestamp: ISO format

### 14.5 Frontend Receives Response
- WebSocket message arrives at frontend
- Frontend displays response in chat UI
- Conversation history updated

---

## Summary: Complete Flow for "Hows the instagram performance in the last 30 days"

1. **WebSocket** (./api_websocket.py:127) - Connection established
2. **Message Receipt** (./api_websocket.py:141) - Query received
3. **Context Loading** (./api_websocket.py:240) - Last 10 messages from Firestore
4. **Profile Loading** (./api_websocket.py:249) - Business profile from Firestore
5. **Workflow Init** (./api_websocket.py:286) - Create LangGraph workflow
6. **Planner** (./workflow/nodes.py:26) - Semantic layer checks, query analysis
7. **Router** (./workflow/nodes.py:195) - Route to data analytics agent
8. **SQL Generator** (./workflow/nodes.py:589) - Template matching → LLM generation
9. **SQL Validator** (./workflow/nodes.py:732) - Syntax, complexity, semantic validation
10. **SQL Executor** (./workflow/nodes.py:927) - Run query on Athena with retries
11. **Data Interpreter** (./workflow/nodes.py:350) - E-commerce analysis with context
12. **Interpretation Validator** (./workflow/nodes.py:434) - Quality check
13. **Output Formatter** (./workflow/nodes.py:532) - Markdown formatting
14. **Interpreter** (./workflow/nodes.py:316) - Final assembly
15. **Response Delivery** (./api_websocket.py:440) - WebSocket send + Firestore save

---

## Key Performance Optimizations

1. **SQL Templates** (./workflow/nodes.py:621) - Pre-optimized queries skip LLM call
2. **Semantic Layer** (./workflow/nodes.py:681) - Reduces validation errors, fewer retries
3. **Complexity Analysis** (./workflow/nodes.py:784) - Catches performance issues early
4. **Parallel Execution** (./workflow/nodes.py:1069) - Comparison queries run concurrently
5. **Retry with Backoff** (./workflow/nodes.py:968) - Handles transient failures
6. **Streaming Progress** (./api_websocket.py:301) - User sees real-time updates

---

## Key Reliability Features

1. **User Isolation** (./workflow/nodes.py:986) - user_id enforced at all data access points
2. **Error Categorization** (./workflow/nodes.py:1029) - Specific, helpful error messages
3. **Validation Loops** (./workflow/nodes.py:905) - SQL and interpretation quality gates
4. **Context Compression** (./utils/firebase_client.py) - Summarizes long conversations
5. **State Preservation** (./workflow/nodes.py:56) - Early exits maintain required fields
6. **Graceful Degradation** (./workflow/nodes.py:483) - Defaults if parsing fails

---

## Areas for Improvement

### 1. **Query Planning Optimization**
- **Current**: Single LLM call for planning (./workflow/nodes.py:169)
- **Improvement**: Cache common query patterns, skip LLM for simple queries
- **Impact**: 200-500ms savings on simple queries

### 2. **SQL Generation Speed**
- **Current**: Template matching then LLM fallback (./workflow/nodes.py:621-730)
- **Improvement**: Expand template library, add fuzzy matching
- **Impact**: More queries hit fast path, fewer LLM calls

### 3. **Semantic Layer Utilization**
- **Current**: Loaded per-query (./workflow/nodes.py:681)
- **Improvement**: Pre-embed schemas, use vector search for relevant columns
- **Impact**: Better column selection, fewer validation errors

### 4. **Interpretation Caching**
- **Current**: Full interpretation every time (./workflow/nodes.py:424)
- **Improvement**: Cache interpretations by (query_signature, data_signature)
- **Impact**: 1-2s savings on repeated queries

### 5. **Parallel Validation**
- **Current**: Sequential validation (SQL → execute → interpret → validate)
- **Improvement**: Run SQL validation and execution preparation in parallel
- **Impact**: 100-300ms savings

### 6. **Context Compression**
- **Current**: Simple summarization (./utils/firebase_client.py)
- **Improvement**: Use specialized summarization model, extract key entities
- **Impact**: Better context quality, shorter prompts

### 7. **Profile Injection Optimization**
- **Current**: Full profile injected every prompt (./workflow/nodes.py:153)
- **Improvement**: Extract only relevant profile fields per query type
- **Impact**: Shorter prompts, faster LLM calls

### 8. **Complexity-Based Routing**
- **Current**: All queries go through same path (./workflow/nodes.py:227)
- **Improvement**: Route simple queries to fast path, complex to thorough path
- **Impact**: Better resource allocation, faster simple queries

### 9. **Athena Query Optimization**
- **Current**: Direct query execution (./workflow/nodes.py:974)
- **Improvement**: Query result caching, partition pruning hints
- **Impact**: Significant speedup for large datasets

### 10. **Real-time Streaming**
- **Current**: Response sent after full completion (./api_websocket.py:440)
- **Improvement**: Stream interpretation as it generates
- **Impact**: Better perceived performance, lower latency

---

## Measurement Points for Optimization

Track these metrics to identify bottlenecks:

1. **Per-node timing**:
   - planner_duration
   - sql_gen_duration
   - sql_validation_duration
   - sql_execution_duration
   - interpretation_duration

2. **Cache hit rates**:
   - template_match_rate
   - context_cache_hit_rate
   - interpretation_cache_hit_rate

3. **Quality metrics**:
   - sql_retry_rate
   - interpretation_retry_rate
   - error_rate_by_category

4. **LLM metrics**:
   - tokens_per_query
   - llm_call_count_per_query
   - llm_latency_p50, p95, p99

5. **User metrics**:
   - end_to_end_latency
   - time_to_first_token
   - user_satisfaction_score
