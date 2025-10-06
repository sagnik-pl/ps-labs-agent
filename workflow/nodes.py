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
            model="gpt-4-turbo-preview",
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
        query = state["query"]
        context = state.get("context", "")

        # Load prompt from prompt manager
        prompt = self.prompt_manager.get_agent_prompt(
            "planner",
            variables={
                "query": query,
                "context": context
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

        Uses the validated data interpretation (which has e-commerce context)
        to generate the final response.

        Args:
            state: Current agent state

        Returns:
            Updated state with final response
        """
        # Use the data interpretation (already has e-commerce context)
        data_interpretation = state.get("data_interpretation", "")
        query = state["query"]
        plan = state.get("plan", {})

        # The data_interpretation already has all the insights,
        # so we can use it directly as the final response
        # or add a final polish layer if needed

        final_response = data_interpretation

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
        query = state["query"]
        raw_data = state.get("raw_data", "")
        context = state.get("context", "")
        feedback = state.get("interpretation_feedback", "")

        # Load prompt from prompt manager with e-commerce knowledge
        prompt = self.prompt_manager.get_agent_prompt(
            "data_interpreter",
            variables={
                "query": query,
                "raw_data": raw_data,
                "context": context,
                "feedback": feedback or "No previous feedback"
            }
        )

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        interpretation = response.content

        return {
            "data_interpretation": interpretation,
            "messages": [AIMessage(content=interpretation)],
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
            "next_step": "retry_interpretation" if needs_retry else "final_interpreter",
        }

    def sql_generator_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate SQL query from natural language.

        Takes user query and available table schemas to generate
        a SQL query for Athena.

        Args:
            state: Current agent state

        Returns:
            Updated state with generated SQL
        """
        from tools.athena_tools import list_tables_tool, table_schema_tool

        query = state["query"]
        user_id = state["user_id"]
        validation_feedback = state.get("sql_validation_feedback", "")

        # Get available tables
        tables_result = list_tables_tool.invoke({"user_id": user_id})

        # Get schemas for relevant tables (for now, get all)
        # In production, you might want to intelligently select which schemas to fetch
        table_schemas_list = []
        if "instagram" in query.lower():
            for table_name in ["instagram_media", "instagram_media_insights"]:
                schema_result = table_schema_tool.invoke({"table_name": table_name})
                table_schemas_list.append(f"**{table_name}**:\n{schema_result}")

        table_schemas = "\n\n".join(table_schemas_list) if table_schemas_list else tables_result

        # Load SQL generator prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "sql_generator",
            variables={
                "user_query": query,
                "user_id": user_id,
                "table_schemas": table_schemas,
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
        Validate generated SQL query.

        Checks SQL query for:
        - User isolation (user_id filter)
        - Correct table/column names
        - Valid SQL syntax
        - Query completeness
        - Safety and efficiency

        Args:
            state: Current agent state

        Returns:
            Updated state with validation results and retry decision
        """
        query = state["query"]
        user_id = state["user_id"]
        generated_sql = state.get("generated_sql", "")
        table_schemas = state.get("table_schemas", "")
        previous_feedback = state.get("sql_validation_feedback", "")

        # Load SQL validator prompt
        prompt = self.prompt_manager.get_agent_prompt(
            "sql_validator",
            variables={
                "user_query": query,
                "sql_query": generated_sql,
                "table_schema": table_schemas,
                "user_id": user_id,
                "previous_feedback": previous_feedback or "No previous feedback"
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

        return {
            "sql_validation": validation,
            "sql_validation_feedback": validation.get("feedback", ""),
            "sql_retry_count": retry_count + 1 if needs_retry else retry_count,
            "next_step": "retry_sql" if needs_retry else "execute_sql",
        }

    def sql_executor_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute validated SQL query.

        Runs the validated SQL query against Athena and returns results.

        Args:
            state: Current agent state

        Returns:
            Updated state with query results
        """
        from tools.athena_tools import athena_query_tool

        user_id = state["user_id"]
        generated_sql = state.get("generated_sql", "")

        # Execute the validated SQL query
        try:
            result = athena_query_tool.invoke({
                "query": generated_sql,
                "user_id": user_id
            })

            return {
                "agent_results": {
                    "agent": "sql_executor",
                    "result": result,
                    "sql_query": generated_sql,
                    "status": "completed",
                },
                "raw_data": result,
                "messages": [AIMessage(content=result)],
            }

        except Exception as e:
            error_msg = f"Error executing SQL query: {str(e)}\n\nQuery:\n{generated_sql}"
            return {
                "agent_results": {
                    "agent": "sql_executor",
                    "result": error_msg,
                    "sql_query": generated_sql,
                    "status": "error",
                },
                "raw_data": error_msg,
                "messages": [AIMessage(content=error_msg)],
            }
