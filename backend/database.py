"""
Database configuration and models for Evaluation Coach
Uses SQLite with SQLAlchemy ORM
"""

import os
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./evaluation_coach.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class JiraIssue(Base):
    """Stores Jira issue data for analysis"""

    __tablename__ = "jira_issues"

    id = Column(Integer, primary_key=True, index=True)
    issue_key = Column(String, unique=True, index=True, nullable=False)
    issue_type = Column(String)
    summary = Column(String)
    description = Column(String)
    status = Column(String, index=True)
    priority = Column(String)
    assignee = Column(String, index=True)
    reporter = Column(String)
    team = Column(String, index=True)
    art = Column(String, index=True)
    portfolio = Column(String, index=True)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)
    resolved_date = Column(DateTime)
    story_points = Column(Float)
    original_estimate = Column(Float)
    sprint = Column(String)
    epic = Column(String)
    epic_link = Column(String)
    parent_key = Column(String)
    labels = Column(JSON)
    components = Column(JSON)
    custom_fields = Column(JSON)

    # Relationships
    transitions = relationship("IssueTransition", back_populates="issue")
    metrics = relationship("MetricCalculation", back_populates="issue")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class IssueTransition(Base):
    """Stores status transition history for flow metrics"""

    __tablename__ = "issue_transitions"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("jira_issues.id"))
    from_status = Column(String)
    to_status = Column(String, index=True)
    transition_date = Column(DateTime)
    author = Column(String)

    issue = relationship("JiraIssue", back_populates="transitions")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MetricCalculation(Base):
    """Stores calculated metrics for caching and trending"""

    __tablename__ = "metric_calculations"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, index=True, nullable=False)
    metric_value = Column(Float)
    metric_data = Column(JSON)
    scope = Column(String, index=True)
    scope_id = Column(String, index=True)
    time_period_start = Column(DateTime)
    time_period_end = Column(DateTime)
    issue_id = Column(Integer, ForeignKey("jira_issues.id"), nullable=True)

    issue = relationship("JiraIssue", back_populates="metrics")

    calculated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Insight(Base):
    """Stores generated coaching insights"""

    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, index=True)
    confidence = Column(Float)
    scope = Column(String, index=True)
    scope_id = Column(String, index=True)

    # 5-part insight structure
    observation = Column(Text)
    interpretation = Column(Text)
    root_causes = Column(JSON)
    recommended_actions = Column(JSON)
    expected_outcomes = Column(JSON)

    # Metadata
    metric_references = Column(JSON)
    evidence = Column(JSON)

    status = Column(String, default="active")
    user_feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Scorecard(Base):
    """Stores health scorecards"""

    __tablename__ = "scorecards"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, index=True, nullable=False)
    scope_id = Column(String, index=True)
    time_period_start = Column(DateTime)
    time_period_end = Column(DateTime)

    overall_score = Column(Float)
    dimension_scores = Column(JSON)
    metric_values = Column(JSON)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatMessage(Base):
    """Stores chat conversation history"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)
    content = Column(Text)
    context = Column(JSON)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class KnowledgeDocument(Base):
    """Stores RAG knowledge base documents"""

    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, unique=True, index=True)
    title = Column(String)
    category = Column(String, index=True)
    content = Column(Text)

    # Metadata for filtering
    tags = Column(JSON)
    applicability_scope = Column(JSON)
    applicability_metrics = Column(JSON)
    related_patterns = Column(JSON)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class RuntimeConfiguration(Base):
    """Stores runtime configuration settings that persist across restarts"""

    __tablename__ = "runtime_configuration"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, index=True, nullable=False)
    config_value = Column(Float, nullable=True)
    config_type = Column(String, default="float")  # float, string, int, bool, json

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class StrategicTarget(Base):
    """Stores strategic targets for metrics (2026, 2027, True North)"""

    __tablename__ = "strategic_targets"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, unique=True, index=True, nullable=False)
    target_2026 = Column(Float, nullable=True)
    target_2027 = Column(Float, nullable=True)
    true_north = Column(Float, nullable=True)
    unit = Column(String, nullable=True)  # e.g., "days", "%", "count"

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Database initialization
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Run initialization if called directly
if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DATABASE_URL)
