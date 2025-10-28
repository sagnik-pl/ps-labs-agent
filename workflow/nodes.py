"""
Node functions for the LangGraph agent workflow.
Each node represents a step in the multi-agent processing pipeline.
"""
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from workflow.state import AgentState
from config.settings import settings
from prompts.prompt_manager import prompt_manager
import json


class WorkflowNodes:
    """Collection of node functions for the agent workflow graph."""

    def __init__(self):
        """Initialize workflow nodes with lazy-loaded LLM instances."""
        # Lazy-load LLMs to prevent startup delays
        self._llm = None
        self._llm_sql = None
        self._llm_interpreter = None
        self.prompt_manager = prompt_manager

    @property
    def llm(self):
        """Lazy-load default LLM for most nodes (planning, assessment, validation, formatting)."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model="gpt-5-mini-2025-08-07",  # GPT-5 Mini: Cost-efficient for structured tasks
                openai_api_key=settings.openai_api_key,
                temperature=1,  # GPT-5 models only support temperature=1
            )
        return self._llm

    @property
    def llm_sql(self):
        """Lazy-load premium model for SQL generation (complex reasoning, table selection, joins)."""
        if self._llm_sql is None:
            self._llm_sql = ChatOpenAI(
                model="gpt-5-2025-08-07",  # GPT-5: Better reasoning for SQL generation
                openai_api_key=settings.openai_api_key,
                temperature=1,  # GPT-5 models only support temperature=1
            )
        return self._llm_sql

    @property
    def llm_interpreter(self):
        """Lazy-load premium model for data interpretation (user-facing quality, 11 knowledge bases)."""
        if self._llm_interpreter is None:
            self._llm_interpreter = ChatOpenAI(
                model="gpt-5-2025-08-07",  # GPT-5: Deep e-commerce analysis and insights
                openai_api_key=settings.openai_api_key,
                temperature=1,  # GPT-5 models only support temperature=1
            )
        return self._llm_interpreter

    def _detect_time_window(self, query: str) -> Dict[str, Any]:
        """
        Detect if query mentions a time window/period.

        Returns dict with:
        - has_time_window: bool
        - time_expressions: list of detected time expressions
        """
        import re

        # Common time window patterns
        time_patterns = [
            r'\blast\s+\d+\s+(day|days|week|weeks|month|months|year|years)\b',
            r'\bpast\s+\d+\s+(day|days|week|weeks|month|months|year|years)\b',
            r'\bprevious\s+(day|week|month|quarter|year)\b',
            r'\bthis\s+(day|week|month|quarter|year)\b',
            r'\byesterday\b',
            r'\btoday\b',
            r'\bthis\s+week\b',
            r'\blast\s+week\b',
            r'\bthis\s+month\b',
            r'\blast\s+month\b',
            r'\bthis\s+quarter\b',
            r'\blast\s+quarter\b',
            r'\bthis\s+year\b',
            r'\blast\s+year\b',
            r'\bsince\s+\d{4}',
            r'\bfrom\s+\d{1,2}[/-]\d{1,2}',
            r'\bbetween\s+\d{1,2}[/-]\d{1,2}',
            r'\bin\s+(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'\bin\s+\d{4}',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\bbefore\s+that\b',
            r'\bprior\s+to\s+that\b',
        ]

        detected_expressions = []
        for pattern in time_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                detected_expressions.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])

        has_time_window = len(detected_expressions) > 0

        return {
            "has_time_window": has_time_window,
            "time_expressions": detected_expressions
        }

    def _decompose_query(self, query: str, context: str, retry_feedback: str = "") -> Dict[str, Any]:
        """
        Classify query intent and decompose multi-intent queries into single-intent sub-queries.

        Args:
            query: User's query
            context: Conversation context
            retry_feedback: Feedback from assessment node if this is a retry

        Returns:
            Dict with classification and decomposition results
        """
        # Load decomposer prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "query_decomposer",
            variables={
                "query": query,
                "context": context,
            }
        )

        # Add retry feedback if this is a retry
        if retry_feedback:
            prompt += f"\n\n## Feedback from Previous Attempt\n\n{retry_feedback}\n\nPlease address this feedback in your decomposition."

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            # Fallback: treat as single-intent
            return {
                "classification": {
                    "type": "single_intent",
                    "complexity": "simple",
                    "reasoning": "Failed to parse decomposition, treating as single-intent",
                    "requires_decomposition": False
                },
                "decomposition": {
                    "original_query": query,
                    "original_goal": query,
                    "sub_queries": []
                }
            }

    def planner_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Create an execution plan for the user query.

        Analyzes the query and conversation context to determine:
        - What information is needed
        - Which agents should be involved
        - The sequence of operations

        Args:
            state: Current agent state

        Returns:
            Updated state with execution plan
        """
        from utils.profile_defaults import format_profile_for_prompt
        from utils.semantic_layer import check_data_availability, detect_ambiguous_query, detect_data_inquiry_query  # detect_comparison_query DISABLED
        # from utils.query_splitter import split_comparison_query  # DISABLED FOR REDESIGN

        query = state["query"]
        context = state.get("context", "")
        user_profile = state.get("user_profile")

        # ========== TIME WINDOW DETECTION ==========
        # Detect if query mentions a time window, default to last 30 days if not
        time_window_check = self._detect_time_window(query)
        has_time_window = time_window_check["has_time_window"]

        # Store time window metadata to be included in final response
        time_window_metadata = {
            "has_explicit_time_window": has_time_window,
            "detected_expressions": time_window_check["time_expressions"],
            "defaulted_to_30_days": not has_time_window,
        }

        # ========== CHECK 0: Data Inquiry Detection ==========
        # Check if user is asking ABOUT data availability (meta-query) rather than requesting data
        inquiry_check = detect_data_inquiry_query(query)

        if inquiry_check['is_inquiry']:
            # User is asking about what data is available - provide informative response
            # IMPORTANT: Preserve existing state to maintain user_id, conversation_id, etc.
            return {
                **state,  # Spread existing state to preserve required fields
                "execution_plan": {
                    "type": "data_inquiry",
                    "data_topic": inquiry_check['data_topic'],
                    "message": inquiry_check['response']
                },
                "next_step": "END",  # Skip rest of workflow
                "final_response": inquiry_check['response'],  # Set for API response
                "messages": state.get("messages", []) + [AIMessage(content=inquiry_check['response'])]
            }

        # ========== CHECK 1: Out-of-Scope Data Detection ==========
        # Before planning, check if user is asking for data we don't have
        data_check = check_data_availability(query)

        if not data_check['available']:
            # User is asking for unavailable data - return early with helpful message
            # IMPORTANT: Preserve existing state to maintain user_id, conversation_id, etc.
            return {
                **state,  # Spread existing state to preserve required fields
                "execution_plan": {
                    "type": "out_of_scope",
                    "message": data_check['suggestion'],
                    "missing_platforms": data_check['missing_platforms'],
                    "available_platforms": data_check['available_platforms']
                },
                "next_step": "END",  # Skip rest of workflow
                "final_response": data_check['suggestion'],  # Set for API response
                "messages": state.get("messages", []) + [AIMessage(content=data_check['suggestion'])]
            }

        # ========== CHECK 2: Ambiguous Query Detection ==========
        # Check if query is too vague and needs clarification
        ambiguity_check = detect_ambiguous_query(query)

        if ambiguity_check['is_ambiguous']:
            # Query is ambiguous - ask for clarification
            # Format the options nicely for the user
            question = ambiguity_check['clarification_question']
            options_list = []
            for i, option in enumerate(ambiguity_check['options'], 1):
                options_list.append(
                    f"{i}. **{option['label']}**: {option['description']}"
                )

            formatted_message = f"{question}\n\n" + "\n".join(options_list)

            # IMPORTANT: Preserve existing state to maintain user_id, conversation_id, etc.
            return {
                **state,  # Spread existing state to preserve required fields
                "execution_plan": {
                    "type": "needs_clarification",
                    "message": formatted_message,
                    "ambiguous_terms": ambiguity_check['ambiguous_terms'],
                    "clarification_question": question,
                    "options": ambiguity_check['options']
                },
                "next_step": "END",  # Wait for user to provide more specific query
                "final_response": formatted_message,  # Set for API response
                "messages": state.get("messages", []) + [AIMessage(content=formatted_message)]
            }

        # ========== CHECK 3: MULTI-INTENT DETECTION & DECOMPOSITION ==========
        # Detect if query is single-intent (direct) or multi-intent (needs decomposition)
        # Multi-intent queries are broken into single-intent sub-queries with dependencies
        import logging
        logger = logging.getLogger(__name__)

        # Check if this is a retry from assessment node
        retry_feedback = state.get("decomposition_assessment", {}).get("feedback", "")
        decomposition_retry_count = state.get("decomposition_retry_count", 0)

        # Call decomposition logic
        decomposition_result = self._decompose_query(query, context, retry_feedback)

        # Store classification and decomposition in state
        query_classification = decomposition_result.get("classification", {})
        query_decomposition = decomposition_result.get("decomposition", {})

        requires_decomposition = query_classification.get("requires_decomposition", False)

        if requires_decomposition:
            logger.info(f"🔀 Multi-intent query detected: {query_classification['type']}")
            logger.info(f"📝 Decomposed into {len(query_decomposition.get('sub_queries', []))} sub-queries")

            # Route to assessment node for validation
            return {
                **state,  # Preserve existing state
                "query_classification": query_classification,
                "query_decomposition": query_decomposition,
                "next_step": "query_assessment",
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"Analyzing query: {query_classification['reasoning']}")
                ],
                "metadata": {
                    **state.get("metadata", {}),
                    "time_window": time_window_metadata,
                },
            }
        else:
            # Single-intent query - proceed normally
            logger.info(f"✓ Single-intent query: {query_classification['reasoning']}")

        # Format profile context for injection
        if user_profile:
            profile_context = format_profile_for_prompt(user_profile)
        else:
            profile_context = "No profile information available."

        # Load prompt from prompt manager
        prompt = self.prompt_manager.get_agent_prompt(
            "planner",
            variables={
                "query": query,
                "context": context,
                "profile_context": profile_context
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            plan = json.loads(response.content)
        except json.JSONDecodeError:
            # Default simple plan
            plan = {
                "steps": [
                    {
                        "step_number": 1,
                        "action": "Execute data query via SQL pipeline",
                        "workflow_path": "sql_pipeline",
                        "dependencies": [],
                    }
                ],
                "requires_multiple_agents": False,
                "estimated_complexity": "medium",
                "reasoning": "Single node execution through SQL pipeline",
            }

        return {
            "plan": plan,
            "query_classification": query_classification,  # Store classification even for single-intent
            "query_decomposition": query_decomposition,  # Empty for single-intent
            "next_step": "router",  # Explicitly set next step to prevent LLM leakage
            "messages": [AIMessage(content=f"Plan created: {plan['reasoning']}")],
            "metadata": {
                **state.get("metadata", {}),  # Preserve existing metadata
                "time_window": time_window_metadata,
                "query_classification": query_classification,
            },
        }

    def router_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Route query based on classification.

        - Single-intent queries → sql_generator (direct SQL execution)
        - Multi-intent queries → multi_intent_executor (orchestrated parallel execution)

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision
        """
        plan = state.get("plan", {})
        query = state["query"]

        # Check query classification
        classification = state.get("query_classification", {})
        query_type = classification.get("type", "single_intent")

        if query_type == "multi_intent":
            # Multi-intent: route to orchestrator for parallel sub-query execution
            decomposition = state.get("query_decomposition", {})
            sub_query_count = len(decomposition.get("sub_queries", []))

            routing_decision = {
                "query_type": "multi_intent_data_analytics",
                "reasoning": f"Multi-intent query with {sub_query_count} sub-queries requiring orchestrated execution",
                "next_step": "multi_intent_executor",
                "workflow_path": "multi_intent_sql_pipeline",
            }

            return {
                "routing_decision": routing_decision,
                "next_step": "multi_intent_executor",
            }
        else:
            # Single-intent: existing routing to SQL generator
            steps = plan.get("steps", [])
            reasoning = steps[0].get("action", "Execute data query via SQL pipeline") if steps else "Default routing to SQL pipeline"

            routing_decision = {
                "query_type": "data_analytics",
                "reasoning": reasoning,
                "next_step": "sql_generator",
                "workflow_path": "sql_pipeline",
            }

            return {
                "routing_decision": routing_decision,
                "next_step": routing_decision["next_step"],
            }

    def multi_intent_executor_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute multiple sub-queries with parallel execution for independent queries.

        Groups queries by execution_order (dependency layers).
        Within each layer, executes queries in parallel using ThreadPoolExecutor.
        Between layers, executes sequentially to respect dependencies.

        Each sub-query goes through full pipeline:
        sql_generator_node → sql_validator_node → sql_executor_node

        Example:
            Layer 1: [sq_1, sq_4] execute in parallel (both order=1, no deps)
            Layer 2: [sq_2, sq_3] execute in parallel (both order=2, depend on sq_1)

        Args:
            state: Current state with query_decomposition

        Returns:
            Updated state with aggregated results
        """
        import logging
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        logger = logging.getLogger(__name__)

        # Extract decomposition
        decomposition = state.get("query_decomposition", {})
        sub_queries = decomposition.get("sub_queries", [])
        original_query = decomposition.get("original_query", state["query"])
        original_goal = decomposition.get("original_goal", state["query"])

        total_queries = len(sub_queries)
        logger.info(f"🔀 Executing {total_queries} sub-queries with parallel optimization")

        # Step 1: Group queries by execution order (dependency layers)
        layers = self._group_queries_by_execution_order(sub_queries)
        logger.info(f"📊 Organized into {len(layers)} execution layers")

        # Step 2: Execute each layer (sequential between layers, parallel within layer)
        sub_results = {}
        execution_log = []
        start_time = time.time()

        for layer_num, layer_queries in enumerate(layers, 1):
            layer_size = len(layer_queries)
            logger.info(f"🚀 Layer {layer_num}: Executing {layer_size} queries in parallel")
            layer_start = time.time()

            # Execute this layer's queries in parallel
            with ThreadPoolExecutor(max_workers=layer_size) as executor:
                # Submit all queries in this layer
                future_to_query = {}
                for sq in layer_queries:
                    future = executor.submit(
                        self._execute_single_sub_query,
                        sq,
                        state,
                        sub_results  # Pass existing results for dependency context
                    )
                    future_to_query[future] = sq

                # Collect results as they complete
                for future in as_completed(future_to_query):
                    sq = future_to_query[future]
                    sq_id = sq["id"]

                    try:
                        result = future.result()
                        sub_results[sq_id] = result

                        status_icon = "✅" if result["execution_status"] == "success" else "❌"
                        logger.info(f"{status_icon} {sq_id} completed")

                        # Log execution
                        execution_log.append({
                            "order": len(execution_log) + 1,
                            "layer": layer_num,
                            "sub_query_id": sq_id,
                            "question": sq["question"],
                            "dependencies": sq.get("dependencies", []),
                            "status": result["execution_status"]
                        })

                    except Exception as e:
                        logger.error(f"❌ {sq_id} failed: {str(e)}")
                        sub_results[sq_id] = {
                            "id": sq_id,
                            "question": sq["question"],
                            "intent": sq["intent"],
                            "sql": "",
                            "data": f"Error: {str(e)}",
                            "execution_status": "error",
                        }

            layer_duration = time.time() - layer_start
            logger.info(f"✅ Layer {layer_num} completed in {layer_duration:.2f}s")

        total_duration = time.time() - start_time
        logger.info(f"✅ All {total_queries} sub-queries completed in {total_duration:.2f}s")

        # Step 3: Aggregate results
        aggregated_data = self._aggregate_sub_query_results(
            sub_results,
            original_query,
            original_goal
        )

        # Calculate parallelization benefit
        successful_count = len([r for r in sub_results.values() if r["execution_status"] == "success"])
        failed_count = len([r for r in sub_results.values() if r["execution_status"] == "error"])

        return {
            "user_id": state["user_id"],
            "query": original_query,
            "sub_query_results": sub_results,
            "sub_query_execution_log": execution_log,
            "raw_data": aggregated_data,
            "execution_status": "success" if failed_count == 0 else "partial_success",
            "metadata": {
                **state.get("metadata", {}),
                "multi_intent_execution": {
                    "total_sub_queries": total_queries,
                    "successful": successful_count,
                    "failed": failed_count,
                    "execution_layers": len(layers),
                    "total_duration_seconds": round(total_duration, 2),
                    "parallel_execution": True
                }
            },
            "messages": state.get("messages", []) + [
                AIMessage(content=f"Executed {total_queries} sub-queries in {total_duration:.1f}s (parallel)")
            ]
        }

    def _group_queries_by_execution_order(self, sub_queries: List[Dict]) -> List[List[Dict]]:
        """
        Group sub-queries by execution_order for layer-by-layer parallel execution.

        Returns:
            List of layers, where each layer is a list of queries that can run in parallel.

        Example:
            Input: [
                {id: "sq_1", execution_order: 1, ...},
                {id: "sq_4", execution_order: 1, ...},
                {id: "sq_2", execution_order: 2, ...},
                {id: "sq_3", execution_order: 2, ...}
            ]
            Output: [
                [{id: "sq_1", ...}, {id: "sq_4", ...}],  # Layer 1
                [{id: "sq_2", ...}, {id: "sq_3", ...}]   # Layer 2
            ]
        """
        from collections import defaultdict

        # Group by execution order
        order_groups = defaultdict(list)
        for sq in sub_queries:
            order = sq.get("execution_order", 1)
            order_groups[order].append(sq)

        # Sort by order and return as list of layers
        sorted_orders = sorted(order_groups.keys())
        return [order_groups[order] for order in sorted_orders]

    def _execute_single_sub_query(
        self,
        sq: Dict,
        parent_state: Dict,
        existing_results: Dict
    ) -> Dict:
        """
        Execute a single sub-query through the full SQL pipeline.

        This method runs in a separate thread for parallel execution.
        Calls sql_generator_node → sql_validator_node → sql_executor_node.

        Args:
            sq: Sub-query definition with id, question, intent, dependencies
            parent_state: Original state from multi_intent_executor
            existing_results: Results from already-executed sub-queries (for dependencies)

        Returns:
            Result dict for this sub-query
        """
        import logging
        logger = logging.getLogger(__name__)

        sq_id = sq["id"]
        sq_question = sq["question"]
        sq_intent = sq["intent"]
        sq_deps = sq.get("dependencies", [])

        try:
            # Step 1: Get dependency context
            dependency_context = self._get_dependency_context(sq_deps, existing_results)

            # Step 2: Create temporary state for this sub-query
            temp_state = {
                "user_id": parent_state["user_id"],
                "conversation_id": parent_state["conversation_id"],
                "query": sq_question,  # Use sub-query question as the query
                "context": parent_state.get("context", "") + "\n\n" + dependency_context,
                "user_profile": parent_state.get("user_profile"),
                "messages": parent_state.get("messages", []),
                "metadata": parent_state.get("metadata", {}),
                "needs_retry": False,
                "retry_count": 0,
                "sql_retry_count": 0,
            }

            # Step 3: Execute SQL pipeline
            # 3a. SQL Generator
            gen_result = self.sql_generator_node(temp_state)
            temp_state.update(gen_result)

            # 3b. SQL Validator
            val_result = self.sql_validator_node(temp_state)
            temp_state.update(val_result)

            # 3c. Handle validation retry if needed
            if temp_state.get("next_step") == "retry_sql":
                logger.warning(f"⚠️ {sq_id} SQL validation failed, retrying...")
                gen_result = self.sql_generator_node(temp_state)
                temp_state.update(gen_result)
                val_result = self.sql_validator_node(temp_state)
                temp_state.update(val_result)

            # 3d. SQL Executor
            exec_result = self.sql_executor_node(temp_state)
            temp_state.update(exec_result)

            # Step 4: Return result
            return {
                "id": sq_id,
                "question": sq_question,
                "intent": sq_intent,
                "sql": temp_state.get("generated_sql", ""),
                "data": temp_state.get("raw_data", ""),
                "execution_status": temp_state.get("execution_status", "success"),
            }

        except Exception as e:
            logger.error(f"❌ Error executing {sq_id}: {str(e)}")
            return {
                "id": sq_id,
                "question": sq_question,
                "intent": sq_intent,
                "sql": "",
                "data": f"Error: {str(e)}",
                "execution_status": "error",
            }

    def _get_dependency_context(self, dependencies: List[str], sub_results: Dict) -> str:
        """
        Extract results from dependency sub-queries to provide context.
        Thread-safe: only reads from sub_results, doesn't modify.
        """
        if not dependencies:
            return ""

        context_parts = ["## Context from dependent queries:"]
        for dep_id in dependencies:
            if dep_id in sub_results:
                result = sub_results[dep_id]
                context_parts.append(f"\n**{dep_id}** - {result['question']}:")
                context_parts.append(f"Result: {result['data'][:500]}...")  # Truncate if long

        return "\n".join(context_parts)

    def _aggregate_sub_query_results(
        self,
        sub_results: Dict,
        original_query: str,
        original_goal: str
    ) -> str:
        """
        Combine all sub-query results into structured data for interpretation.
        """
        aggregated = {
            "original_query": original_query,
            "original_goal": original_goal,
            "sub_query_count": len(sub_results),
            "results": {}
        }

        for sq_id, result in sub_results.items():
            aggregated["results"][sq_id] = {
                "question": result["question"],
                "intent": result["intent"],
                "data": result["data"],
                "status": result["execution_status"]
            }

        import json
        return json.dumps(aggregated, indent=2)

    def _format_sub_results_for_interpretation(self, sub_results: Dict) -> str:
        """
        Format sub-query results for the data interpreter prompt.

        Includes the SQL query, data results, and execution status for each sub-query
        to enable comprehensive synthesis across multiple sub-queries.

        Args:
            sub_results: Dictionary of sub-query results with SQL and data

        Returns:
            Formatted string with all sub-query results including SQL queries
        """
        formatted = []
        for sq_id, result in sub_results.items():
            status_icon = "✅" if result["execution_status"] == "success" else "❌"
            formatted.append(f"\n{status_icon} **{sq_id}**: {result['question']}")
            formatted.append(f"   Intent: {result['intent']}")
            formatted.append(f"   Status: {result['execution_status']}")

            # Include SQL query for transparency and context
            sql = result.get('sql', 'N/A')
            if sql and sql != 'N/A':
                # Truncate SQL if very long (keep first 400 chars)
                if len(sql) > 400:
                    formatted.append(f"   SQL: {sql[:400]}... (truncated)")
                else:
                    formatted.append(f"   SQL: {sql}")

            # Include data results (increase limit to 1200 chars for richer context)
            data = result.get('data', 'No data')
            if len(data) > 1200:
                formatted.append(f"   Data: {data[:1200]}... (truncated)")
            else:
                formatted.append(f"   Data: {data}")

        return "\n".join(formatted)

    def query_assessment_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Assess if query decomposition adequately answers the original goal.

        Validates that sub-queries are complete and sufficient. If not,
        provides feedback and routes back to planner for retry.

        Args:
            state: Current agent state with query_decomposition

        Returns:
            Updated state with assessment and routing decision
        """
        import logging
        logger = logging.getLogger(__name__)

        query_decomposition = state.get("query_decomposition", {})
        decomposition_retry_count = state.get("decomposition_retry_count", 0)
        MAX_RETRIES = 2

        # Extract decomposition details
        original_query = query_decomposition.get("original_query", state["query"])
        original_goal = query_decomposition.get("original_goal", state["query"])
        sub_queries = query_decomposition.get("sub_queries", [])

        # Format sub-queries for prompt
        sub_queries_formatted = ""
        for sq in sub_queries:
            deps = ", ".join(sq.get("dependencies", [])) if sq.get("dependencies") else "None"
            sub_queries_formatted += f"\n- **{sq['id']}** (order: {sq['execution_order']}, depends on: {deps})\n"
            sub_queries_formatted += f"  Question: {sq['question']}\n"
            sub_queries_formatted += f"  Intent: {sq['intent']}\n"

        # Load assessor prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "query_assessor",
            variables={
                "original_query": original_query,
                "original_goal": original_goal,
                "sub_queries_formatted": sub_queries_formatted,
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            assessment = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback: assume complete if can't parse
            logger.warning("Failed to parse assessment response, assuming complete")
            assessment = {
                "is_complete": True,
                "can_answer_goal": True,
                "confidence": "medium",
                "reasoning": "Assessment parse failed, proceeding with decomposition",
                "missing_intents": [],
                "suggested_additions": [],
                "feedback": "",
                "retry_needed": False
            }

        is_complete = assessment.get("is_complete", False)
        retry_needed = assessment.get("retry_needed", False)

        logger.info(f"📋 Decomposition assessment: {'✓ Complete' if is_complete else '✗ Incomplete'}")
        logger.info(f"   Reasoning: {assessment.get('reasoning', 'No reasoning provided')}")

        # Store assessment in state
        state_update = {
            **state,
            "decomposition_assessment": assessment,
        }

        if not is_complete and retry_needed and decomposition_retry_count < MAX_RETRIES:
            # Incomplete - retry decomposition
            logger.warning(f"⚠️ Decomposition incomplete. Retry {decomposition_retry_count + 1}/{MAX_RETRIES}")
            logger.info(f"   Missing: {', '.join(assessment.get('missing_intents', []))}")

            return {
                **state_update,
                "decomposition_retry_count": decomposition_retry_count + 1,
                "next_step": "planner",  # Route back to planner with feedback
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"Refining query analysis: {assessment.get('feedback', 'Addressing gaps')}")
                ],
            }
        elif not is_complete and decomposition_retry_count >= MAX_RETRIES:
            # Max retries reached - proceed anyway with warning
            logger.warning(f"⚠️ Max retries reached. Proceeding with current decomposition.")
            return {
                **state_update,
                "next_step": "router",
                "messages": state.get("messages", []) + [
                    AIMessage(content="Proceeding with query analysis (may be incomplete)")
                ],
            }
        else:
            # Complete - proceed to router
            logger.info(f"✓ Decomposition validated. Proceeding to execution.")
            return {
                **state_update,
                "next_step": "router",
                "messages": state.get("messages", []) + [
                    AIMessage(content="Query analysis complete. Executing...")
                ],
            }

    def interpreter_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Create final user-facing response.

        Uses the formatted output if available, otherwise falls back to
        the data interpretation.

        Args:
            state: Current agent state

        Returns:
            Updated state with final response
        """
        # Use formatted output if available, otherwise fall back to interpretation
        formatted_output = state.get("formatted_output", "")
        data_interpretation = state.get("data_interpretation", "")
        query = state["query"]
        plan = state.get("plan", {})

        # Prefer formatted output, but gracefully fall back if not available
        final_response = formatted_output if formatted_output else data_interpretation

        return {
            "final_response": final_response,
            "messages": [AIMessage(content=final_response)],
            "next_step": "end",
            "metadata": {
                "plan": plan,
                "routing": state.get("routing_decision"),
                "validation": state.get("validation_result"),
                "interpretation_validation": state.get("interpretation_validation"),
            },
        }

    def data_interpreter_node(self, state: AgentState) -> Dict[str, Any]:
        """
        E-commerce data interpreter - the brain for data analysis.

        Takes raw data results and interprets them with deep e-commerce
        knowledge, providing context, insights, and actionable recommendations.

        Args:
            state: Current agent state

        Returns:
            Updated state with data interpretation
        """
        import logging

        logger = logging.getLogger(__name__)

        # Check if there was an error in execution
        execution_status = state.get("execution_status", "success")
        error_message = state.get("error_message", "")

        if execution_status == "error":
            # Don't try to interpret error messages - return user-friendly error instead
            logger.warning("Skipping data interpretation due to execution error")

            error_response = f"⚠️ **Unable to retrieve data**\n\n{error_message}"

            # If there's more context from agent_results, add it
            agent_results = state.get("agent_results", {})
            error_category = agent_results.get("error_category", "unknown")

            # Add helpful suggestions based on error category
            if error_category == "data_not_found":
                error_response += "\n\n**What you can do:**\n- Check if your data sources are connected\n- Try a different time range\n- Verify your account has data available"
            elif error_category == "sql_syntax":
                error_response += "\n\n**What you can try:**\n- Rephrase your question more simply\n- Be more specific about what data you want\n- Ask about a specific metric or time period"
            elif error_category == "timeout":
                error_response += "\n\n**What you can try:**\n- Ask about a shorter time period\n- Be more specific in your question\n- Focus on a specific aspect of your data"

            return {
                "data_interpretation": error_response,
                "messages": [AIMessage(content=error_response)],
                "interpretation_is_error": True,  # Mark this as an error response
            }

        # Normal path - interpret successful data results
        from utils.profile_defaults import format_profile_for_prompt

        query = state["query"]
        raw_data = state.get("raw_data", "")
        context = state.get("context", "")
        feedback = state.get("interpretation_feedback", "")
        user_profile = state.get("user_profile")

        # Check if this is multi-intent query
        sub_query_results = state.get("sub_query_results")
        is_multi_intent = sub_query_results is not None

        # Format profile context for injection
        if user_profile:
            profile_context = format_profile_for_prompt(user_profile)
        else:
            profile_context = "No profile information available."

        # Load prompt from prompt manager with e-commerce knowledge
        prompt_variables = {
            "query": query,
            "raw_data": raw_data,
            "context": context,
            "feedback": feedback or "No previous feedback",
            "profile_context": profile_context,
            "user_id": state.get("user_id", "unknown")
        }

        prompt = self.prompt_manager.get_agent_prompt(
            "data_interpreter",
            variables=prompt_variables
        )

        # If multi-intent, add special section for sub-query results
        if is_multi_intent:
            logger.info("🧠 Interpreting multi-intent query with aggregated sub-query results")

            decomposition = state.get("query_decomposition", {})
            original_goal = decomposition.get("original_goal", query)

            # Format sub-query results for interpretation
            sub_results_formatted = self._format_sub_results_for_interpretation(sub_query_results)

            prompt += f"""

## Multi-Intent Query Interpretation

This query required breaking down into multiple sub-queries for comprehensive analysis.

**Original Goal**: {original_goal}

**Sub-Query Results**:
{sub_results_formatted}

**Your Task - Multi-Intent Synthesis**:
You must STITCH TOGETHER findings from all sub-queries into ONE comprehensive, cohesive response that answers the original goal holistically.

**Synthesis Requirements** (CRITICAL - follow exactly):

1. **Connect the Dots**:
   - Show how findings from different sub-queries relate to and influence each other
   - Identify patterns, correlations, or contradictions across sub-queries
   - Don't treat sub-queries as isolated data points

2. **Build a Narrative**:
   - Create a coherent story from individual data points
   - Use transitions like "This explains why...", "As a result...", "However..."
   - Present a unified picture, not a list of separate findings

3. **Answer the Original Goal**:
   - Directly address the user's high-level question
   - Focus on the big picture, not individual sub-query details
   - Your response should answer "{original_goal}", not just summarize sub-queries

4. **Cross-Reference Findings**:
   - Reference findings across sub-queries explicitly
   - Example: "Your low engagement (sq_1: 2.8%) is likely caused by inconsistent posting (sq_2: only 6 posts/month vs recommended 12-15)"
   - Show cause-and-effect relationships

5. **Unified Recommendations**:
   - Provide actions that consider ALL findings together
   - Prioritize recommendations based on combined insights
   - Show how one action addresses multiple issues

**Example of Good vs Bad Synthesis**:

❌ **BAD** (just listing sub-query results):
- sq_1: Your engagement is 2.8%
- sq_2: You posted 6 times this month
- sq_3: Your reach is 8,000
- sq_4: You gained 50 followers

✅ **GOOD** (stitching together):
"Your Instagram performance shows a critical pattern: despite decent reach (8K), your engagement is below benchmark (2.8% vs 3.5% industry avg), which directly stems from inconsistent posting—only 6 posts this month versus the recommended 12-15. This infrequent posting not only hurts engagement but also limits follower growth (50 new followers is 40% below potential). The solution: increase posting frequency to 3-4x/week with high-quality content to simultaneously boost engagement, reach, and follower acquisition."

Now synthesize the sub-query results above following these requirements.
"""

        messages = [HumanMessage(content=prompt)]
        response = self.llm_interpreter.invoke(messages)  # Use GPT-5 for data interpretation

        interpretation = response.content

        return {
            "data_interpretation": interpretation,
            "messages": [AIMessage(content=interpretation)],
            "interpretation_is_error": False,  # Mark this as a successful interpretation
        }

    def interpretation_validator_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Validate the quality of data interpretation.

        Checks if interpretation meets quality criteria:
        - Has proper context and benchmarks
        - Provides actionable insights
        - Uses e-commerce knowledge appropriately
        - Fully answers the query

        Args:
            state: Current agent state

        Returns:
            Updated state with validation results and retry decision
        """
        # Skip validation if this was an error response
        interpretation_is_error = state.get("interpretation_is_error", False)

        if interpretation_is_error:
            # Don't validate error messages - just pass through to final interpreter
            return {
                "interpretation_validation": {
                    "is_valid": True,
                    "quality_score": 100,
                    "feedback": "Error message - no validation needed",
                    "reasoning": "Skipped validation for error response"
                },
                "next_step": "final_interpreter",
            }

        query = state["query"]
        raw_data = state.get("raw_data", "")
        interpretation = state.get("data_interpretation", "")

        # Detect if this is multi-intent query for specialized validation
        sub_query_results = state.get("sub_query_results")
        is_multi_intent = sub_query_results is not None

        # Prepare multi-intent context for validation
        original_goal = query
        multi_intent_context = ""

        if is_multi_intent:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("🔍 Validating MULTI-INTENT interpretation (includes synthesis quality check)")

            # Get original goal from decomposition
            decomposition = state.get("query_decomposition", {})
            original_goal = decomposition.get("original_goal", query)
            num_sub_queries = len(sub_query_results)

            # Format context for validator
            multi_intent_context = f"""
**⚠️ MULTI-INTENT QUERY DETECTED**

**Original User Goal**: "{original_goal}"
**Sub-Queries Executed**: {num_sub_queries}

This interpretation MUST:
1. Synthesize findings from ALL {num_sub_queries} sub-queries into a cohesive response
2. Show relationships and connections between findings
3. Directly answer the original goal: "{original_goal}"
4. NOT just list sub-query results separately

Apply criterion #9 (Multi-Intent Synthesis Quality) when validating.
"""
        else:
            multi_intent_context = "This is a standard single-intent query. Skip multi-intent validation (criterion #9)."

        # Load prompt from prompt manager
        prompt = self.prompt_manager.get_agent_prompt(
            "interpretation_validator",
            variables={
                "query": query,
                "raw_data": raw_data,
                "interpretation": interpretation,
                "multi_intent_context": multi_intent_context
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            # Try to parse JSON directly
            validation = json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                # Extract content between ```json and ```
                lines = content.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                content = "\n".join(json_lines)

            try:
                validation = json.loads(content)
            except json.JSONDecodeError as e:
                # Still failed - default to valid with warning
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Interpretation validation parsing failed: {e}")
                logger.debug(f"Response content: {response.content[:200]}...")
                validation = {
                    "is_valid": True,
                    "quality_score": 80,
                    "feedback": "Validation parsing failed - accepting interpretation",
                    "reasoning": "Could not parse validation response"
                }

        # Determine if we need to retry interpretation
        is_valid = validation.get("is_valid", True)
        retry_count = state.get("interpretation_retry_count", 0)
        max_retries = 2

        needs_retry = not is_valid and retry_count < max_retries

        return {
            "interpretation_validation": validation,
            "interpretation_feedback": validation.get("feedback", ""),
            "interpretation_retry_count": retry_count + 1 if needs_retry else retry_count,
            "next_step": "retry_interpretation" if needs_retry else "output_formatter",
        }

    def output_formatter_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Format the data interpretation into structured, professional markdown.

        Takes the interpreted response and formats it with:
        - Tables for data comparison
        - Bullet points for key insights
        - Clear action items
        - Visual formatting for readability

        Args:
            state: Current agent state

        Returns:
            Updated state with formatted output
        """
        import logging

        logger = logging.getLogger(__name__)

        # Skip formatting for error responses
        interpretation_is_error = state.get("interpretation_is_error", False)

        if interpretation_is_error:
            # Don't format error messages, pass through as-is
            logger.info("Skipping output formatting for error response")
            return {
                "formatted_output": state.get("data_interpretation", ""),
                "messages": [AIMessage(content=state.get("data_interpretation", ""))],
            }

        interpretation = state.get("data_interpretation", "")
        query = state["query"]
        raw_data = state.get("raw_data", "")

        # Load formatter prompt from prompt manager
        prompt = self.prompt_manager.get_agent_prompt(
            "output_formatter",
            variables={
                "query": query,
                "interpretation": interpretation,
                "raw_data": raw_data
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        formatted_output = response.content

        # Check if we defaulted to 30 days and append notice
        time_window_metadata = state.get("metadata", {}).get("time_window", {})
        if time_window_metadata.get("defaulted_to_30_days", False):
            # Append time window notice to formatted output
            formatted_output += "\n\n---\n\n_Note: This analysis covers the **last 30 days** by default since no specific time period was mentioned._"

        logger.info("Output formatted successfully")

        return {
            "formatted_output": formatted_output,
            "messages": [AIMessage(content=formatted_output)],
        }

    def sql_generator_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate SQL query from natural language with template optimization.

        Strategy:
        1. Check if query matches a pre-optimized template
        2. If match found and parameters valid, use template (faster + more reliable)
        3. Otherwise, generate SQL from scratch using LLM

        Takes user query and available table schemas to generate
        a SQL query for Athena. Enhanced with semantic layer for
        better schema information and metric definitions.

        Args:
            state: Current agent state

        Returns:
            Updated state with generated SQL
        """
        from tools.athena_tools import list_tables_tool, table_schema_tool
        from utils.semantic_layer import semantic_layer
        import logging

        logger = logging.getLogger(__name__)

        query = state["query"]
        user_id = state.get("user_id")
        validation_feedback = state.get("sql_validation_feedback", "")
        correction_recommendations = state.get("sql_correction_recommendations")

        # Check if we're in correction mode (retry with recommendations)
        is_correction_mode = correction_recommendations is not None

        if is_correction_mode:
            logger.info("🔧 SQL Generation: CORRECTION MODE (using fix recommendations)")
        else:
            logger.info("🆕 SQL Generation: FRESH MODE (intelligent table selection)")

        # ========== STEP 1: Intelligent Table Selection ==========
        # Identify relevant data streams based on query keywords
        query_lower = query.lower()
        relevant_streams = []

        # Detect data streams from query
        if any(kw in query_lower for kw in ['instagram', 'ig', 'post', 'reel', 'follower', 'insta']):
            relevant_streams.append('instagram')
        if any(kw in query_lower for kw in ['facebook', 'fb', 'ad', 'ads', 'campaign']):
            relevant_streams.append('facebook')
        if any(kw in query_lower for kw in ['website', 'traffic', 'product', 'purchase', 'ecommerce', 'google analytics', 'ga']):
            relevant_streams.append('google_analytics')

        # Default to instagram if no stream detected (most common)
        if not relevant_streams:
            relevant_streams = ['instagram']
            logger.info(f"No specific data stream detected, defaulting to instagram")

        logger.info(f"Detected data streams: {relevant_streams}")

        # Get all tables for relevant streams with detailed schema information
        all_tables_info = []
        detailed_schemas = []

        for stream in relevant_streams:
            tables = semantic_layer.list_tables_by_data_stream(stream)
            for table_name in tables:
                table_schema = semantic_layer.get_table_schema(table_name)
                if table_schema:
                    # High-level info for selection overview
                    table_info = {
                        'name': table_name,
                        'description': table_schema.get('description', ''),
                        'use_cases': table_schema.get('use_cases', []),
                        'data_stream_type': table_schema.get('stream_type', ''),  # Updated field name
                        'category': table_schema.get('category', ''),
                        'columns_summary': list(table_schema.get('columns', {}).keys())[:15]  # First 15 columns
                    }
                    all_tables_info.append(table_info)

                    # Detailed schema with examples, filters, joins for SQL generation
                    detailed_schema = semantic_layer.get_schema_for_sql_gen(table_name)
                    detailed_schemas.append(detailed_schema)

        # Format schemas for SQL generation prompt
        # Combine both overview and detailed schemas
        overview = semantic_layer.format_tables_for_selection(all_tables_info)
        detailed = "\n\n---\n\n".join(detailed_schemas)

        table_schemas_formatted = f"{overview}\n\n{'='*70}\n# DETAILED SCHEMAS\n{'='*70}\n\n{detailed}"

        logger.info(f"Prepared {len(all_tables_info)} tables with detailed schemas for SQL generation")

        # ========== STEP 2: Multi-Intent Context Handling ==========
        # Check if this is part of a multi-intent query decomposition
        multi_intent_context = ""
        is_sub_query = state.get("is_sub_query", False)

        if is_sub_query:
            sub_query_info = state.get("sub_query_info", {})
            intent = sub_query_info.get('intent', 'N/A')
            original_goal = sub_query_info.get('original_goal', query)

            multi_intent_context = f"""
## Multi-Intent Query Decomposition

This query is part of a larger multi-intent question that was decomposed into focused sub-queries.

**Your Specific Intent**: {intent}

**Your Question**: {query}

**Original User Goal**: {original_goal}

⚠️ **IMPORTANT**:
- Focus ONLY on answering YOUR specific question above
- Don't try to answer other parts of the original goal
- Keep your query simple and focused on this single intent
- The decomposition system will combine all sub-query results later
"""
            logger.info(f"Multi-intent context added: intent={intent}")

        # ========== STEP 3: Correction Recommendations ==========
        correction_mode_info = ""
        if is_correction_mode:
            recommendations = correction_recommendations
            error_category = recommendations.get("error_category", "UNKNOWN")
            summary = recommendations.get("summary", "")

            correction_mode_info = f"\n\n## CORRECTION MODE ACTIVE\n\n"
            correction_mode_info += f"**Error Category**: {error_category}\n"
            correction_mode_info += f"**Summary**: {summary}\n\n"
            correction_mode_info += "**Specific Issues**:\n"
            for issue in recommendations.get("specific_issues", []):
                correction_mode_info += f"- {issue.get('issue', '')} ({issue.get('location', 'unknown location')})\n"
                correction_mode_info += f"  Reason: {issue.get('reason', '')}\n"

            correction_mode_info += "\n**Fix Recommendations** (apply in order):\n"
            for rec in recommendations.get("fix_recommendations", []):
                step = rec.get("step", "?")
                action = rec.get("action", "")
                reasoning = rec.get("reasoning", "")
                snippet = rec.get("corrected_snippet", "")

                correction_mode_info += f"\n{step}. {action}\n"
                correction_mode_info += f"   Reasoning: {reasoning}\n"
                if snippet:
                    correction_mode_info += f"   Corrected Code: `{snippet}`\n"

        # Load SQL generator prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "sql_generator",
            variables={
                "user_query": query,
                "user_id": user_id,
                "table_schemas": table_schemas_formatted,
                "validation_feedback": validation_feedback or "No previous feedback",
                "correction_recommendations": correction_mode_info or "No correction recommendations",
                "multi_intent_context": multi_intent_context
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm_sql.invoke(messages)  # Use GPT-5 for SQL generation

        # Extract SQL query from response (remove any markdown formatting)
        generated_sql = response.content.strip()
        # Remove markdown code fences if present
        if generated_sql.startswith("```"):
            lines = generated_sql.split("\n")
            generated_sql = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        return {
            "generated_sql": generated_sql,
            "table_schemas": table_schemas_formatted,
            "sql_correction_recommendations": None,  # Clear recommendations after use
            "messages": [AIMessage(content=f"Generated SQL query using intelligent table selection")],
        }

    def sql_validator_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Validate generated SQL query with complexity analysis.

        Checks SQL query for:
        - User isolation (user_id filter)
        - Correct table/column names (using semantic layer)
        - Valid SQL syntax
        - Query completeness
        - Safety and efficiency
        - Complexity scoring and optimization hints

        Args:
            state: Current agent state

        Returns:
            Updated state with validation results, complexity score, and retry decision
        """
        from utils.semantic_layer import semantic_layer
        from utils.sql_analyzer import (
            calculate_complexity,
            check_required_filters,
            get_optimization_hints,
            validate_syntax_basic,
            format_complexity_report
        )
        import logging
        logger = logging.getLogger(__name__)

        query = state["query"]
        user_id = state.get("user_id")
        generated_sql = state.get("generated_sql", "")
        table_schemas = state.get("table_schemas", "")
        previous_feedback = state.get("sql_validation_feedback", "")

        # ========== STEP 1: Basic Syntax Validation ==========
        is_valid_syntax, syntax_error = validate_syntax_basic(generated_sql)
        if not is_valid_syntax:
            logger.error(f"SQL syntax error: {syntax_error}")
            return {
                "sql_validation": {
                    "is_valid": False,
                    "validation_score": 0,
                    "feedback": f"❌ SYNTAX ERROR: {syntax_error}",
                    "reasoning": "Basic syntax validation failed"
                },
                "sql_validation_feedback": f"Fix syntax error: {syntax_error}",
                "sql_retry_count": state.get("sql_retry_count", 0) + 1,
                "next_step": "retry_sql"
            }

        # ========== STEP 2: Complexity Analysis ==========
        complexity = calculate_complexity(generated_sql)
        hints = get_optimization_hints(generated_sql, complexity)

        logger.info(f"SQL complexity: {complexity['score']}/10 ({complexity['level']})")

        # ========== STEP 3: Required Filters Check ==========
        # Determine primary table
        primary_table = "instagram_media_insights"  # Default
        if "instagram_media " in generated_sql.lower():
            primary_table = "instagram_media"

        missing_filters = check_required_filters(generated_sql, primary_table)

        if missing_filters:
            logger.warning(f"Missing required filters: {missing_filters}")

        # ========== STEP 4: Semantic Layer Validation ==========
        semantic_validation = []

        # Check for 'saves' vs 'saved' error and other column issues
        if "instagram" in query.lower():
            # Validate instagram_media_insights columns
            validation_result = semantic_layer.validate_sql_columns(
                generated_sql,
                "instagram_media_insights"
            )

            if validation_result.get('invalid'):
                invalid_cols = validation_result['invalid']
                suggestions = validation_result.get('suggestions', {})
                logger.warning(f"Invalid columns detected: {invalid_cols}")

                error_msg = f"⚠️ COLUMN ERROR: Found invalid columns: {', '.join(invalid_cols)}."

                # Add specific suggestions if available
                if suggestions:
                    corrections = [f"'{wrong}' → '{correct}'" for wrong, correct in suggestions.items()]
                    error_msg += f" Did you mean: {', '.join(corrections)}?"
                else:
                    error_msg += " Check schema carefully. Common mistake: use 'saved' not 'saves'."

                semantic_validation.append(error_msg)

        # ========== STEP 5: Compile Validation Feedback ==========
        feedback_parts = []

        # Add complexity report
        complexity_report = format_complexity_report(complexity, hints)
        feedback_parts.append(f"**Complexity Analysis**:\n{complexity_report}")

        # Add missing filters warning
        if missing_filters:
            feedback_parts.append(f"\n⚠️ **Missing Required Filters**:\n" +
                                 "\n".join(f"  - {f}" for f in missing_filters))

        # Add semantic validation
        if semantic_validation:
            feedback_parts.append("\n" + "\n".join(semantic_validation))

        # Add high complexity warning
        if complexity['score'] >= 7:
            feedback_parts.append(
                f"\n⚠️ **High Complexity Warning**: This query has a complexity score of {complexity['score']}/10. "
                "Consider simplifying or using query templates for better performance."
            )

        semantic_feedback = "\n\n".join(feedback_parts) if feedback_parts else ""

        # Load SQL validator prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "sql_validator",
            variables={
                "user_query": query,
                "sql_query": generated_sql,
                "table_schema": table_schemas,
                "user_id": user_id,
                "previous_feedback": (previous_feedback or "No previous feedback") +
                                   ("\n\n" + semantic_feedback if semantic_feedback else "")
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            # Try to parse JSON directly
            validation = json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                # Extract content between ```json and ```
                lines = content.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                content = "\n".join(json_lines)

            try:
                validation = json.loads(content)
            except json.JSONDecodeError as e:
                # Still failed - default to valid with warning
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"SQL validation parsing failed: {e}")
                logger.debug(f"Response content: {response.content[:200]}...")
                validation = {
                    "is_valid": True,
                    "validation_score": 75,
                    "feedback": "Validation parsing failed - proceeding with caution",
                    "reasoning": "Could not parse validation response"
                }

        # Determine if we need to retry SQL generation
        is_valid = validation.get("is_valid", True)
        retry_count = state.get("sql_retry_count", 0)
        max_retries = 3  # Allow up to 3 retries for SQL

        needs_retry = not is_valid and retry_count < max_retries

        # Add complexity data to validation result
        validation_with_complexity = {
            **validation,
            "complexity_score": complexity['score'],
            "complexity_level": complexity['level'],
            "optimization_hints": hints
        }

        return {
            "sql_validation": validation_with_complexity,
            "sql_validation_feedback": validation.get("feedback", ""),
            "sql_complexity": complexity,  # Store full complexity analysis
            "sql_retry_count": retry_count + 1 if needs_retry else retry_count,
            "next_step": "retry_sql" if needs_retry else "execute_sql",
        }

    def sql_corrector_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Analyze SQL validation failures and provide specific fix recommendations.

        This node acts as an intermediary between the validator and generator on retries.
        It translates validation feedback into structured, actionable recommendations
        that the SQL generator can use to regenerate a corrected query.

        Args:
            state: Current agent state with validation failure

        Returns:
            Updated state with correction recommendations
        """
        import logging
        logger = logging.getLogger(__name__)

        query = state["query"]
        user_id = state.get("user_id")
        generated_sql = state.get("generated_sql", "")
        validation_feedback = state.get("sql_validation_feedback", "")
        table_schemas = state.get("table_schemas", "")

        logger.info("🔧 Analyzing SQL validation failure for correction recommendations...")

        # Load SQL corrector prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "sql_corrector",
            variables={
                "user_query": query,
                "generated_sql": generated_sql,
                "validation_feedback": validation_feedback,
                "table_schemas": table_schemas,
                "user_id": user_id,
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            # Try to parse JSON directly
            recommendations = json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                content = "\n".join(json_lines)

            try:
                recommendations = json.loads(content)
            except json.JSONDecodeError as e:
                # Still failed - create minimal recommendations
                logger.warning(f"SQL corrector parsing failed: {e}")
                recommendations = {
                    "error_category": "UNKNOWN",
                    "specific_issues": [
                        {
                            "issue": "Validation failed",
                            "location": "Unknown",
                            "reason": validation_feedback
                        }
                    ],
                    "fix_recommendations": [
                        {
                            "step": 1,
                            "action": "Review validation feedback and regenerate SQL",
                            "reasoning": validation_feedback,
                            "corrected_snippet": ""
                        }
                    ],
                    "summary": "Review validation feedback and fix errors"
                }

        # Log recommendations
        error_category = recommendations.get("error_category", "UNKNOWN")
        summary = recommendations.get("summary", "No summary")
        logger.info(f"   Error Category: {error_category}")
        logger.info(f"   Fix Summary: {summary}")

        num_fixes = len(recommendations.get("fix_recommendations", []))
        logger.info(f"   Recommendations: {num_fixes} fix step(s)")

        return {
            "sql_correction_recommendations": recommendations,
            "next_step": "generate_with_corrections",
            "messages": [AIMessage(content=f"Analyzed SQL error: {error_category}. Generated {num_fixes} fix recommendation(s).")],
        }

    def sql_executor_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute validated SQL query with retry logic.

        Runs the validated SQL query against Athena and returns results.
        Implements retry logic with exponential backoff for transient failures.

        Args:
            state: Current agent state

        Returns:
            Updated state with query results
        """
        from tools.athena_tools import athena_query_tool
        import logging
        import traceback
        import time

        logger = logging.getLogger(__name__)
        user_id = state.get("user_id")
        generated_sql = state.get("generated_sql", "")

        # Retry configuration
        max_retries = 3
        retry_count = 0
        base_delay = 1  # seconds

        def is_retryable_error(error_details: str, error_type: str) -> bool:
            """Determine if an error is transient and worth retrying."""
            retryable_patterns = [
                "timeout",
                "timed out",
                "connection",
                "network",
                "throttl",
                "rate limit",
                "temporarily unavailable",
                "serviceexception"
            ]
            return any(pattern in error_details.lower() for pattern in retryable_patterns)

        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    logger.info(f"Retry attempt {retry_count}/{max_retries} for user {user_id[:8]}...")

                logger.info(f"Executing SQL query for user {user_id[:8]}...")
                result = athena_query_tool.invoke({
                    "query": generated_sql,
                    "user_id": user_id
                })

                # Check if result is an error string (athena_tools returns errors as strings)
                if result.startswith("Error executing query:") or result.startswith("Error getting schema:"):
                    # Treat error strings as exceptions
                    raise Exception(result.replace("Error executing query:", "").replace("Error getting schema:", "").strip())

                logger.info(f"SQL query executed successfully for user {user_id[:8]}... (attempts: {retry_count + 1})")
                return {
                    "user_id": user_id,  # CRITICAL: Maintain user_id for data isolation
                    "query": state["query"],  # Maintain query for next nodes
                    "agent_results": {
                        "agent": "sql_executor",
                        "result": result,
                        "sql_query": generated_sql,
                        "status": "completed",
                        "retry_count": retry_count,
                    },
                    "raw_data": result,
                    "execution_status": "success",  # Explicit success marker
                    "messages": [AIMessage(content=result)],
                }

            except Exception as e:
                # Log detailed error information
                error_type = type(e).__name__
                error_details = str(e)
                stack_trace = traceback.format_exc()

                logger.error(f"SQL Execution Error for user {user_id[:8]}... (attempt {retry_count + 1}/{max_retries + 1})")
                logger.error(f"Error Type: {error_type}")
                logger.error(f"Error Message: {error_details}")

                # Check if error is retryable
                is_retryable = is_retryable_error(error_details, error_type)

                if is_retryable and retry_count < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = base_delay * (2 ** retry_count)
                    logger.info(f"Retryable error detected. Retrying in {delay}s...")
                    time.sleep(delay)
                    retry_count += 1
                    continue  # Retry
                else:
                    # Non-retryable error or max retries exceeded
                    if retry_count >= max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for user {user_id[:8]}...")

                    logger.error(f"SQL Query:\n{generated_sql}")
                    logger.error(f"Stack Trace:\n{stack_trace}")

                    # Categorize error type for better user messages
                    if "NoSuchKey" in error_details or "does not exist" in error_details.lower():
                        error_category = "data_not_found"
                        user_message = "No data found. This could mean you haven't connected your data sources yet or there's no data for the requested time period."
                    elif "SYNTAX_ERROR" in error_details or "syntax" in error_details.lower() or "mismatched input" in error_details.lower() or "InvalidRequestException" in error_details:
                        error_category = "sql_syntax"
                        user_message = "There was an issue generating the query. Please try rephrasing your question."
                    elif "timeout" in error_details.lower() or "timed out" in error_details.lower():
                        error_category = "timeout"
                        user_message = "The query took too long to execute. Try narrowing down your time range or being more specific."
                    elif "permission" in error_details.lower() or "access denied" in error_details.lower():
                        error_category = "permission"
                        user_message = "Unable to access the data. Please check your data source permissions."
                    elif is_retryable:
                        error_category = "transient"
                        user_message = "We're experiencing temporary connectivity issues. Please try again in a moment."
                    else:
                        error_category = "unknown"
                        user_message = "An error occurred while retrieving your data. Our team has been notified."

                    error_msg = f"Error executing SQL query: {error_details}\n\nQuery:\n{generated_sql}"

                    return {
                        "user_id": user_id,  # CRITICAL: Maintain user_id for data isolation
                        "query": state["query"],  # Maintain query for next nodes
                        "agent_results": {
                            "agent": "sql_executor",
                            "result": error_msg,
                            "sql_query": generated_sql,
                            "status": "error",
                            "error_type": error_type,
                            "error_category": error_category,
                            "error_details": error_details,
                            "retry_count": retry_count,
                        },
                        "raw_data": error_msg,
                        "execution_status": "error",  # Explicit error marker
                        "error_message": user_message,  # User-friendly message
                        "messages": [AIMessage(content=error_msg)],
                    }

    # ============================================================================
    # PARALLEL COMPARISON NODE - DISABLED FOR COMPLETE REDESIGN
    # ============================================================================
    # This entire node is being redesigned from scratch. The current implementation
    # has architectural issues and needs to be rebuilt with a better approach.
    # ============================================================================
    #
    # async def parallel_comparison_node(self, state: AgentState) -> Dict[str, Any]:
    #     """
    #     Execute comparison queries in parallel for significant speedup.
    #
    #     This node handles queries that compare two or more items (time periods,
    #     content types, campaigns, etc.) by splitting them into independent
    #     sub-queries and executing them concurrently.
    #
    #     Args:
    #         state: Current agent state with execution_plan containing sub_queries
    #
    #     Returns:
    #         Updated state with merged comparison results
    #     """
    #     import asyncio
    #     from utils.parallel_executor import execute_queries_parallel, merge_comparison_results
    #     import logging
    #
    #     logger = logging.getLogger(__name__)
    #     user_id = state.get("user_id")
    #     execution_plan = state.get("execution_plan", {})
    #
    #     if not user_id:
    #         logger.error("No user_id in state for parallel comparison")
    #         return {
    #             "user_id": "",
    #             "query": state.get("query", ""),
    #             "agent_results": {
    #                 "agent": "parallel_comparison",
    #                 "result": "Error: No user_id provided",
    #                 "status": "error"
    #             },
    #             "raw_data": "Error: No user_id provided",
    #             "execution_status": "error",
    #             "messages": [AIMessage(content="Error: No user_id provided")]
    #         }
    #
    #     # Extract sub-queries from execution plan
    #     sub_queries_data = execution_plan.get("sub_queries", [])
    #     comparison_data = execution_plan.get("comparison_data", {})
    #     merge_strategy = execution_plan.get("merge_strategy", "side_by_side")
    #
    #     if not sub_queries_data:
    #         logger.error("No sub-queries found in execution plan for parallel comparison")
    #         return {
    #             "user_id": user_id,
    #             "query": state["query"],
    #             "agent_results": {
    #                 "agent": "parallel_comparison",
    #                 "result": "Error: No sub-queries to execute",
    #                 "status": "error"
    #             },
    #             "raw_data": "Error: No sub-queries to execute",
    #             "execution_status": "error",
    #             "messages": [AIMessage(content="Error: No sub-queries to execute")]
    #         }
    #
    #     logger.info(f"🔀 Executing {len(sub_queries_data)} comparison queries in parallel...")
    #
    #     # For each sub-query, we need to:
    #     # 1. Generate SQL using sql_generator_node
    #     # 2. Validate SQL using sql_validator_node
    #     # 3. Execute in parallel
    #
    #     # Extract just the text queries and labels
    #     queries_text = [sq['query'] for sq in sub_queries_data]
    #     labels = [sq['label'] for sq in sub_queries_data]
    #
    #     # Generate SQL for each sub-query
    #     sql_queries = []
    #     for i, sub_query_data in enumerate(sub_queries_data):
    #         sub_query_text = sub_query_data['query']
    #         label = sub_query_data['label']
    #
    #         logger.info(f"📝 Generating SQL for sub-query {i+1}: {label}")
    #
    #         # Create a temporary state for this sub-query
    #         temp_state = {
    #             "user_id": user_id,
    #             "query": sub_query_text,
    #             "context": state.get("context", ""),
    #             "user_profile": state.get("user_profile"),
    #             "sub_query_filters": sub_query_data.get('filters', {})
    #         }
    #
    #         # Generate SQL
    #         sql_gen_result = self.sql_generator_node(temp_state)
    #         generated_sql = sql_gen_result.get("generated_sql", "")
    #
    #         if not generated_sql:
    #             logger.error(f"Failed to generate SQL for sub-query: {label}")
    #             return {
    #                 "user_id": user_id,
    #                 "query": state["query"],
    #                 "agent_results": {
    #                     "agent": "parallel_comparison",
    #                     "result": f"Error: Failed to generate SQL for {label}",
    #                     "status": "error"
    #                 },
    #                 "raw_data": f"Error: Failed to generate SQL for {label}",
    #                 "execution_status": "error",
    #                 "messages": [AIMessage(content=f"Error: Failed to generate SQL for {label}")]
    #             }
    #
    #         # Validate SQL
    #         temp_state["generated_sql"] = generated_sql
    #         validation_result = self.sql_validator_node(temp_state)
    #
    #         if not validation_result.get("sql_validation", {}).get("is_valid", False):
    #             errors = validation_result.get("sql_validation", {}).get("errors", [])
    #             logger.error(f"SQL validation failed for {label}: {errors}")
    #             return {
    #                 "user_id": user_id,
    #                 "query": state["query"],
    #                 "agent_results": {
    #                     "agent": "parallel_comparison",
    #                     "result": f"Error: SQL validation failed for {label}: {errors}",
    #                     "status": "error"
    #                 },
    #                 "raw_data": f"Error: SQL validation failed for {label}",
    #                 "execution_status": "error",
    #                 "messages": [AIMessage(content=f"Error: SQL validation failed for {label}")]
    #             }
    #
    #         sql_queries.append(generated_sql)
    #         logger.info(f"✅ SQL generated and validated for {label}")
    #
    #     # Execute all queries in parallel
    #     logger.info(f"⚡ Executing {len(sql_queries)} queries in parallel...")
    #
    #     try:
    #         parallel_results = await execute_queries_parallel(
    #             queries=sql_queries,
    #             user_id=user_id,
    #             labels=labels,
    #             max_concurrent=5
    #         )
    #
    #         logger.info(f"✅ Parallel execution complete: {parallel_results['speedup']:.1f}x speedup ({parallel_results['total_duration']:.2f}s)")
    #
    #         # Merge results into comparison format
    #         comparison_result = merge_comparison_results(
    #             parallel_results=parallel_results,
    #             comparison_data=comparison_data
    #         )
    #
    #         # Format the comparison result as a user-friendly message
    #         if comparison_result.get('error'):
    #             result_message = comparison_result['summary']
    #         else:
    #             # Build formatted comparison output
    #             items_compared = comparison_result['items_compared']
    #             comparison_table = comparison_result['comparison_table']
    #             deltas = comparison_result['deltas']
    #             summary = comparison_result['summary']
    #
    #             # Format as markdown table
    #             result_parts = []
    #             result_parts.append(f"**Comparison: {' vs '.join(items_compared)}**\n")
    #             result_parts.append(summary)
    #             result_parts.append(f"\n**Performance Metrics:**")
    #
    #             # Build table
    #             if comparison_table:
    #                 for metric, values in comparison_table.items():
    #                     value_strs = [f"{label}: {values.get(label, 'N/A')}" for label in items_compared]
    #                     result_parts.append(f"- {metric}: " + " | ".join(value_strs))
    #
    #                     # Add delta if available
    #                     if metric in deltas:
    #                         delta_info = deltas[metric]
    #                         result_parts.append(f"  → Change: {delta_info['formatted']}")
    #
    #             result_parts.append(f"\n⚡ Query speedup: {parallel_results['speedup']:.1f}x faster ({parallel_results['total_duration']:.2f}s)")
    #
    #             result_message = "\n".join(result_parts)
    #
    #         return {
    #             "user_id": user_id,
    #             "query": state["query"],
    #             "agent_results": {
    #                 "agent": "parallel_comparison",
    #                 "result": result_message,
    #                 "comparison_result": comparison_result,
    #                 "parallel_stats": {
    #                     "speedup": parallel_results['speedup'],
    #                     "total_duration": parallel_results['total_duration'],
    #                     "query_count": parallel_results['query_count']
    #                 },
    #                 "status": "completed"
    #             },
    #             "raw_data": comparison_result,
    #             "execution_status": "success",
    #             "messages": [AIMessage(content=result_message)]
    #         }
    #
    #     except Exception as e:
    #         import traceback
    #         error_msg = f"Error executing parallel comparison: {str(e)}"
    #         stack_trace = traceback.format_exc()
    #         logger.error(error_msg)
    #         logger.error(stack_trace)
    #
    #         return {
    #             "user_id": user_id,
    #             "query": state["query"],
    #             "agent_results": {
    #                 "agent": "parallel_comparison",
    #                 "result": error_msg,
    #                 "status": "error",
    #                 "error_details": str(e)
    #             },
    #             "raw_data": error_msg,
    #             "execution_status": "error",
    #             "error_message": "Failed to execute comparison query. Please try rephrasing your question.",
    #             "messages": [AIMessage(content=error_msg)]
    #         }
