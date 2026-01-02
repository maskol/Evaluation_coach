"""
Insights generation service
Analyzes metrics and generates actionable coaching insights
"""

from datetime import datetime
from typing import List, Optional

from api_models import (
    Action,
    ExpectedOutcome,
    InsightResponse,
    RootCause,
    ScopeType,
    TimeRange,
)
from sqlalchemy.orm import Session


class InsightsService:
    """Service for generating coaching insights"""

    async def generate_insights(
        self,
        scope: ScopeType,
        scope_id: Optional[str],
        time_range: TimeRange,
        db: Session,
    ) -> List[InsightResponse]:
        """
        Generate actionable insights based on metric analysis

        Args:
            scope: Analysis scope
            scope_id: Specific ART or team ID
            time_range: Time period for analysis
            db: Database session

        Returns:
            List of generated insights
        """

        # TODO: Implement actual insight generation using LLM + metrics
        # For now, create sample insights and save to database

        insights_data = [
            {
                "title": "High WIP Across Multiple Teams",
                "severity": "critical",
                "confidence": 92.0,
                "scope": "art",
                "scope_id": "customer_experience",
                "observation": "Customer Experience ART shows WIP ratio of 2.3 (vs target 1.5), affecting 3 teams with combined 43 active stories against 18 person capacity.",
                "interpretation": "Excessive WIP leads to context switching, reduced flow efficiency, and delayed delivery. Teams are attempting too much concurrent work.",
                "root_causes": [
                    {
                        "description": "Scattered focus due to external dependencies",
                        "evidence": ["JIRA-123", "JIRA-456"],
                        "confidence": 85.0,
                        "reference": "dependency_analysis_report",
                    },
                    {
                        "description": "Lack of WIP limits enforcement in sprint planning",
                        "evidence": ["sprint_retrospectives"],
                        "confidence": 90.0,
                        "reference": None,
                    },
                ],
                "recommended_actions": [
                    {
                        "timeframe": "short-term",
                        "description": "Implement hard WIP limits (1.5x team size) in next sprint planning",
                        "owner": "Scrum Masters",
                        "effort": "Low",
                        "dependencies": [],
                        "success_signal": "WIP ratio drops below 1.5 within 2 sprints",
                    },
                    {
                        "timeframe": "medium-term",
                        "description": "Review and reduce external dependencies with dependency mapping",
                        "owner": "ART Leadership",
                        "effort": "Medium",
                        "dependencies": ["Architecture review"],
                        "success_signal": "25% reduction in blocked time",
                    },
                ],
                "expected_outcomes": {
                    "metrics_to_watch": ["WIP ratio", "Flow efficiency", "Lead time"],
                    "leading_indicators": [
                        "Number of stories in progress",
                        "Daily blocked time",
                    ],
                    "lagging_indicators": ["Throughput", "PI predictability"],
                    "timeline": "2-3 sprints",
                    "risks": [
                        "Initial productivity dip as teams adjust",
                        "Resistance to change",
                    ],
                },
                "metric_references": ["wip_ratio", "flow_efficiency"],
                "evidence": ["JIRA-123", "JIRA-456", "JIRA-789"],
            },
            {
                "title": "Increasing Defect Escape Rate",
                "severity": "warning",
                "confidence": 87.0,
                "scope": "team",
                "scope_id": "mobile_apps",
                "observation": "Mobile Apps team shows 7.2% defect escape rate (vs target 5%), with 12 production defects found in last sprint from 167 delivered stories.",
                "interpretation": "Quality issues are reaching production, indicating gaps in testing coverage or test effectiveness.",
                "root_causes": [
                    {
                        "description": "68% of escaped defects lack automated test coverage",
                        "evidence": ["test_coverage_report"],
                        "confidence": 95.0,
                        "reference": "quality_audit_2025",
                    }
                ],
                "recommended_actions": [
                    {
                        "timeframe": "short-term",
                        "description": "Add Definition of Done checklist requiring test coverage review",
                        "owner": "Team Lead",
                        "effort": "Low",
                        "dependencies": [],
                        "success_signal": "100% stories reviewed for coverage before Done",
                    }
                ],
                "expected_outcomes": {
                    "metrics_to_watch": ["Defect escape rate", "Test coverage"],
                    "leading_indicators": ["Stories with >80% coverage"],
                    "lagging_indicators": ["Production defects"],
                    "timeline": "1-2 months",
                    "risks": ["Extended story completion time"],
                },
                "metric_references": ["defect_escape_rate", "test_coverage"],
                "evidence": ["PROD-001", "PROD-002"],
            },
            {
                "title": "Excellent Flow Efficiency Improvement",
                "severity": "success",
                "confidence": 95.0,
                "scope": "art",
                "scope_id": "platform_engineering",
                "observation": "Platform Engineering ART achieved 72% flow efficiency (up from 64%), with 28% reduction in blocked time over last 2 PIs.",
                "interpretation": "Significant improvement in flow efficiency indicates successful implementation of lean practices and effective dependency management.",
                "root_causes": [
                    {
                        "description": "Proactive dependency management and cross-team collaboration",
                        "evidence": ["sync_meeting_notes"],
                        "confidence": 90.0,
                        "reference": "dependency_board",
                    }
                ],
                "recommended_actions": [
                    {
                        "timeframe": "short-term",
                        "description": "Document and share best practices with other ARTs",
                        "owner": "RTE",
                        "effort": "Low",
                        "dependencies": [],
                        "success_signal": "Best practices adopted by 2+ other ARTs",
                    }
                ],
                "expected_outcomes": {
                    "metrics_to_watch": ["Flow efficiency", "Blocked time"],
                    "leading_indicators": ["Dependency resolution time"],
                    "lagging_indicators": ["Throughput"],
                    "timeline": "Sustained",
                    "risks": ["Complacency leading to regression"],
                },
                "metric_references": ["flow_efficiency", "blocked_time"],
                "evidence": ["PI_metrics_Q4"],
            },
        ]

        # Save insights to database
        from database import Insight

        saved_insights = []

        for insight_data in insights_data:
            insight = Insight(
                title=insight_data["title"],
                severity=insight_data["severity"],
                confidence=insight_data["confidence"],
                scope=insight_data["scope"],
                scope_id=insight_data["scope_id"],
                observation=insight_data["observation"],
                interpretation=insight_data["interpretation"],
                root_causes=insight_data["root_causes"],
                recommended_actions=insight_data["recommended_actions"],
                expected_outcomes=insight_data["expected_outcomes"],
                metric_references=insight_data["metric_references"],
                evidence=insight_data["evidence"],
                status="active",
            )
            db.add(insight)
            db.commit()
            db.refresh(insight)

            # Convert to response model
            saved_insights.append(
                InsightResponse(
                    id=insight.id,
                    title=insight.title,
                    severity=insight.severity,
                    confidence=insight.confidence,
                    scope=insight.scope,
                    scope_id=insight.scope_id,
                    observation=insight.observation,
                    interpretation=insight.interpretation,
                    root_causes=[RootCause(**rc) for rc in insight.root_causes],
                    recommended_actions=[
                        Action(**a) for a in insight.recommended_actions
                    ],
                    expected_outcomes=ExpectedOutcome(**insight.expected_outcomes),
                    metric_references=insight.metric_references,
                    evidence=insight.evidence,
                    status=insight.status,
                    created_at=insight.created_at,
                )
            )

        return saved_insights

        return saved_insights
