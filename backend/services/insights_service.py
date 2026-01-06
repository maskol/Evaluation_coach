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
from config.settings import Settings


class InsightsService:
    """Service for generating coaching insights"""

    def _generate_strategic_target_insights(
        self,
        settings: Settings,
        current_leadtime: Optional[float] = None,
        current_planning_accuracy: Optional[float] = None,
    ) -> List[dict]:
        """Generate insights comparing current metrics against strategic targets

        Args:
            settings: Application settings containing targets
            current_leadtime: Actual current feature lead-time in days (if available)
            current_planning_accuracy: Actual current planning accuracy % (if available)
        """
        insights = []

        # Feature Lead-Time Target Insight
        if settings.leadtime_target_2026:
            # Use provided current lead-time or fallback to example value
            if current_leadtime is None:
                current_leadtime = 47.0  # Example fallback value

            target_2026 = settings.leadtime_target_2026
            target_2027 = settings.leadtime_target_2027
            target_true_north = settings.leadtime_target_true_north

            # Determine severity based on 2026 target
            gap_2026 = current_leadtime - target_2026
            if gap_2026 > 15:
                severity = "critical"
            elif gap_2026 > 5:
                severity = "warning"
            elif gap_2026 > 0:
                severity = "info"
            else:
                severity = "success"

            observation_parts = [
                f"Current average Feature lead-time is {current_leadtime:.1f} days."
            ]
            interpretation_parts = []

            if target_2026:
                observation_parts.append(
                    f"2026 target: {target_2026:.1f} days (gap: {gap_2026:+.1f} days)."
                )
                if gap_2026 > 0:
                    interpretation_parts.append(
                        f"Need to reduce lead-time by {gap_2026:.1f} days ({gap_2026/current_leadtime*100:.1f}%) to meet 2026 target."
                    )
                else:
                    interpretation_parts.append(
                        f"Currently {abs(gap_2026):.1f} days ahead of 2026 target - excellent progress!"
                    )

            if target_2027:
                gap_2027 = current_leadtime - target_2027
                observation_parts.append(
                    f"2027 target: {target_2027:.1f} days (gap: {gap_2027:+.1f} days)."
                )
                if gap_2027 > 0:
                    interpretation_parts.append(
                        f"2027 target requires additional {gap_2027:.1f} days reduction."
                    )

            if target_true_north:
                gap_true_north = current_leadtime - target_true_north
                observation_parts.append(
                    f"True North: {target_true_north:.1f} days (gap: {gap_true_north:+.1f} days)."
                )
                if gap_true_north > 0:
                    interpretation_parts.append(
                        f"True North vision requires {gap_true_north/current_leadtime*100:.1f}% total reduction."
                    )

            insights.append(
                {
                    "title": "Feature Lead-Time vs Strategic Targets",
                    "severity": severity,
                    "confidence": 95.0,
                    "scope": "portfolio",
                    "scope_id": "strategic_targets",
                    "observation": " ".join(observation_parts),
                    "interpretation": " ".join(interpretation_parts),
                    "root_causes": [
                        {
                            "description": "Baseline measurement for strategic goal tracking",
                            "evidence": ["current_metrics"],
                            "confidence": 95.0,
                            "reference": "strategic_targets_config",
                        }
                    ],
                    "recommended_actions": [
                        {
                            "timeframe": "short-term",
                            "description": "Analyze bottlenecks in current flow to identify improvement opportunities",
                            "owner": "Process Improvement Team",
                            "effort": "Medium",
                            "dependencies": [
                                "Bottleneck analysis",
                                "Flow metrics review",
                            ],
                            "success_signal": "Identified top 3 bottlenecks affecting lead-time",
                        },
                        {
                            "timeframe": "medium-term",
                            "description": "Implement incremental improvements targeting 2026 goals",
                            "owner": "ART Leadership",
                            "effort": "High",
                            "dependencies": ["Resource allocation", "Team training"],
                            "success_signal": f"Lead-time reduced to {target_2026:.1f} days by end of 2026",
                        },
                    ],
                    "expected_outcomes": {
                        "metrics_to_watch": [
                            "Feature lead-time",
                            "Flow efficiency",
                            "Cycle time",
                        ],
                        "leading_indicators": [
                            "Bottleneck reduction",
                            "WIP limits adherence",
                        ],
                        "lagging_indicators": ["Average lead-time trend"],
                        "timeline": "12-24 months for 2026 target",
                        "risks": ["Organizational resistance", "Resource constraints"],
                    },
                    "metric_references": ["feature_leadtime"],
                    "evidence": ["strategic_targets"],
                }
            )

        # Planning Accuracy Target Insight
        if settings.planning_accuracy_target_2026:
            # Use provided current accuracy or fallback to example value
            if current_planning_accuracy is None:
                current_accuracy = 72.0  # Example fallback value
            else:
                current_accuracy = current_planning_accuracy

            target_2026 = settings.planning_accuracy_target_2026
            target_2027 = settings.planning_accuracy_target_2027
            target_true_north = settings.planning_accuracy_target_true_north

            # Determine severity based on 2026 target
            gap_2026 = target_2026 - current_accuracy
            if gap_2026 > 15:
                severity = "critical"
            elif gap_2026 > 5:
                severity = "warning"
            elif gap_2026 > 0:
                severity = "info"
            else:
                severity = "success"

            observation_parts = [
                f"Current Planning Accuracy is {current_accuracy:.1f}%."
            ]
            interpretation_parts = []

            if target_2026:
                observation_parts.append(
                    f"2026 target: {target_2026:.1f}% (gap: {gap_2026:+.1f}%)."
                )
                if gap_2026 > 0:
                    interpretation_parts.append(
                        f"Need to improve accuracy by {gap_2026:.1f} percentage points to meet 2026 target."
                    )
                else:
                    interpretation_parts.append(
                        f"Currently {abs(gap_2026):.1f}% ahead of 2026 target - excellent predictability!"
                    )

            if target_2027:
                gap_2027 = target_2027 - current_accuracy
                observation_parts.append(
                    f"2027 target: {target_2027:.1f}% (gap: {gap_2027:+.1f}%)."
                )
                if gap_2027 > 0:
                    interpretation_parts.append(
                        f"2027 target requires additional {gap_2027:.1f}% improvement."
                    )

            if target_true_north:
                gap_true_north = target_true_north - current_accuracy
                observation_parts.append(
                    f"True North: {target_true_north:.1f}% (gap: {gap_true_north:+.1f}%)."
                )
                if gap_true_north > 0:
                    interpretation_parts.append(
                        f"True North vision requires reaching world-class predictability levels."
                    )

            insights.append(
                {
                    "title": "Planning Accuracy vs Strategic Targets",
                    "severity": severity,
                    "confidence": 95.0,
                    "scope": "portfolio",
                    "scope_id": "strategic_targets",
                    "observation": " ".join(observation_parts),
                    "interpretation": " ".join(interpretation_parts),
                    "root_causes": [
                        {
                            "description": "Baseline measurement for strategic goal tracking",
                            "evidence": ["current_metrics"],
                            "confidence": 95.0,
                            "reference": "strategic_targets_config",
                        }
                    ],
                    "recommended_actions": [
                        {
                            "timeframe": "short-term",
                            "description": "Review historical planning patterns to identify accuracy gaps",
                            "owner": "Product Management",
                            "effort": "Low",
                            "dependencies": ["Historical PI data"],
                            "success_signal": "Identified common causes of planning misses",
                        },
                        {
                            "timeframe": "medium-term",
                            "description": "Implement capacity-based planning with velocity normalization",
                            "owner": "RTE & Scrum Masters",
                            "effort": "Medium",
                            "dependencies": [
                                "Team velocity data",
                                "Capacity planning tools",
                            ],
                            "success_signal": f"Planning accuracy improved to {target_2026:.1f}% by end of 2026",
                        },
                    ],
                    "expected_outcomes": {
                        "metrics_to_watch": [
                            "Planning accuracy",
                            "PI predictability",
                            "Velocity stability",
                        ],
                        "leading_indicators": [
                            "Sprint commitment accuracy",
                            "Velocity variance",
                        ],
                        "lagging_indicators": ["PI objectives achievement rate"],
                        "timeline": "6-12 months for 2026 target",
                        "risks": ["Underestimation pressure", "Scope creep"],
                    },
                    "metric_references": ["planning_accuracy"],
                    "evidence": ["strategic_targets"],
                }
            )

        return insights

    async def generate_insights(
        self,
        scope: ScopeType,
        scope_id: Optional[str],
        time_range: TimeRange,
        db: Session,
        current_leadtime: Optional[float] = None,
        current_planning_accuracy: Optional[float] = None,
    ) -> List[InsightResponse]:
        """
        Generate actionable insights based on metric analysis

        Args:
            scope: Analysis scope
            scope_id: Specific ART or team ID
            time_range: Time period for analysis
            db: Database session
            current_leadtime: Actual current feature lead-time (optional, for strategic targets)
            current_planning_accuracy: Actual current planning accuracy (optional, for strategic targets)

        Returns:
            List of generated insights
        """

        # Load strategic targets from settings
        settings = Settings()

        # TODO: Implement actual insight generation using LLM + metrics
        # For now, create sample insights and save to database
        # Strategic targets are now available for AI insight analysis

        insights_data = []

        # Add strategic target insights if targets are configured
        if settings.leadtime_target_2026 or settings.planning_accuracy_target_2026:
            target_insights = self._generate_strategic_target_insights(
                settings,
                current_leadtime=current_leadtime,
                current_planning_accuracy=current_planning_accuracy,
            )
            insights_data.extend(target_insights)

        # Add operational insights
        insights_data.extend(
            [
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
                        "metrics_to_watch": [
                            "WIP ratio",
                            "Flow efficiency",
                            "Lead time",
                        ],
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
        )

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
