"""
Core Jira data models for the Evaluation Coach.

These models represent normalized Jira entities used throughout the system.
All timestamps are in UTC. All optional fields use None as default.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class IssueType(str, Enum):
    """Jira issue types relevant to SAFe/Agile execution."""

    EPIC = "Epic"
    FEATURE = "Feature"
    STORY = "Story"
    ENABLER = "Enabler"
    BUG = "Bug"
    TASK = "Task"
    SPIKE = "Spike"


class IssueStatus(str, Enum):
    """Normalized issue statuses."""

    BACKLOG = "Backlog"
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    BLOCKED = "Blocked"
    DONE = "Done"
    CANCELLED = "Cancelled"


class Priority(str, Enum):
    """Issue priority levels."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Scope(str, Enum):
    """Analysis scope levels."""

    PORTFOLIO = "Portfolio"
    ART = "ART"
    TEAM = "Team"


class StatusTransition(BaseModel):
    """Represents a single status change in an issue's lifecycle."""

    from_status: str
    to_status: str
    transitioned_at: datetime
    transitioned_by: str
    duration_in_previous_status_hours: Optional[float] = None


class Issue(BaseModel):
    """
    Normalized Jira issue representation.

    This model consolidates data from Jira's REST API into a consistent format
    for analysis. All custom fields are mapped to their semantic names.
    """

    key: str = Field(..., description="Jira issue key (e.g., PROJ-123)")
    id: str = Field(..., description="Jira internal ID")
    issue_type: IssueType
    summary: str
    description: Optional[str] = None
    status: str
    priority: Optional[Priority] = None

    # Hierarchy
    parent_key: Optional[str] = Field(
        None, description="Parent issue key (Epic for Story)"
    )
    epic_key: Optional[str] = Field(None, description="Epic key for this issue")

    # Ownership
    assignee: Optional[str] = None
    reporter: str
    team: Optional[str] = Field(None, description="Agile team name")
    art: Optional[str] = Field(None, description="Agile Release Train name")

    # Time tracking
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Estimation
    story_points: Optional[float] = None
    original_estimate_hours: Optional[float] = None
    time_spent_hours: Optional[float] = None
    remaining_estimate_hours: Optional[float] = None

    # Sprint/PI tracking
    sprint: Optional[str] = Field(None, description="Current or last sprint name")
    sprint_id: Optional[str] = None
    pi: Optional[str] = Field(None, description="Program Increment identifier")

    # Status history
    status_transitions: List[StatusTransition] = Field(default_factory=list)

    # Dependencies and blockers
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    blocked_since: Optional[datetime] = None
    blocks_issues: List[str] = Field(
        default_factory=list, description="Issue keys this blocks"
    )
    blocked_by_issues: List[str] = Field(
        default_factory=list, description="Issue keys blocking this"
    )

    # Additional metadata
    labels: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    fix_versions: List[str] = Field(default_factory=list)

    # Raw data reference
    raw_data: Optional[Dict[str, Any]] = Field(
        None, description="Original Jira JSON for debugging"
    )

    @validator("status_transitions", pre=True, each_item=False)
    def sort_transitions(cls, v):
        """Ensure transitions are sorted chronologically."""
        if v:
            return sorted(
                v,
                key=lambda x: (
                    x.transitioned_at
                    if isinstance(x, StatusTransition)
                    else x["transitioned_at"]
                ),
            )
        return v

    @property
    def lead_time_hours(self) -> Optional[float]:
        """Calculate lead time from creation to resolution."""
        if self.resolved_at:
            return (self.resolved_at - self.created_at).total_seconds() / 3600
        return None

    @property
    def cycle_time_hours(self) -> Optional[float]:
        """Calculate cycle time from first 'In Progress' to resolution."""
        if not self.resolved_at or not self.status_transitions:
            return None

        first_in_progress = None
        for transition in self.status_transitions:
            if "progress" in transition.to_status.lower():
                first_in_progress = transition.transitioned_at
                break

        if first_in_progress:
            return (self.resolved_at - first_in_progress).total_seconds() / 3600
        return None


class Sprint(BaseModel):
    """Represents a sprint/iteration."""

    id: str
    name: str
    team: str
    art: Optional[str] = None

    state: str = Field(..., description="active, closed, future")
    start_date: datetime
    end_date: datetime
    complete_date: Optional[datetime] = None

    # Sprint goals
    goal: Optional[str] = None

    # Issues
    committed_issues: List[str] = Field(
        default_factory=list, description="Issue keys committed at start"
    )
    completed_issues: List[str] = Field(
        default_factory=list, description="Issue keys completed"
    )
    incomplete_issues: List[str] = Field(
        default_factory=list, description="Issue keys not completed"
    )
    added_after_start: List[str] = Field(
        default_factory=list, description="Scope additions"
    )
    removed_issues: List[str] = Field(
        default_factory=list, description="Scope removals"
    )

    @property
    def commitment_reliability(self) -> Optional[float]:
        """Calculate percentage of committed items completed."""
        if not self.committed_issues:
            return None
        completed_committed = len(
            set(self.completed_issues) & set(self.committed_issues)
        )
        return completed_committed / len(self.committed_issues)

    @property
    def scope_change_rate(self) -> Optional[float]:
        """Calculate percentage of scope change."""
        if not self.committed_issues:
            return None
        changes = len(self.added_after_start) + len(self.removed_issues)
        return changes / len(self.committed_issues)


class ProgramIncrement(BaseModel):
    """Represents a Program Increment (PI) in SAFe."""

    id: str
    name: str
    art: str

    start_date: datetime
    end_date: datetime

    # PI objectives
    objectives: List[str] = Field(default_factory=list)

    # Features and enablers
    planned_features: List[str] = Field(
        default_factory=list, description="Feature keys planned"
    )
    delivered_features: List[str] = Field(
        default_factory=list, description="Feature keys delivered"
    )

    # Sprints in this PI
    sprint_ids: List[str] = Field(default_factory=list)

    @property
    def predictability_score(self) -> Optional[float]:
        """Calculate PI predictability (planned vs delivered)."""
        if not self.planned_features:
            return None
        delivered_planned = len(
            set(self.delivered_features) & set(self.planned_features)
        )
        return delivered_planned / len(self.planned_features)


class Team(BaseModel):
    """Represents an Agile team."""

    id: str
    name: str
    art: Optional[str] = None

    # Team composition
    members: List[str] = Field(default_factory=list, description="Team member user IDs")
    capacity_points_per_sprint: Optional[float] = None

    # Configuration
    board_id: Optional[str] = None
    jira_project_key: Optional[str] = None


class ART(BaseModel):
    """Represents an Agile Release Train."""

    id: str
    name: str

    # Teams in this ART
    team_ids: List[str] = Field(default_factory=list)

    # Current PI
    current_pi_id: Optional[str] = None

    # Configuration
    pi_duration_weeks: int = Field(default=10, description="Typical PI length")
    sprint_duration_weeks: int = Field(default=2, description="Typical sprint length")


class Portfolio(BaseModel):
    """Represents a portfolio of ARTs."""

    id: str
    name: str

    # ARTs in this portfolio
    art_ids: List[str] = Field(default_factory=list)

    # Strategic themes
    strategic_themes: List[str] = Field(default_factory=list)
