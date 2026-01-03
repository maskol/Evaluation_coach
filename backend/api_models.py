"""
Pydantic models for API request/response validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class ScopeType(str, Enum):
    PORTFOLIO = "portfolio"
    ART = "art"
    TEAM = "team"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class TimeRange(str, Enum):
    CURRENT_PI = "current_pi"
    LAST_PI = "last_pi"
    LAST_QUARTER = "last_quarter"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"


# Request Models
class AnalysisRequest(BaseModel):
    scope: ScopeType
    scope_id: Optional[str] = None
    time_range: TimeRange = TimeRange.LAST_PI
    metric_focus: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: str
    context: Optional[Dict[str, Any]] = None


class InsightFeedback(BaseModel):
    insight_id: int
    action: str  # accept, dismiss
    feedback: Optional[str] = None


# Response Models
class MetricValue(BaseModel):
    name: str
    value: float
    unit: str
    status: str  # healthy, warning, critical
    trend: str  # up, down, stable
    benchmark: Optional[Dict[str, float]] = None


class HealthScorecard(BaseModel):
    id: int
    scope: str
    scope_id: Optional[str]
    overall_score: float
    dimension_scores: Dict[str, float]
    metrics: List[MetricValue]
    time_period_start: datetime
    time_period_end: datetime
    created_at: datetime


class RootCause(BaseModel):
    description: str
    evidence: List[str]
    confidence: float
    reference: Optional[str] = None


class Action(BaseModel):
    timeframe: str  # short-term, medium-term, long-term
    description: str
    owner: str
    effort: str
    dependencies: List[str]
    success_signal: str


class ExpectedOutcome(BaseModel):
    metrics_to_watch: List[str]
    leading_indicators: List[str]
    lagging_indicators: List[str]
    timeline: str
    risks: List[str]


class InsightResponse(BaseModel):
    id: int
    title: str
    severity: str
    confidence: float
    scope: str
    scope_id: Optional[str]

    observation: str
    interpretation: str
    root_causes: List[RootCause]
    recommended_actions: List[Action]
    expected_outcomes: ExpectedOutcome

    metric_references: List[str]
    evidence: List[str]
    status: str
    created_at: datetime


class ChatResponse(BaseModel):
    message: str
    context: Dict[str, Any]
    timestamp: datetime


class DashboardData(BaseModel):
    portfolio_metrics: List[MetricValue]
    art_comparison: List[Dict[str, Any]]
    recent_insights: List[InsightResponse]
    trends: Dict[str, Any]
    current_pi: Optional[str] = None
    available_pis: Optional[List[str]] = None
    selected_pis: Optional[List[str]] = None


class ARTPerformance(BaseModel):
    art_name: str
    flow_efficiency: float
    pi_predictability: float
    quality_score: float
    team_stability: float
    status: str


# Jira Models
class JiraIssueBase(BaseModel):
    issue_key: str
    issue_type: str
    summary: str
    status: str
    team: Optional[str] = None
    art: Optional[str] = None


class JiraIssueCreate(JiraIssueBase):
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created_date: datetime
    story_points: Optional[float] = None
    sprint: Optional[str] = None
    epic: Optional[str] = None
    labels: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class JiraIssueResponse(JiraIssueBase):
    id: int
    assignee: Optional[str]
    created_date: datetime
    resolved_date: Optional[datetime]
    story_points: Optional[float]

    class Config:
        from_attributes = True


# Export/Report Models
class ReportRequest(BaseModel):
    scope: ScopeType
    scope_id: Optional[str] = None
    time_range: TimeRange
    include_sections: List[str] = [
        "scorecard",
        "metrics",
        "insights",
        "recommendations",
    ]
    format: str = "pdf"  # pdf, html, json


class ReportResponse(BaseModel):
    report_id: str
    download_url: str
    expires_at: datetime


# System Status
class SystemStatus(BaseModel):
    status: str
    database_connected: bool
    jira_connected: bool
    llm_available: bool
    leadtime_server_connected: bool
    last_sync: Optional[datetime]
    total_issues: int
    total_insights: int


# Lead-Time Models
class LeadTimeStageMetrics(BaseModel):
    """Metrics for a single workflow stage."""

    in_backlog: Optional[float] = None
    in_planned: Optional[float] = None
    in_analysis: Optional[float] = None
    in_progress: Optional[float] = None
    in_reviewing: Optional[float] = None
    in_sit: Optional[float] = None
    in_uat: Optional[float] = None
    ready_for_deployment: Optional[float] = None
    deployed: Optional[float] = None
    total_leadtime: Optional[float] = None


class LeadTimeFeature(BaseModel):
    """Feature with lead-time data."""

    issue_key: str
    summary: str
    status: str
    art: Optional[str] = None
    pi: Optional[str] = None
    development_team: Optional[str] = None
    leadtime: LeadTimeStageMetrics


class LeadTimeStatistics(BaseModel):
    """Statistical analysis of lead-time."""

    mean: float
    median: float
    min: float
    max: float
    stdev: float
    p85: float
    p95: float
    count: int


class LeadTimeAnalysisResponse(BaseModel):
    """Response for lead-time analysis."""

    stage_statistics: Dict[str, LeadTimeStatistics]
    scope: Dict[str, Any]
    data_source: str


class LeadTimeFilterOptions(BaseModel):
    """Available filter options from lead-time server."""

    arts: List[str]
    pis: List[str]
    teams: List[str]
    statuses: List[str]


class LeadTimeSummaryRequest(BaseModel):
    """Request for lead-time summary."""

    art: Optional[str] = None
    pi: Optional[str] = None
