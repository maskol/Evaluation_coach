"""
Metrics data models for the Evaluation Coach.

These models represent calculated metrics and statistical measures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Types of metrics calculated by the system."""

    FLOW = "Flow"
    PREDICTABILITY = "Predictability"
    QUALITY = "Quality"
    TEAM_HEALTH = "TeamHealth"


class Trend(str, Enum):
    """Trend direction."""

    IMPROVING = "Improving"
    STABLE = "Stable"
    DECLINING = "Declining"
    INSUFFICIENT_DATA = "InsufficientData"


class TimeWindow(BaseModel):
    """Represents a time window for analysis."""

    start_date: datetime
    end_date: datetime
    label: str = Field(
        ..., description="Human-readable label (e.g., 'Sprint 42', 'PI 2024.Q1')"
    )

    @property
    def duration_days(self) -> float:
        """Calculate duration in days."""
        return (self.end_date - self.start_date).total_seconds() / 86400


class MetricValue(BaseModel):
    """A single metric measurement."""

    metric_name: str
    value: float
    unit: str = Field(
        ..., description="Unit of measurement (e.g., 'hours', 'count', 'percentage')"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Contextual information
    scope: str = Field(
        ..., description="Scope this metric applies to (team/ART/portfolio name)"
    )
    scope_type: str = Field(..., description="Type of scope (Team, ART, Portfolio)")
    time_window: Optional[TimeWindow] = None


class FlowMetrics(BaseModel):
    """Flow-based metrics for a given scope and time window."""

    scope: str
    scope_type: str
    time_window: TimeWindow

    # Core flow metrics
    throughput: Optional[float] = Field(
        None, description="Items completed per unit time"
    )
    wip: Optional[float] = Field(None, description="Average work in progress")
    lead_time_avg_hours: Optional[float] = Field(None, description="Average lead time")
    lead_time_p50_hours: Optional[float] = Field(None, description="Median lead time")
    lead_time_p85_hours: Optional[float] = Field(
        None, description="85th percentile lead time"
    )
    lead_time_p95_hours: Optional[float] = Field(
        None, description="95th percentile lead time"
    )
    cycle_time_avg_hours: Optional[float] = Field(
        None, description="Average cycle time"
    )
    cycle_time_p50_hours: Optional[float] = Field(None, description="Median cycle time")
    cycle_time_p85_hours: Optional[float] = Field(
        None, description="85th percentile cycle time"
    )

    # Distribution
    lead_time_std_dev: Optional[float] = Field(
        None, description="Standard deviation of lead time"
    )
    cycle_time_std_dev: Optional[float] = Field(
        None, description="Standard deviation of cycle time"
    )

    # Breakdown by issue type
    throughput_by_type: Dict[str, float] = Field(default_factory=dict)
    lead_time_by_type: Dict[str, float] = Field(default_factory=dict)


class PredictabilityMetrics(BaseModel):
    """Predictability metrics for a given scope and time window."""

    scope: str
    scope_type: str
    time_window: TimeWindow

    # Commitment reliability
    commitment_reliability: Optional[float] = Field(
        None, description="Percentage of committed items completed (0.0-1.0)"
    )
    planned_vs_delivered_ratio: Optional[float] = Field(
        None, description="Ratio of delivered to planned (can be >1 if overdelivered)"
    )

    # Scope stability
    scope_change_rate: Optional[float] = Field(
        None, description="Percentage of scope changes during execution"
    )
    scope_additions: int = Field(0, description="Count of items added after commitment")
    scope_removals: int = Field(
        0, description="Count of items removed after commitment"
    )

    # Velocity
    velocity_avg: Optional[float] = Field(
        None, description="Average velocity (story points)"
    )
    velocity_std_dev: Optional[float] = Field(
        None, description="Velocity standard deviation"
    )
    velocity_trend: Optional[Trend] = None

    # Estimation accuracy
    estimation_accuracy: Optional[float] = Field(
        None, description="Ratio of estimated to actual effort (1.0 = perfect)"
    )


class QualityMetrics(BaseModel):
    """Quality and flow efficiency metrics."""

    scope: str
    scope_type: str
    time_window: TimeWindow

    # Flow efficiency
    flow_efficiency: Optional[float] = Field(
        None, description="Ratio of active time to total time (0.0-1.0)"
    )
    wait_time_avg_hours: Optional[float] = Field(
        None, description="Average wait/blocked time"
    )

    # Blocked time
    blocked_time_total_hours: Optional[float] = Field(
        None, description="Total blocked time"
    )
    blocked_time_percentage: Optional[float] = Field(
        None, description="Percentage of time blocked"
    )
    blocked_issues_count: int = Field(0, description="Number of issues blocked")
    blocked_issues_resolved: int = Field(0, description="Number of blocks resolved")
    avg_time_to_resolve_block_hours: Optional[float] = None

    # Rework
    rework_rate: Optional[float] = Field(
        None, description="Percentage of completed work requiring rework"
    )
    bug_rate: Optional[float] = Field(
        None, description="Ratio of bugs to features/stories"
    )

    # Defects
    defects_found: int = Field(0, description="Defects discovered")
    defects_escaped_to_production: int = Field(
        0, description="Defects found in production"
    )


class TeamHealthMetrics(BaseModel):
    """Team health and sustainability metrics."""

    scope: str  # Should be a team name
    time_window: TimeWindow

    # Workload
    avg_wip_per_person: Optional[float] = None
    max_wip_per_person: Optional[float] = None

    # Stability
    team_size: int = Field(0, description="Number of team members")
    team_churn: Optional[float] = Field(
        None, description="Percentage of team members who joined/left"
    )

    # Collaboration
    cross_team_dependencies: int = Field(
        0, description="Number of cross-team dependencies"
    )
    cross_team_blocks: int = Field(
        0, description="Number of cross-team blocking issues"
    )

    # Focus
    context_switches: Optional[int] = Field(
        None, description="Average number of concurrent work items per person"
    )
    unplanned_work_percentage: Optional[float] = Field(
        None, description="Percentage of work that was unplanned"
    )


class MetricsTrend(BaseModel):
    """Time-series trend for a specific metric."""

    metric_name: str
    scope: str
    scope_type: str

    # Data points
    data_points: List[MetricValue] = Field(default_factory=list)

    # Trend analysis
    trend_direction: Trend
    rate_of_change: Optional[float] = Field(
        None, description="Rate of change per time period"
    )

    # Statistical measures
    mean: Optional[float] = None
    median: Optional[float] = None
    std_dev: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class MetricsSnapshot(BaseModel):
    """Complete metrics snapshot for a scope and time window."""

    scope: str
    scope_type: str
    time_window: TimeWindow
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metrics collections
    flow_metrics: Optional[FlowMetrics] = None
    predictability_metrics: Optional[PredictabilityMetrics] = None
    quality_metrics: Optional[QualityMetrics] = None
    team_health_metrics: Optional[TeamHealthMetrics] = None

    # Raw issue count for context
    total_issues_analyzed: int = 0
    completed_issues: int = 0
    in_progress_issues: int = 0

    # Data quality indicators
    data_completeness: float = Field(
        1.0, description="Percentage of expected data fields populated (0.0-1.0)"
    )
    confidence_level: str = Field(
        "High", description="Confidence in the metrics (High/Medium/Low)"
    )


class BenchmarkComparison(BaseModel):
    """Comparison of metrics against benchmarks."""

    metric_name: str
    current_value: float
    benchmark_value: Optional[float] = None
    industry_average: Optional[float] = None

    # Relative performance
    vs_benchmark_percentage: Optional[float] = Field(
        None, description="Percentage difference from benchmark (positive is better)"
    )
    performance_category: str = Field(
        ...,
        description="Performance category: Excellent, Good, Average, Below Average, Poor",
    )
