"""
Analysis and pattern detection data models.

These models represent the output of pattern detection and analysis.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .jira_models import Scope


class Severity(str, Enum):
    """Severity level for findings."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


class PatternType(str, Enum):
    """Types of patterns that can be detected."""

    BOTTLENECK = "Bottleneck"
    ANOMALY = "Anomaly"
    TREND = "Trend"
    DEPENDENCY_ISSUE = "DependencyIssue"
    SCOPE_CREEP = "ScopeCreep"
    CAPACITY_ISSUE = "CapacityIssue"
    QUALITY_ISSUE = "QualityIssue"


class RootCauseCategory(str, Enum):
    """Categories for root cause classification."""

    CAPACITY = "Capacity"  # Not enough people or time
    CAPABILITY = "Capability"  # Skills or knowledge gap
    PROCESS = "Process"  # Inefficient or unclear process
    DEPENDENCY = "Dependency"  # External dependencies or blockers
    TECHNICAL_DEBT = "TechnicalDebt"  # Accumulated technical issues
    SCOPE_MANAGEMENT = "ScopeManagement"  # Poor scope control
    TOOLING = "Tooling"  # Inadequate tools or infrastructure
    ORGANIZATIONAL = "Organizational"  # Structural or cultural issues


class Evidence(BaseModel):
    """Represents evidence supporting a finding or conclusion."""

    description: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    issue_keys: List[str] = Field(
        default_factory=list, description="Related Jira issues"
    )
    data_source: str = Field(..., description="Where this evidence came from")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in this evidence (0.0-1.0)"
    )


class Pattern(BaseModel):
    """Represents a detected pattern in the data."""

    id: str = Field(..., description="Unique identifier for this pattern")
    pattern_type: PatternType
    title: str
    description: str

    # Scope
    scope: str
    scope_type: Scope

    # Severity and impact
    severity: Severity
    impact_description: str = Field(
        ..., description="Describe the impact of this pattern"
    )

    # Evidence
    evidence: List[Evidence] = Field(default_factory=list)

    # Temporal context
    first_observed: datetime
    last_observed: datetime
    frequency: str = Field(
        ...,
        description="How often this pattern occurs (e.g., 'Every sprint', 'Intermittent')",
    )

    # Related entities
    affected_teams: List[str] = Field(default_factory=list)
    affected_issue_keys: List[str] = Field(default_factory=list)

    # Confidence
    confidence_score: float = Field(..., ge=0.0, le=1.0)


class Bottleneck(BaseModel):
    """Represents a flow bottleneck."""

    location: str = Field(
        ..., description="Where the bottleneck occurs (e.g., 'Code Review', 'QA')"
    )
    scope: str
    scope_type: Scope

    # Metrics
    avg_wait_time_hours: float
    affected_items_count: int
    throughput_impact_percentage: Optional[float] = Field(
        None, description="Estimated impact on throughput"
    )

    # Evidence
    evidence: List[Evidence] = Field(default_factory=list)

    # Root cause hypothesis
    suspected_root_cause: RootCauseCategory
    root_cause_explanation: str


class Anomaly(BaseModel):
    """Represents a statistical anomaly."""

    metric_name: str
    scope: str
    scope_type: Scope

    # Anomaly details
    observed_value: float
    expected_value: float
    deviation_percentage: float
    statistical_significance: float = Field(..., description="p-value or similar")

    # Context
    observation_date: datetime
    description: str

    # Is this a positive or negative anomaly?
    is_positive: bool = Field(..., description="True if anomaly represents improvement")


class TrendAnalysis(BaseModel):
    """Represents trend analysis results."""

    metric_name: str
    scope: str
    scope_type: Scope

    # Trend details
    direction: str = Field(..., description="Improving, Declining, Stable, Volatile")
    rate_of_change: Optional[float] = None
    confidence: float = Field(..., ge=0.0, le=1.0)

    # Time range
    analysis_start_date: datetime
    analysis_end_date: datetime

    # Statistical
    correlation_coefficient: Optional[float] = None
    p_value: Optional[float] = None

    # Interpretation
    interpretation: str = Field(
        ..., description="Human-readable interpretation of the trend"
    )


class AnalysisResult(BaseModel):
    """Complete analysis result for a scope."""

    scope: str
    scope_type: Scope
    analysis_date: datetime = Field(default_factory=datetime.utcnow)

    # Detected patterns
    patterns: List[Pattern] = Field(default_factory=list)
    bottlenecks: List[Bottleneck] = Field(default_factory=list)
    anomalies: List[Anomaly] = Field(default_factory=list)
    trends: List[TrendAnalysis] = Field(default_factory=list)

    # Summary statistics
    total_patterns_found: int = 0
    critical_issues_count: int = 0
    high_priority_issues_count: int = 0

    # Data quality
    data_quality_score: float = Field(1.0, ge=0.0, le=1.0)
    analysis_confidence: str = Field("High", description="High, Medium, or Low")

    # Metadata
    analysis_duration_seconds: Optional[float] = None
    data_sources: List[str] = Field(default_factory=list)
