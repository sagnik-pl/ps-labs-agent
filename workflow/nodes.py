"""
Node functions for the LangGraph agent workflow.
Each node represents a step in the multi-agent processing pipeline.
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from workflow.state import AgentState
from config.settings import settings
from prompts.prompt_manager import prompt_manager
import json


class WorkflowNodes:
    """Collection of node functions for the agent workflow graph."""

    def __init__(self):
        """Initialize workflow nodes with OpenAI."""
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Upgraded from gpt-4-turbo-preview for 2x speed improvement
            openai_api_key=settings.openai_api_key,
            temperature=0,
        )
        self.prompt_manager = prompt_manager

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
        from utils.semantic_layer import check_data_availability, detect_ambiguous_query

        query = state["query"]
        context = state.get("context", "")
        user_profile = state.get("user_profile")

        # ========== CHECK 1: Out-of-Scope Data Detection ==========
        # Before planning, check if user is asking for data we don't have
        data_check = check_data_availability(query)

        if not data_check['available']:
            # User is asking for unavailable data - return early with helpful message
            return {
                "execution_plan": {
                    "type": "out_of_scope",
                    "message": data_check['suggestion'],
                    "missing_platforms": data_check['missing_platforms'],
                    "available_platforms": data_check['available_platforms']
                },
                "next_step": "END",  # Skip rest of workflow
                "messages": [AIMessage(content=data_check['suggestion'])]
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

            return {
                "execution_plan": {
                    "type": "needs_clarification",
                    "message": formatted_message,
                    "ambiguous_terms": ambiguity_check['ambiguous_terms'],
                    "clarification_question": question,
                    "options": ambiguity_check['options']
                },
                "next_step": "END",  # Wait for user to provide more specific query
                "messages": [AIMessage(content=formatted_message)]
            }

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
                        "agent": "data_analytics",
                        "action": "Execute data query",
                        "dependencies": [],
                    }
                ],
                "requires_multiple_agents": False,
                "estimated_complexity": "medium",
                "reasoning": "Single agent execution",
            }

        return {
            "plan": plan,
            "messages": [AIMessage(content=f"Plan created: {plan['reasoning']}")],
        }

    def router_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Route query to appropriate agent based on the plan.

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision
        """
        plan = state.get("plan", {})
        query = state["query"]

        # Get the first step from plan
        steps = plan.get("steps", [])
        if not steps:
            # Fallback to default routing
            routing_decision = {
                "primary_agent": "data_analytics",
                "reasoning": "Default routing",
                "next_step": "data_analytics_agent",
            }
        else:
            first_step = steps[0]
            agent = first_step.get("agent", "data_analytics")

            routing_decision = {
                "primary_agent": agent,
                "reasoning": first_step.get("action", "Execute query"),
                "next_step": f"{agent}_agent",
            }

        return {
            "routing_decision": routing_decision,
            "current_agent": routing_decision["primary_agent"],
            "next_step": routing_decision["next_step"],
        }

    def data_analytics_agent_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute data analytics query using tools.

        This node wraps the existing DataAnalyticsAgent functionality
        into the LangGraph workflow.

        Args:
            state: Current agent state

        Returns:
            Updated state with agent results and raw data
        """
        from agents.data_analytics_agent import DataAnalyticsAgent

        query = state["query"]
        user_id = state["user_id"]
        context = state.get("context", "")

        # Initialize and run the agent
        agent = DataAnalyticsAgent(use_anthropic=False)
        result = agent.run(query, user_id, context)

        return {
            "agent_results": {
                "agent": "data_analytics",
                "result": result,
                "status": "completed",
            },
            "raw_data": result,  # Store raw data for interpretation
            "messages": [AIMessage(content=result)],
        }

    def validator_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Validate agent results for correctness and completeness.

        Checks:
        - Did the agent produce a result?
        - Is the result well-formed?
        - Does it answer the user's query?
        - Are there any errors or issues?

        Args:
            state: Current agent state

        Returns:
            Updated state with validation results
        """
        agent_results = state.get("agent_results", {})
        query = state["query"]
        result = agent_results.get("result", "")

        # Load prompt from prompt manager
        prompt = self.prompt_manager.get_agent_prompt(
            "validator",
            variables={
                "query": query,
                "result": result
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        try:
            validation = json.loads(response.content)
        except json.JSONDecodeError:
            # Default to valid if parsing fails
            validation = {
                "is_valid": True,
                "completeness_score": 80,
                "issues": [],
                "needs_retry": False,
                "reasoning": "Validation completed",
            }

        return {
            "validation_result": validation,
            "needs_retry": validation.get("needs_retry", False),
            "next_step": "retry" if validation.get("needs_retry") else "interpreter",
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

        # Format profile context for injection
        if user_profile:
            profile_context = format_profile_for_prompt(user_profile)
        else:
            profile_context = "No profile information available."

        # Load prompt from prompt manager with e-commerce knowledge
        prompt = self.prompt_manager.get_agent_prompt(
            "data_interpreter",
            variables={
                "query": query,
                "raw_data": raw_data,
                "context": context,
                "feedback": feedback or "No previous feedback",
                "profile_context": profile_context
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

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

        # Load prompt from prompt manager
        prompt = self.prompt_manager.get_agent_prompt(
            "interpretation_validator",
            variables={
                "query": query,
                "raw_data": raw_data,
                "interpretation": interpretation
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
        from utils.sql_templates import suggest_template, get_template_with_validation, get_template_metadata
        import logging

        logger = logging.getLogger(__name__)

        query = state["query"]
        user_id = state["user_id"]
        validation_feedback = state.get("sql_validation_feedback", "")

        # ========== STEP 1: Try Template-Based Generation ==========
        # Check if query matches a pre-optimized template
        matched_template = suggest_template(query)

        if matched_template:
            logger.info(f"Found matching template: {matched_template}")

            # Get template metadata to extract default parameters
            template_meta = get_template_metadata(matched_template)

            if template_meta:
                # Prepare parameters (user_id is always required)
                template_params = {"user_id": user_id}

                # Try to extract time period from query if needed
                if 'days' in template_meta['parameters']:
                    # Simple extraction: look for numbers followed by "day(s)" or "week(s)"
                    import re
                    days_match = re.search(r'(\d+)\s*(?:day|days)', query.lower())
                    weeks_match = re.search(r'(\d+)\s*(?:week|weeks)', query.lower())

                    if days_match:
                        template_params['days'] = int(days_match.group(1))
                    elif weeks_match:
                        template_params['days'] = int(weeks_match.group(1)) * 7
                    # else: will use default from template

                # Try to extract limit from query if needed
                if 'limit' in template_meta['parameters']:
                    limit_match = re.search(r'(?:top|first|last)\s*(\d+)', query.lower())
                    if limit_match:
                        template_params['limit'] = int(limit_match.group(1))

                # Generate SQL from template
                template_result = get_template_with_validation(matched_template, **template_params)

                if template_result['success']:
                    logger.info(f"✅ Using optimized template: {matched_template}")

                    return {
                        "generated_sql": template_result['sql'],
                        "table_schemas": f"Using optimized template: {template_meta['display_name']}",
                        "used_template": matched_template,
                        "template_params": template_params,
                        "messages": [AIMessage(content=f"Generated SQL using optimized template: {template_meta['display_name']}")],
                    }
                else:
                    logger.warning(f"Template validation failed: {template_result['error']}")
                    # Fall through to LLM-based generation

        # ========== STEP 2: LLM-Based SQL Generation ==========
        # No matching template or template failed - generate from scratch

        # Get available tables
        tables_result = list_tables_tool.invoke({"user_id": user_id})

        # Get schemas for relevant tables using semantic layer
        # Semantic layer provides enhanced schema with column types, descriptions, and notes
        table_schemas_list = []
        if "instagram" in query.lower():
            for table_name in ["instagram_media", "instagram_media_insights"]:
                # Get enhanced schema from semantic layer
                semantic_schema = semantic_layer.get_schema_for_sql_gen(table_name)

                # Also get Athena schema for column list
                athena_schema = table_schema_tool.invoke({"table_name": table_name})

                # Combine both for comprehensive information
                combined_schema = f"{semantic_schema}\n\nAthena Schema:\n{athena_schema}"
                table_schemas_list.append(combined_schema)

        table_schemas = "\n\n".join(table_schemas_list) if table_schemas_list else tables_result

        # Add pattern info hint if we found a template but couldn't use it
        pattern_info = ""
        if matched_template:
            pattern_def = semantic_layer.get_query_pattern(matched_template)
            if pattern_def:
                pattern_info = f"\n\n**Similar Query Pattern**: {pattern_def.get('name')}\n"
                pattern_info += f"Description: {pattern_def.get('description')}\n"
                pattern_info += f"You can reference this pattern's structure for your query.\n"
                # Include the template as an example
                if 'template' in pattern_def:
                    pattern_info += f"\n**Example Template Structure**:\n{pattern_def['template'][:500]}...\n"

        # Load SQL generator prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "sql_generator",
            variables={
                "user_query": query,
                "user_id": user_id,
                "table_schemas": table_schemas + pattern_info,
                "validation_feedback": validation_feedback or "No previous feedback"
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        # Extract SQL query from response (remove any markdown formatting)
        generated_sql = response.content.strip()
        # Remove markdown code fences if present
        if generated_sql.startswith("```"):
            lines = generated_sql.split("\n")
            generated_sql = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        return {
            "generated_sql": generated_sql,
            "table_schemas": table_schemas,
            "messages": [AIMessage(content=f"Generated SQL query")],
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
        user_id = state["user_id"]
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
        user_id = state["user_id"]
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
