"""
State schema for the LangGraph agent workflow.
"""
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    State passed between nodes in the agent workflow graph.

    This state maintains all context needed for multi-agent coordination,
    query planning, execution, validation, and interpretation.
    """

    # User & Session Info
    user_id: str
    conversation_id: str
    user_profile: Optional[Dict[str, Any]]  # User business profile for personalization

    # Messages & Query
    messages: Annotated[List[BaseMessage], operator.add]  # Conversation history
    query: str  # Current user query
    context: str  # Conversation context summary

    # Planning & Routing
    plan: Optional[Dict[str, Any]]  # Execution plan
    execution_plan: Optional[Dict[str, Any]]  # Detailed execution plan (for comparisons, etc.)
    routing_decision: Optional[Dict[str, Any]]  # Routing decision (query type, workflow path)
    next_step: Optional[str]  # Next node to execute

    # Query Classification & Decomposition (for multi-intent handling)
    query_classification: Optional[Dict[str, Any]]  # Intent classification result
    # {
    #   "type": "single_intent" | "multi_intent" | "comparison",
    #   "complexity": "simple" | "complex",
    #   "reasoning": str,
    #   "requires_decomposition": bool
    # }

    query_decomposition: Optional[Dict[str, Any]]  # Decomposed queries for multi-intent
    # {
    #   "original_query": str,
    #   "original_goal": str,
    #   "sub_queries": [
    #     {
    #       "id": str,  # e.g., "sq_1", "sq_2"
    #       "question": str,
    #       "intent": str,  # What this sub-query aims to find
    #       "dependencies": List[str],  # IDs of sub-queries this depends on
    #       "execution_order": int
    #     }
    #   ]
    # }

    decomposition_assessment: Optional[Dict[str, Any]]  # Validation of decomposition
    # {
    #   "is_complete": bool,
    #   "can_answer_goal": bool,
    #   "missing_intents": List[str],
    #   "feedback": str,
    #   "retry_needed": bool
    # }

    decomposition_retry_count: int  # Number of decomposition retries

    # Node Execution
    current_agent: Optional[str]  # Currently executing node (legacy field name, contains node name)
    agent_results: Dict[str, Any]  # Results from node execution (legacy field name)

    # SQL Query Generation & Validation (new layer)
    generated_sql: Optional[str]  # Generated SQL query
    sql_validation: Optional[Dict[str, Any]]  # SQL validation result
    sql_validation_feedback: Optional[str]  # Feedback for SQL regeneration
    sql_retry_count: int  # Number of SQL generation retries
    table_schemas: Optional[str]  # Available table schemas for SQL generation

    # Validation & Interpretation
    validation_result: Optional[Dict[str, Any]]  # Validation outcome
    needs_retry: bool  # Whether agent needs to retry
    retry_count: int  # Number of retries attempted

    # Data Interpretation (new specialized layer)
    raw_data: Optional[str]  # Raw data from agent execution
    data_interpretation: Optional[str]  # E-commerce focused interpretation
    interpretation_validation: Optional[Dict[str, Any]]  # Interpretation quality check
    interpretation_feedback: Optional[str]  # Feedback for re-interpretation
    interpretation_retry_count: int  # Number of interpretation retries

    # Final Output
    final_response: Optional[str]  # Synthesized response to user
    metadata: Dict[str, Any]  # Additional metadata
