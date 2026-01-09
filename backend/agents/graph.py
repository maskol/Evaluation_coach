"""
LangGraph workflow definition for the Evaluation Coach agent.

This module defines the multi-node workflow that orchestrates the analysis process.
"""

from datetime import datetime
from typing import Literal

from langgraph.graph import END, StateGraph

from .nodes.coach import coaching_node
from .nodes.data_collector import data_collector_node
from .nodes.explainer import explainer_node
from .nodes.knowledge_retriever import knowledge_retriever_node
from .nodes.littles_law_analyzer import littles_law_analyzer_node
from .nodes.metrics_engine import metrics_engine_node
from .nodes.pattern_detector import pattern_detector_node
from .state import AgentState


def should_continue_after_data_collection(
    state: AgentState,
) -> Literal["metrics_engine", "end"]:
    """
    Routing logic after data collection.

    If data collection fails or produces insufficient data, end the workflow.
    Otherwise, proceed to metrics calculation.
    """
    if state.get("errors"):
        return "end"

    if not state.get("normalized_issues"):
        return "end"

    # Check data quality threshold
    if state.get("data_quality_score", 0) < 0.3:
        return "end"

    return "metrics_engine"


def should_continue_after_metrics(
    state: AgentState,
) -> Literal["pattern_detector", "littles_law_analyzer", "end"]:
    """
    Routing logic after metrics calculation.

    If metrics calculation fails, end the workflow.
    Otherwise, proceed to both pattern detection and Little's Law analysis.
    """
    if state.get("errors"):
        return "end"

    if not state.get("metrics_snapshot"):
        return "end"

    # For portfolio or PI scope, prefer Little's Law analysis first
    scope_type = state.get("scope_type", "").lower()
    if scope_type in ["portfolio", "pi"]:
        return "littles_law_analyzer"

    return "pattern_detector"


def should_continue_after_littles_law(
    state: AgentState,
) -> Literal["pattern_detector", "end"]:
    """
    Routing logic after Little's Law analysis.

    Always proceed to pattern detection after Little's Law.
    """
    if state.get("errors"):
        return "end"

    return "pattern_detector"


def should_continue_after_patterns(
    state: AgentState,
) -> Literal["knowledge_retriever", "end"]:
    """
    Routing logic after pattern detection.

    Always proceed to knowledge retrieval if we get here, even if no patterns found.
    We still want to provide coaching based on the metrics.
    """
    if state.get("errors"):
        return "end"

    return "knowledge_retriever"


def should_continue_after_knowledge(state: AgentState) -> Literal["coach", "end"]:
    """
    Routing logic after knowledge retrieval.

    Proceed to coaching node.
    """
    if state.get("errors"):
        return "end"

    return "coach"


def should_continue_after_coaching(state: AgentState) -> Literal["explainer", "end"]:
    """
    Routing logic after coaching.

    If we have insights or proposals, generate explanations.
    """
    if state.get("errors"):
        return "end"

    # Even if no proposals, we should generate a report explaining why
    return "explainer"


def create_evaluation_coach_graph() -> StateGraph:
    """
    Create the LangGraph workflow for the Evaluation Coach.

    The workflow follows this structure:

    START
      ↓
    Data Collector (Node 1)
      ↓ [conditional: check data quality]
    Metrics Engine (Node 2)
      ↓ [conditional: check metrics computed]
    Little's Law Analyzer (Node 3a) [for portfolio/PI scope]
      ↓
    Pattern Detector (Node 3b)
      ↓ [conditional: continue even if no patterns]
    Knowledge Retriever (Node 4)
      ↓ [conditional: check knowledge retrieved]
    Coaching (Node 5)
      ↓ [conditional: check proposals generated]
    Explainer (Node 6)
      ↓
    END

    Returns:
        Compiled StateGraph ready for execution
    """

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("data_collector", data_collector_node)
    workflow.add_node("metrics_engine", metrics_engine_node)
    workflow.add_node("littles_law_analyzer", littles_law_analyzer_node)
    workflow.add_node("pattern_detector", pattern_detector_node)
    workflow.add_node("knowledge_retriever", knowledge_retriever_node)
    workflow.add_node("coach", coaching_node)
    workflow.add_node("explainer", explainer_node)

    # Set entry point
    workflow.set_entry_point("data_collector")

    # Add conditional edges
    workflow.add_conditional_edges(
        "data_collector",
        should_continue_after_data_collection,
        {
            "metrics_engine": "metrics_engine",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "metrics_engine",
        should_continue_after_metrics,
        {
            "pattern_detector": "pattern_detector",
            "littles_law_analyzer": "littles_law_analyzer",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "littles_law_analyzer",
        should_continue_after_littles_law,
        {
            "pattern_detector": "pattern_detector",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "pattern_detector",
        should_continue_after_patterns,
        {
            "knowledge_retriever": "knowledge_retriever",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "knowledge_retriever",
        should_continue_after_knowledge,
        {
            "coach": "coach",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "coach",
        should_continue_after_coaching,
        {
            "explainer": "explainer",
            "end": END,
        },
    )

    # Explainer is always the last node
    workflow.add_edge("explainer", END)

    # Compile the graph
    return workflow.compile()


def run_evaluation_coach(
    scope: str,
    scope_type: str,
    time_window_start: datetime,
    time_window_end: datetime,
    jira_project_keys: list[str] | None = None,
    include_issue_types: list[str] | None = None,
) -> AgentState:
    """
    Execute the Evaluation Coach workflow.

    This is the main entry point for running an analysis.

    Args:
        scope: The entity being analyzed (team name, ART name, or portfolio name)
        scope_type: "Team", "ART", or "Portfolio"
        time_window_start: Start of analysis period
        time_window_end: End of analysis period
        jira_project_keys: Optional list of Jira project keys to filter
        include_issue_types: Optional list of issue types to include

    Returns:
        Final AgentState containing all analysis results and the coaching report

    Example:
        >>> from datetime import datetime, timedelta
        >>> result = run_evaluation_coach(
        ...     scope="Platform Team",
        ...     scope_type="Team",
        ...     time_window_start=datetime.now() - timedelta(days=14),
        ...     time_window_end=datetime.now(),
        ...     jira_project_keys=["PLAT"],
        ... )
        >>> print(result["coaching_report"].executive_summary.overall_health_score)
        75.5
    """
    from .state import create_initial_state

    # Create initial state
    initial_state = create_initial_state(
        scope=scope,
        scope_type=scope_type,
        time_window_start=time_window_start,
        time_window_end=time_window_end,
        jira_project_keys=jira_project_keys,
        include_issue_types=include_issue_types,
    )

    # Create and run the graph
    graph = create_evaluation_coach_graph()

    # Execute the workflow
    final_state = graph.invoke(initial_state)

    # Mark workflow end time
    final_state["workflow_end_time"] = datetime.utcnow()

    return final_state


# For visualization and debugging
def visualize_graph(output_path: str = "evaluation_coach_graph.png"):
    """
    Generate a visual representation of the workflow graph.

    Requires graphviz to be installed:
        pip install graphviz

    Args:
        output_path: Path where to save the visualization
    """
    try:
        graph = create_evaluation_coach_graph()

        # Get mermaid representation
        mermaid_code = graph.get_graph().draw_mermaid()

        with open(output_path.replace(".png", ".mmd"), "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        print(f"Graph visualization saved to {output_path.replace('.png', '.mmd')}")
        print("You can visualize this at https://mermaid.live")

    except Exception as e:
        print(f"Could not generate visualization: {e}")
