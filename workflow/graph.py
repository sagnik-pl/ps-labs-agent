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
    START → planner ──→ query_assessment ──→ router ──→ [single OR multi-intent execution]
              ↓              ↓       ↑                  │
              ↓              ↓       └─ retry ──────────┤
              ↓              ↓       (if incomplete)    │
              ↓              └─→ router ────────────────┤
              ↓              (single-intent, skip       │
              ↓               assessment)                │
              └─→ END                                    │
              (out-of-scope/needs-clarification)        │
                                                         │
    Single-Intent Path: ─────────────────────────────────┘
    router → sql_generator → sql_validator → sql_executor → data_interpreter
                   ↑              ↓
                   └─ sql_corrector ──┘
                      (if validation fails - analyzes errors & provides fix recommendations)

    Multi-Intent Path: ───────────────────────────────────┐
    router → multi_intent_executor → data_interpreter     │
             └→ For each sub-query (parallel):            │
                sql_generator → sql_validator → sql_corrector (if needed)
                → sql_executor (internal)                 │
                                                           │
    Final Path (both converge): ───────────────────────────┘
    data_interpreter → interpretation_validator → output_formatter → interpreter → END
                             ↓
                 retry_interpretation ─┘

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

    # Multi-intent execution layer (parallel sub-query orchestration)
    workflow.add_node("multi_intent_executor", nodes.multi_intent_executor_node)

    # SQL generation and validation layer
    workflow.add_node("sql_generator", nodes.sql_generator_node)
    workflow.add_node("sql_validator", nodes.sql_validator_node)
    workflow.add_node("sql_corrector", nodes.sql_corrector_node)  # Error analysis and fix recommendations
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

    # router -> multi_intent_executor OR sql_generator (based on query type)
    def route_to_executor(state: AgentState) -> str:
        """
        Route to appropriate executor based on query classification.

        - Multi-intent queries → multi_intent_executor (orchestrated parallel execution)
        - Single-intent queries → sql_generator (direct SQL pipeline)
        """
        routing_decision = state.get("routing_decision", {})
        next_step = routing_decision.get("next_step", "sql_generator")

        if next_step == "multi_intent_executor":
            return "multi_intent_executor"
        return "sql_generator"

    workflow.add_conditional_edges(
        "router",
        route_to_executor,
        {
            "multi_intent_executor": "multi_intent_executor",
            "sql_generator": "sql_generator",
        },
    )

    # multi_intent_executor -> data_interpreter (skip SQL pipeline, already executed)
    workflow.add_edge("multi_intent_executor", "data_interpreter")

    # sql_generator -> sql_validator
    workflow.add_edge("sql_generator", "sql_validator")

    # sql_validator -> sql_executor or sql_corrector (on validation failure)
    def should_retry_sql(state: AgentState) -> Literal["sql_executor", "sql_corrector"]:
        """Determine if we need to correct SQL or proceed to execution."""
        next_step = state.get("next_step", "execute_sql")

        if next_step == "retry_sql":
            return "sql_corrector"  # Route to corrector for error analysis
        return "sql_executor"

    workflow.add_conditional_edges(
        "sql_validator",
        should_retry_sql,
        {
            "sql_corrector": "sql_corrector",
            "sql_executor": "sql_executor",
        },
    )

    # sql_corrector -> sql_generator (with fix recommendations)
    workflow.add_edge("sql_corrector", "sql_generator")

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
