"""
Coaching output data models.

These models represent the final coaching recommendations and insights
produced by the Evaluation Coach agent.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .analysis_models import Evidence, RootCauseCategory
from .jira_models import Scope


class ImprovementImpact(str, Enum):
    """Expected impact of an improvement."""

    TRANSFORMATIONAL = "Transformational"  # >50% improvement
    HIGH = "High"  # 20-50% improvement
    MEDIUM = "Medium"  # 10-20% improvement
    LOW = "Low"  # <10% improvement


class ImprovementEffort(str, Enum):
    """Effort required to implement an improvement."""

    LOW = "Low"  # <1 week
    MEDIUM = "Medium"  # 1-4 weeks
    HIGH = "High"  # 1-3 months
    VERY_HIGH = "VeryHigh"  # >3 months


class ActionableStep(BaseModel):
    """A specific actionable step within an improvement proposal."""

    step_number: int
    description: str
    responsible_role: str = Field(
        ..., description="Who should own this (e.g., 'Scrum Master', 'Product Owner')"
    )
    estimated_effort: str = Field(..., description="Time estimate")
    dependencies: List[int] = Field(
        default_factory=list, description="Step numbers this depends on"
    )


class ImprovementProposal(BaseModel):
    """
    A specific, actionable improvement proposal.

    Each proposal is:
    - Specific: Clear scope and target
    - Actionable: Contains concrete steps
    - Measurable: Success criteria defined
    - Evidence-based: Linked to data
    """

    id: str = Field(..., description="Unique identifier")
    title: str
    description: str

    # Scope
    scope: str
    scope_type: Scope

    # Categorization
    root_cause_category: RootCauseCategory
    addresses_patterns: List[str] = Field(
        default_factory=list, description="Pattern IDs this proposal addresses"
    )

    # Impact and effort
    expected_impact: ImprovementImpact
    implementation_effort: ImprovementEffort
    priority_score: float = Field(
        ..., ge=0.0, le=100.0, description="0-100 priority score"
    )

    # Evidence and rationale
    evidence: List[Evidence] = Field(default_factory=list)
    rationale: str = Field(..., description="Why this improvement is recommended")

    # Actionable steps
    steps: List[ActionableStep] = Field(default_factory=list)

    # Success criteria
    success_metrics: List[str] = Field(
        default_factory=list, description="How to measure success"
    )
    target_improvement: str = Field(
        ...,
        description="Specific improvement target (e.g., 'Reduce cycle time by 30%')",
    )

    # Risks and considerations
    risks: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)

    # Timeline
    estimated_timeline: str = Field(..., description="Expected implementation timeline")
    quick_wins: List[str] = Field(
        default_factory=list, description="Quick wins that can be achieved immediately"
    )


class Insight(BaseModel):
    """
    A key insight derived from analysis.

    Insights are interpretations of data that provide understanding
    but may not directly lead to action.
    """

    title: str
    description: str
    scope: str
    scope_type: Scope

    # Supporting data
    evidence: List[Evidence] = Field(default_factory=list)

    # Context
    implication: str = Field(
        ..., description="What this means for the team/ART/portfolio"
    )

    # Related proposals
    related_proposals: List[str] = Field(
        default_factory=list, description="IDs of related improvement proposals"
    )


class ExecutiveSummary(BaseModel):
    """High-level executive summary of analysis."""

    scope: str
    scope_type: Scope
    time_period: str = Field(
        ..., description="Time period analyzed (e.g., 'Q4 2025', 'Sprint 42')"
    )

    # Key highlights
    key_achievements: List[str] = Field(default_factory=list)
    key_challenges: List[str] = Field(default_factory=list)

    # Metrics summary
    overall_health_score: float = Field(
        ..., ge=0.0, le=100.0, description="0-100 health score"
    )
    predictability_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    flow_efficiency_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Priorities
    top_priorities: List[str] = Field(
        default_factory=list, description="Top 3-5 priorities for improvement"
    )

    # Trend indicators
    trends: Dict[str, str] = Field(
        default_factory=dict,
        description="Key metrics and their trends (e.g., {'lead_time': 'improving', 'quality': 'stable'})",
    )


class CoachingReport(BaseModel):
    """
    Complete coaching report for a scope.

    This is the main output of the Evaluation Coach agent.
    """

    # Metadata
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(default="Evaluation Coach v1.0")

    # Scope
    scope: str
    scope_type: Scope
    analysis_period_start: datetime
    analysis_period_end: datetime

    # Executive summary
    executive_summary: ExecutiveSummary

    # Insights
    insights: List[Insight] = Field(default_factory=list)

    # Improvement proposals
    improvement_proposals: List[ImprovementProposal] = Field(default_factory=list)

    # Prioritized action list
    prioritized_actions: List[str] = Field(
        default_factory=list,
        description="Ordered list of improvement proposal IDs by priority",
    )

    # Supporting data references
    metrics_snapshot_id: Optional[str] = None
    analysis_result_id: Optional[str] = None

    # Knowledge base references
    knowledge_sources_used: List[str] = Field(
        default_factory=list, description="Knowledge sources consulted during analysis"
    )

    # Explanation and traceability
    reasoning_chain: List[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning chain for transparency",
    )

    # Quality indicators
    confidence_level: str = Field("High", description="High, Medium, or Low confidence")
    data_completeness: float = Field(1.0, ge=0.0, le=1.0)

    # Coaching philosophy statement
    coaching_note: str = Field(
        default="This analysis focuses on systemic improvement, not individual performance. "
        "All recommendations are evidence-based and align with Agile and SAFe principles.",
        description="Philosophical framing for the report",
    )


class TeamLevelReport(CoachingReport):
    """Team-specific coaching report with team-level context."""

    team_name: str
    art_name: Optional[str] = None

    # Team-specific metrics
    team_velocity_trend: Optional[str] = None
    team_capacity_utilization: Optional[float] = None
    team_stability_score: Optional[float] = None


class ARTLevelReport(CoachingReport):
    """ART-level coaching report with cross-team insights."""

    art_name: str

    # ART-specific metrics
    pi_predictability: Optional[float] = None
    cross_team_dependencies_count: int = 0

    # Team comparisons
    team_performance_comparison: Dict[str, Any] = Field(
        default_factory=dict, description="Comparative view of teams within the ART"
    )


class PortfolioLevelReport(CoachingReport):
    """Portfolio-level coaching report with strategic alignment."""

    portfolio_name: str

    # Strategic alignment
    strategic_theme_coverage: Dict[str, float] = Field(
        default_factory=dict,
        description="Coverage of each strategic theme (percentage)",
    )

    # ART comparisons
    art_performance_comparison: Dict[str, Any] = Field(
        default_factory=dict,
        description="Comparative view of ARTs within the portfolio",
    )

    # Investment distribution
    investment_by_theme: Dict[str, float] = Field(
        default_factory=dict,
        description="Investment distribution across themes (percentage)",
    )
