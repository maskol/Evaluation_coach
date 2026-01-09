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

    def __init__(self):
        self._cancel_requested = False

    def cancel(self):
        """Request cancellation of ongoing insight generation"""
        self._cancel_requested = True
        print("🛑 Insights generation cancellation requested")

    def reset_cancel(self):
        """Reset cancel flag for new generation"""
        self._cancel_requested = False

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

    def _generate_littles_law_insight(
        self,
        pi: str,
        flow_data: List[dict],
        pi_duration_days: int = 84,
    ) -> Optional[dict]:
        """Generate Little's Law analysis insight for a specific PI

        Little's Law: L = λ × W
        Where:
        - L = Average WIP (Work in Progress)
        - λ = Throughput (features completed per day)
        - W = Average Lead Time (days per feature)

        Args:
            pi: Program Increment identifier (e.g., "21Q4")
            flow_data: List of features from flow_leadtime API
            pi_duration_days: Duration of PI in days (default 84 for 6 weeks)

        Returns:
            Insight dictionary or None if insufficient data
        """
        if not flow_data:
            return None

        # Filter completed features for the PI
        completed_features = [
            f
            for f in flow_data
            if f.get("status") in ["Done", "Deployed"]
            and f.get("total_leadtime", 0) > 0
        ]

        if len(completed_features) < 5:  # Need minimum data for meaningful analysis
            return None

        # Calculate metrics
        total_features = len(completed_features)

        # W: Average Lead Time (days)
        lead_times = [f["total_leadtime"] for f in completed_features]
        avg_leadtime = sum(lead_times) / len(lead_times)

        # λ: Throughput (features per day)
        throughput_per_day = total_features / pi_duration_days

        # L: Predicted WIP using Little's Law
        predicted_wip = throughput_per_day * avg_leadtime

        # Calculate actual average WIP (if we have in_progress data)
        # This is approximate based on the total time items spent in progress
        in_progress_times = [
            f.get("in_progress", 0) + f.get("in_analysis", 0) + f.get("in_reviewing", 0)
            for f in completed_features
        ]
        avg_active_time = (
            sum(in_progress_times) / len(in_progress_times)
            if in_progress_times
            else avg_leadtime
        )

        # Estimated actual WIP
        actual_wip = throughput_per_day * avg_active_time

        # Calculate efficiency metrics
        flow_efficiency = (
            (avg_active_time / avg_leadtime * 100) if avg_leadtime > 0 else 0
        )
        wait_time = avg_leadtime - avg_active_time

        # Determine severity based on lead time and flow efficiency
        if avg_leadtime > 60 or flow_efficiency < 30:
            severity = "critical"
        elif avg_leadtime > 45 or flow_efficiency < 40:
            severity = "warning"
        elif avg_leadtime > 30 or flow_efficiency < 50:
            severity = "info"
        else:
            severity = "success"

        # Generate insights based on Little's Law analysis
        observation_parts = [
            f"PI {pi} analysis using Little's Law (L = λ × W):",
            f"{total_features} features completed in {pi_duration_days} days.",
            f"Throughput (λ) = {throughput_per_day:.2f} features/day.",
            f"Average Lead Time (W) = {avg_leadtime:.1f} days.",
            f"Predicted WIP (L) = {predicted_wip:.1f} features.",
            f"Flow Efficiency = {flow_efficiency:.1f}% (active time / total lead time).",
        ]

        interpretation_parts = []

        if flow_efficiency < 40:
            interpretation_parts.append(
                f"Low flow efficiency ({flow_efficiency:.1f}%) indicates features spend {wait_time:.1f} days waiting "
                f"vs {avg_active_time:.1f} days in active work. This suggests significant waste in the system."
            )
        elif flow_efficiency < 60:
            interpretation_parts.append(
                f"Moderate flow efficiency ({flow_efficiency:.1f}%) shows room for improvement. "
                f"Features wait {wait_time:.1f} days on average."
            )
        else:
            interpretation_parts.append(
                f"Good flow efficiency ({flow_efficiency:.1f}%) indicates smooth flow with minimal waiting."
            )

        if avg_leadtime > 45:
            interpretation_parts.append(
                f"Average lead time of {avg_leadtime:.1f} days exceeds healthy targets (30-45 days). "
                f"To reduce lead time while maintaining throughput, focus on reducing WIP."
            )

        # Calculate optimal WIP for target lead time of 30 days
        target_leadtime = 30
        optimal_wip = throughput_per_day * target_leadtime
        wip_reduction = predicted_wip - optimal_wip

        if wip_reduction > 2:
            interpretation_parts.append(
                f"To achieve 30-day lead time, reduce WIP from {predicted_wip:.1f} to {optimal_wip:.1f} features "
                f"(reduction of {wip_reduction:.1f} features)."
            )

        # Root causes
        root_causes = []

        if flow_efficiency < 50:
            root_causes.append(
                {
                    "description": f"High wait time ({wait_time:.1f} days) indicates bottlenecks or blocked work",
                    "evidence": [f"flow_efficiency_{flow_efficiency:.0f}pct"],
                    "confidence": 90.0,
                    "reference": "littles_law_analysis",
                }
            )

        if predicted_wip > 10:
            root_causes.append(
                {
                    "description": "Excessive WIP leads to context switching and delayed flow",
                    "evidence": [f"predicted_wip_{predicted_wip:.1f}"],
                    "confidence": 85.0,
                    "reference": "littles_law_analysis",
                }
            )

        # Recommended actions
        actions = []

        if predicted_wip > optimal_wip:
            actions.append(
                {
                    "timeframe": "short-term",
                    "description": f"Implement WIP limits: cap active features at {optimal_wip:.0f} per team",
                    "owner": "Scrum Masters & Product Owner",
                    "effort": "Low",
                    "dependencies": [],
                    "success_signal": f"WIP reduced to {optimal_wip:.0f}, lead time trending toward 30 days",
                }
            )

        if flow_efficiency < 50:
            actions.append(
                {
                    "timeframe": "medium-term",
                    "description": "Identify and eliminate sources of wait time (dependencies, blockers, handoffs)",
                    "owner": "ART Leadership",
                    "effort": "Medium",
                    "dependencies": ["Value stream mapping session"],
                    "success_signal": "Flow efficiency improves to >50% within 2 PIs",
                }
            )

        actions.append(
            {
                "timeframe": "ongoing",
                "description": f"Monitor Little's Law metrics weekly: maintain λ={throughput_per_day:.2f}/day, reduce W to 30 days",
                "owner": "RTE",
                "effort": "Low",
                "dependencies": ["Lead time tracking dashboard"],
                "success_signal": f"Consistent delivery of L={optimal_wip:.0f} features with W=30 days",
            }
        )

        return {
            "title": f"Little's Law Analysis for PI {pi}",
            "severity": severity,
            "confidence": 88.0,
            "scope": "pi",
            "scope_id": pi,
            "observation": " ".join(observation_parts),
            "interpretation": " ".join(interpretation_parts),
            "root_causes": (
                root_causes
                if root_causes
                else [
                    {
                        "description": "System dynamics analysis using Little's Law",
                        "evidence": ["flow_leadtime_data"],
                        "confidence": 88.0,
                        "reference": "littles_law_formula",
                    }
                ]
            ),
            "recommended_actions": actions,
            "expected_outcomes": {
                "metrics_to_watch": [
                    "Average Lead Time",
                    "Throughput",
                    "WIP",
                    "Flow Efficiency",
                ],
                "leading_indicators": [
                    "Daily WIP count",
                    "Features started vs completed",
                    "Time in blocked status",
                ],
                "lagging_indicators": [
                    "Average lead time trend",
                    "Throughput stability",
                ],
                "timeline": "2-3 PIs to reach optimal flow",
                "risks": [
                    "Reduced WIP may initially slow starts",
                    "Team resistance to limiting work",
                ],
            },
            "metric_references": ["lead_time", "throughput", "wip", "flow_efficiency"],
            "evidence": [f"pi_{pi}_flow_data", "littles_law_calculation"],
        }

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

        # Reset cancel flag at start of new generation
        self.reset_cancel()

        # Check for cancellation
        if self._cancel_requested:
            print("🛑 Insights generation cancelled by user")
            return []

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

        # Add Little's Law insight if PI is specified and leadtime service is available
        if scope_id and (scope == "pi" or scope == "portfolio"):
            try:
                from services.leadtime_service import LeadTimeService

                leadtime_service = LeadTimeService()

                if leadtime_service.is_available():
                    # Determine PI to analyze
                    pi_to_analyze = scope_id if scope == "pi" else None

                    # If no specific PI, try to get the most recent one
                    if not pi_to_analyze:
                        try:
                            filters = leadtime_service.client.get_available_filters()
                            available_pis = filters.get("pis", [])
                            if available_pis:
                                # Sort PIs and get most recent (assumes format like "21Q4", "22Q1")
                                pi_to_analyze = sorted(available_pis, reverse=True)[0]
                        except Exception as e:
                            print(f"⚠️ Could not fetch available PIs: {e}")

                    if pi_to_analyze:
                        print(
                            f"📊 Generating Little's Law insight for PI {pi_to_analyze}..."
                        )
                        try:
                            # Fetch flow_leadtime data for the PI
                            flow_data = leadtime_service.client.get_flow_leadtime(
                                pi=pi_to_analyze,
                                limit=10000,  # Get all features for the PI
                            )

                            if flow_data:
                                littles_law_insight = (
                                    self._generate_littles_law_insight(
                                        pi=pi_to_analyze,
                                        flow_data=flow_data,
                                        pi_duration_days=84,  # Standard 6-week PI
                                    )
                                )

                                if littles_law_insight:
                                    insights_data.append(littles_law_insight)
                                    print(
                                        f"✅ Generated Little's Law insight for PI {pi_to_analyze}"
                                    )
                                else:
                                    print(
                                        f"⚠️ Insufficient data for Little's Law analysis"
                                    )
                            else:
                                print(
                                    f"⚠️ No flow data available for PI {pi_to_analyze}"
                                )

                        except Exception as e:
                            print(f"⚠️ Error generating Little's Law insight: {e}")
                else:
                    print("⚠️ Lead-time service not available for Little's Law analysis")

            except Exception as e:
                print(f"⚠️ Could not initialize lead-time service: {e}")

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
