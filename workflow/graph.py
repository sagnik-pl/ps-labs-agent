"""
LangGraph workflow definition for the multi-agent system.
"""
from typing import Literal
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from workflow.state import AgentState
from workflow.nodes import WorkflowNodes


def create_agent_workflow(checkpointer=None):
    """
    Create the LangGraph agent workflow.

    Workflow:
    START → planner → router → sql_generator → sql_validator → sql_executor → data_interpreter
                                     ↑              ↓                              ↓
                                     └─ retry_sql ──┘                  interpretation_validator
                                                                                 ↓        ↓
                                                                    retry_interpretation  interpreter → END
                                                                           ↑                  ↓
                                                                           └──────────────────┘

    Args:
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize nodes
    nodes = WorkflowNodes()

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("planner", nodes.planner_node)
    workflow.add_node("router", nodes.router_node)

    # SQL generation and validation layer
    workflow.add_node("sql_generator", nodes.sql_generator_node)
    workflow.add_node("sql_validator", nodes.sql_validator_node)
    workflow.add_node("sql_executor", nodes.sql_executor_node)

    # Data interpretation layer
    workflow.add_node("data_interpreter", nodes.data_interpreter_node)
    workflow.add_node("interpretation_validator", nodes.interpretation_validator_node)
    workflow.add_node("interpreter", nodes.interpreter_node)

    # Define edges
    # START -> planner
    workflow.add_edge(START, "planner")

    # planner -> router
    workflow.add_edge("planner", "router")

    # router -> sql_generator (for data analytics queries)
    def route_to_agent(state: AgentState) -> str:
        """Determine which agent to route to."""
        next_step = state.get("next_step", "sql_generator")

        # Map agent names to node names
        agent_map = {
            "data_analytics_agent": "sql_generator",
            "data_analytics": "sql_generator",
            "sql_generator": "sql_generator",
            # Future agents will be added here
        }

        return agent_map.get(next_step, "sql_generator")

    workflow.add_conditional_edges(
        "router",
        route_to_agent,
        {
            "sql_generator": "sql_generator",
            # Future: add more agent routes here
        },
    )

    # sql_generator -> sql_validator
    workflow.add_edge("sql_generator", "sql_validator")

    # sql_validator -> sql_executor or retry sql_generator
    def should_retry_sql(state: AgentState) -> Literal["sql_executor", "sql_generator"]:
        """Determine if we need to retry SQL generation or proceed to execution."""
        next_step = state.get("next_step", "execute_sql")

        if next_step == "retry_sql":
            return "sql_generator"
        return "sql_executor"

    workflow.add_conditional_edges(
        "sql_validator",
        should_retry_sql,
        {
            "sql_generator": "sql_generator",
            "sql_executor": "sql_executor",
        },
    )

    # sql_executor -> data_interpreter
    workflow.add_edge("sql_executor", "data_interpreter")

    # data_interpreter -> interpretation_validator
    workflow.add_edge("data_interpreter", "interpretation_validator")

    # interpretation_validator -> data_interpreter (retry) or interpreter (final)
    def should_retry_interpretation(state: AgentState) -> Literal["data_interpreter", "interpreter"]:
        """Determine if we need to retry interpretation or proceed to final response."""
        next_step = state.get("next_step", "final_interpreter")

        if next_step == "retry_interpretation":
            return "data_interpreter"
        return "interpreter"

    workflow.add_conditional_edges(
        "interpretation_validator",
        should_retry_interpretation,
        {
            "data_interpreter": "data_interpreter",
            "interpreter": "interpreter",
        },
    )

    # interpreter -> END
    workflow.add_edge("interpreter", END)

    # Compile the graph
    if checkpointer is None:
        checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer)

    return app


def visualize_graph(app):
    """
    Visualize the workflow graph (requires graphviz).

    Args:
        app: Compiled LangGraph workflow

    Returns:
        Graph visualization
    """
    try:
        return app.get_graph().draw_mermaid()
    except Exception as e:
        print(f"Could not visualize graph: {e}")
        return None
