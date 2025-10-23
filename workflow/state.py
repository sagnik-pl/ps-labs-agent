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
    routing_decision: Optional[Dict[str, Any]]  # Which agent(s) to use
    next_step: Optional[str]  # Next node to execute

    # Agent Execution
    current_agent: Optional[str]  # Currently executing agent
    agent_results: Dict[str, Any]  # Results from agent execution

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
