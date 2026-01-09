"""
LangGraph agent state management.

The state flows through all nodes in the agent workflow, accumulating data
and analysis results at each step.
"""

from datetime import datetime
from operator import add
from typing import Annotated, Any, Dict, List, Optional

from typing_extensions import TypedDict


class AgentState(TypedDict):
    """
    Complete state for the Evaluation Coach agent.

    This state flows through all nodes in the LangGraph workflow.
    Each node reads from and writes to this state.

    The operator annotation allows incremental updates:
    - add: Appends to lists rather than replacing
    """

    # Input parameters (set at initialization)
    scope: str  # The entity being analyzed (team name, ART name, or portfolio name)
    scope_type: str  # "Team", "ART", or "Portfolio"
    time_window_start: datetime
    time_window_end: datetime

    # Optional filters
    jira_project_keys: List[str]
    include_issue_types: Optional[List[str]]

    # Node 1: Data Collector outputs
    raw_issues: Annotated[List[Dict[str, Any]], add]  # Raw Jira issue data
    normalized_issues: Annotated[List, add]  # Normalized Issue objects
    sprints: Annotated[List, add]  # Sprint objects
    program_increments: Annotated[List, add]  # ProgramIncrement objects
    data_collection_timestamp: Optional[datetime]
    data_quality_score: float  # 0.0-1.0

    # Node 2: Metrics Engine outputs
    metrics_snapshot: Optional[Any]  # MetricsSnapshot object
    flow_metrics: Optional[Any]  # FlowMetrics
    predictability_metrics: Optional[Any]  # PredictabilityMetrics
    quality_metrics: Optional[Any]  # QualityMetrics
    team_health_metrics: Optional[Any]  # TeamHealthMetrics (if scope is Team)
    metrics_calculation_timestamp: Optional[datetime]

    # Node 3: Pattern Detection outputs
    patterns: Annotated[List, add]  # List of Pattern objects
    bottlenecks: Annotated[List, add]  # List of Bottleneck objects
    anomalies: Annotated[List, add]  # List of Anomaly objects
    trends: Annotated[List, add]  # List of TrendAnalysis objects
    analysis_result: Optional[Any]  # AnalysisResult object
    pattern_detection_timestamp: Optional[datetime]

    # Node 4: Knowledge Retrieval outputs
    retrieved_documents: Annotated[List[str], add]  # Retrieved knowledge snippets
    knowledge_sources: Annotated[List[str], add]  # Source names/IDs
    rag_queries: Annotated[List[str], add]  # Queries sent to RAG
    knowledge_retrieval_timestamp: Optional[datetime]

    # Node 4b: Little's Law Analyzer outputs
    littles_law_metrics: Optional[Dict[str, Any]]  # Calculated L, λ, W metrics
    littles_law_insights: Annotated[List, add]  # Little's Law specific insights
    littles_law_analysis_timestamp: Optional[datetime]

    # Node 5: Reasoning & Coaching outputs
    insights: Annotated[List, add]  # List of Insight objects
    improvement_proposals: Annotated[List, add]  # List of ImprovementProposal objects
    prioritized_proposal_ids: List[str]  # Ordered by priority
    executive_summary: Optional[Any]  # ExecutiveSummary object
    reasoning_chain: Annotated[
        List[str], add
    ]  # Step-by-step reasoning for explainability
    coaching_timestamp: Optional[datetime]

    # Node 6: Explanation Generator outputs
    coaching_report: Optional[Any]  # Final CoachingReport object
    report_sections: Dict[str, str]  # Generated report sections (HTML or Markdown)
    explanation_timestamp: Optional[datetime]

    # Error handling
    errors: Annotated[List[str], add]  # Any errors encountered
    warnings: Annotated[List[str], add]  # Warnings or caveats

    # Agent metadata
    agent_version: str
    workflow_start_time: datetime
    workflow_end_time: Optional[datetime]

    # Internal routing
    next_node: Optional[str]  # Used for conditional routing
    should_continue: bool  # Whether to continue processing


def create_initial_state(
    scope: str,
    scope_type: str,
    time_window_start: datetime,
    time_window_end: datetime,
    jira_project_keys: Optional[List[str]] = None,
    include_issue_types: Optional[List[str]] = None,
) -> AgentState:
    """
    Create an initial agent state with the given parameters.

    Args:
        scope: The entity being analyzed (team name, ART name, or portfolio name)
        scope_type: "Team", "ART", or "Portfolio"
        time_window_start: Start of analysis period
        time_window_end: End of analysis period
        jira_project_keys: Optional list of Jira project keys to filter
        include_issue_types: Optional list of issue types to include

    Returns:
        Initialized AgentState
    """
    return AgentState(
        # Input parameters
        scope=scope,
        scope_type=scope_type,
        time_window_start=time_window_start,
        time_window_end=time_window_end,
        jira_project_keys=jira_project_keys or [],
        include_issue_types=include_issue_types,
        # Initialize all collections as empty
        raw_issues=[],
        normalized_issues=[],
        sprints=[],
        program_increments=[],
        data_collection_timestamp=None,
        data_quality_score=1.0,
        metrics_snapshot=None,
        flow_metrics=None,
        predictability_metrics=None,
        quality_metrics=None,
        team_health_metrics=None,
        metrics_calculation_timestamp=None,
        patterns=[],
        bottlenecks=[],
        anomalies=[],
        trends=[],
        analysis_result=None,
        pattern_detection_timestamp=None,
        retrieved_documents=[],
        knowledge_sources=[],
        rag_queries=[],
        knowledge_retrieval_timestamp=None,
        littles_law_metrics=None,
        littles_law_insights=[],
        littles_law_analysis_timestamp=None,
        insights=[],
        improvement_proposals=[],
        prioritized_proposal_ids=[],
        executive_summary=None,
        reasoning_chain=[],
        coaching_timestamp=None,
        coaching_report=None,
        report_sections={},
        explanation_timestamp=None,
        errors=[],
        warnings=[],
        agent_version="1.0.0",
        workflow_start_time=datetime.utcnow(),
        workflow_end_time=None,
        next_node=None,
        should_continue=True,
    )
