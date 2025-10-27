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
    START → planner ──→ query_assessment ──→ router → sql_generator → sql_validator → sql_executor → data_interpreter
              ↓              ↓       ↑                     ↑              ↓                              ↓
              ↓              ↓       └─── retry ───────────┘              └─ retry_sql ──┘                  interpretation_validator
              ↓              ↓       (if incomplete)                                                                ↓        ↓
              ↓              ↓                                                                         retry_interpretation  output_formatter → interpreter → END
              ↓              └─→ router (single-intent, skip assessment)                                     ↑                     ↑                 ↓
              ↓                                                                                              └─────────────────────┘                 └──────────┘
              └─→ END (out-of-scope / needs-clarification / greetings)

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
    workflow.add_node("query_assessment", nodes.query_assessment_node)  # Validates decomposition
    workflow.add_node("router", nodes.router_node)

    # SQL generation and validation layer
    workflow.add_node("sql_generator", nodes.sql_generator_node)
    workflow.add_node("sql_validator", nodes.sql_validator_node)
    workflow.add_node("sql_executor", nodes.sql_executor_node)

    # Parallel comparison execution layer - DISABLED FOR REDESIGN
    # workflow.add_node("parallel_comparison", nodes.parallel_comparison_node)

    # Data interpretation layer
    workflow.add_node("data_interpreter", nodes.data_interpreter_node)
    workflow.add_node("interpretation_validator", nodes.interpretation_validator_node)
    workflow.add_node("output_formatter", nodes.output_formatter_node)
    workflow.add_node("interpreter", nodes.interpreter_node)

    # Define edges
    # START -> planner
    workflow.add_edge(START, "planner")

    # planner -> query_assessment OR router OR END
    # - END: out-of-scope/greetings/needs-clarification
    # - query_assessment: multi-intent queries (need validation)
    # - router: single-intent queries (direct execution)
    def route_from_planner(state: AgentState):
        """Determine next step from planner based on query classification."""
        next_step = state.get("next_step", "router")

        # Handle early exits (out-of-scope queries, needs clarification, greetings)
        if next_step == "END":
            return END

        # Handle multi-intent decomposition (route to assessment)
        if next_step == "query_assessment":
            return "query_assessment"

        # Normal single-intent flow
        return "router"

    workflow.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "query_assessment": "query_assessment",
            "router": "router",
            END: END
        }
    )

    # query_assessment -> planner (retry) OR router (proceed)
    def route_from_assessment(state: AgentState):
        """Route based on assessment: retry decomposition or proceed to execution."""
        next_step = state.get("next_step", "router")

        if next_step == "planner":
            return "planner"  # Retry decomposition
        return "router"  # Proceed to execution

    workflow.add_conditional_edges(
        "query_assessment",
        route_from_assessment,
        {
            "planner": "planner",
            "router": "router"
        }
    )

    # router -> sql_generator (for data analytics queries)
    def route_to_agent(state: AgentState) -> str:
        """
        Route to appropriate node based on query type.

        Currently only data analytics queries are supported, which route to sql_generator.
        Future: Add routing logic for other specialized agents here.
        """
        # Currently only data analytics queries supported
        # All queries route through the SQL pipeline: sql_generator → validator → executor
        return "sql_generator"

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

    # DISABLED: parallel_comparison -> output_formatter (skip interpretation since it's already formatted)
    # workflow.add_edge("parallel_comparison", "output_formatter")

    # data_interpreter -> interpretation_validator
    workflow.add_edge("data_interpreter", "interpretation_validator")

    # interpretation_validator -> data_interpreter (retry) or output_formatter
    def should_retry_interpretation(state: AgentState) -> Literal["data_interpreter", "output_formatter"]:
        """Determine if we need to retry interpretation or proceed to formatting."""
        next_step = state.get("next_step", "output_formatter")

        if next_step == "retry_interpretation":
            return "data_interpreter"
        return "output_formatter"

    workflow.add_conditional_edges(
        "interpretation_validator",
        should_retry_interpretation,
        {
            "data_interpreter": "data_interpreter",
            "output_formatter": "output_formatter",
        },
    )

    # output_formatter -> interpreter
    workflow.add_edge("output_formatter", "interpreter")

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
