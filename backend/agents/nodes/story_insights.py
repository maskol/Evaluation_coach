"""
Story-Level Insights Generator

Analyzes story-level delivery metrics to generate actionable insights.
Specifically designed for user story workflow with 8 stages vs 11 feature stages.

Story stages:
1. refinement
2. ready_for_development
3. in_development
4. in_review (unique to stories - code review)
5. ready_for_test
6. in_testing
7. ready_for_deployment
8. deployed

Based on the new DL Webb App story-level API endpoints.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from api_models import InsightResponse, RootCause, Action, ExpectedOutcome


def generate_story_insights(
    story_analysis_summary: Dict[str, Any],
    story_pip_data: List[Dict[str, Any]],
    story_waste_analysis: Dict[str, Any],
    selected_arts: Optional[List[str]] = None,
    selected_pis: Optional[List[str]] = None,
    selected_team: Optional[str] = None,
    llm_service=None,
) -> List[InsightResponse]:
    """
    Generate comprehensive insights from story-level analysis data

    Args:
        story_analysis_summary: Data from /api/story_analysis_summary endpoint
        story_pip_data: Data from /api/story_pip_data endpoint
        story_waste_analysis: Data from /api/story_waste_analysis endpoint
        selected_arts: Filtered ARTs (if any)
        selected_pis: Filtered PIs (if any)
        selected_team: Selected team name (if any)
        llm_service: LLM service for expert commentary (optional)

    Returns:
        List of detailed story-level insights with root causes and recommendations
    """
    insights = []

    # Extract analysis sections
    bottleneck = story_analysis_summary.get("bottleneck_analysis", {})
    waste = story_waste_analysis.get("waste_metrics", {})

    # 1. Story Bottleneck Analysis
    insights.extend(
        _analyze_story_bottlenecks(
            bottleneck, selected_arts, selected_pis, selected_team
        )
    )

    # 2. Story Stuck Item Pattern Analysis
    insights.extend(
        _analyze_story_stuck_items(
            bottleneck, selected_arts, selected_pis, selected_team
        )
    )

    # 3. Story WIP Analysis
    insights.extend(
        _analyze_story_wip(bottleneck, selected_arts, selected_pis, selected_team)
    )

    # 4. Story Planning Accuracy
    insights.extend(
        _analyze_story_planning(
            story_pip_data, selected_arts, selected_pis, selected_team
        )
    )

    # 5. Story Waste Analysis
    insights.extend(
        _analyze_story_waste(waste, selected_arts, selected_pis, selected_team)
    )

    # 6. Code Review Insights (unique to stories)
    insights.extend(
        _analyze_code_review(bottleneck, selected_arts, selected_pis, selected_team)
    )

    return insights


def _format_scope(
    arts: Optional[List[str]], pis: Optional[List[str]], team: Optional[str]
) -> str:
    """Format scope description from filters"""
    parts = []
    if team:
        parts.append(f"Team: {team}")
    elif arts:
        parts.append(f"ART: {', '.join(arts)}")
    if pis:
        parts.append(f"PI: {', '.join(pis)}")
    return " | ".join(parts) if parts else "Portfolio"


def _analyze_story_bottlenecks(
    bottleneck_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
    selected_team: Optional[str] = None,
) -> List[InsightResponse]:
    """Analyze story workflow bottlenecks and generate insights"""
    insights = []

    stage_analysis = bottleneck_data.get("stage_analysis", {})
    if not stage_analysis:
        return insights

    # Calculate bottleneck scores for each stage
    stage_scores = []
    for stage_name, stage_data in stage_analysis.items():
        mean_time = float(stage_data.get("mean_time", 0) or 0)
        max_time = float(stage_data.get("max_time", 0) or 0)
        items_exceeding = int(stage_data.get("items_exceeding_threshold", 0) or 0)

        if mean_time > 0:
            # Simple bottleneck score: (mean_time / expected_time) * 100
            # Expected times for stories (in days): development=5, testing=3, review=1, etc.
            expected_times = {
                "refinement": 2,
                "ready_for_development": 1,
                "in_development": 5,
                "in_review": 1,
                "ready_for_test": 0.5,
                "in_testing": 3,
                "ready_for_deployment": 0.5,
                "deployed": 0,
            }
            expected = expected_times.get(stage_name, 2)
            score = (mean_time / expected) * 100 if expected > 0 else mean_time * 10

            stage_scores.append(
                {
                    "stage": stage_name,
                    "score": score,
                    "mean_time": mean_time,
                    "max_time": max_time,
                    "items_exceeding": items_exceeding,
                }
            )

    # Sort by score
    sorted_bottlenecks = sorted(stage_scores, key=lambda x: x["score"], reverse=True)

    # Top bottleneck
    if sorted_bottlenecks:
        top = sorted_bottlenecks[0]
        stage_name = top["stage"]
        score = top["score"]
        mean_time = top["mean_time"]
        max_time = top["max_time"]
        items_exceeding = top["items_exceeding"]

        if score > 100:  # Significant bottleneck (exceeding expected time)
            scope_desc = _format_scope(selected_arts, selected_pis, selected_team)

            # Get stuck stories for this stage
            stuck_items = bottleneck_data.get("stuck_items", [])

            # Filter by team if specified (critical for team view accuracy)
            if selected_team:
                stuck_items = [
                    item
                    for item in stuck_items
                    if item.get("development_team") == selected_team
                ]

            stage_stuck = [
                item for item in stuck_items if item.get("stage") == stage_name
            ][:3]

            stuck_evidence = []
            if stage_stuck:
                for item in stage_stuck:
                    issue_key = item.get("issue_key", "Unknown")
                    days = item.get("days_in_stage", 0)
                    stuck_evidence.append(
                        f"{issue_key}: {days:.1f} days in {stage_name}"
                    )

            insights.append(
                InsightResponse(
                    id=0,
                    title=f"Story Bottleneck in {stage_name.replace('_', ' ').title()} Stage",
                    severity="critical" if score > 200 else "warning",
                    confidence=0.9,
                    scope=scope_desc,
                    scope_id=None,
                    observation=f"The {stage_name.replace('_', ' ')} stage shows a bottleneck with average time of {mean_time:.1f} days (expected: ~{_get_expected_time(stage_name):.1f} days). {items_exceeding} stories exceeded threshold, with max duration of {max_time:.1f} days.",
                    interpretation=f"User stories are spending excessive time in {stage_name.replace('_', ' ')}. This stage is constraining story delivery velocity. Stories should move through this stage faster to maintain team flow and meet sprint commitments.",
                    root_causes=[
                        RootCause(
                            description=_get_stage_root_cause(stage_name),
                            evidence=(
                                stuck_evidence
                                if stuck_evidence
                                else [
                                    f"Mean time: {mean_time:.1f} days",
                                    f"Max time: {max_time:.1f} days",
                                    f"{items_exceeding} stories exceeding threshold",
                                ]
                            ),
                            confidence=0.85,
                            reference=f"Story {stage_name} metrics",
                        ),
                    ],
                    recommended_actions=_get_stage_actions(
                        stage_name, mean_time, items_exceeding
                    ),
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=[
                            f"story_{stage_name}_mean_time",
                            "story_lead_time",
                            "story_throughput",
                        ],
                        leading_indicators=[
                            f"Reduced time in {stage_name}",
                            "Fewer stuck stories",
                        ],
                        lagging_indicators=[
                            f"Mean time reduced to <{_get_expected_time(stage_name) * 1.5:.1f} days",
                            "Sprint predictability improved",
                        ],
                        timeline="2-4 weeks",
                        risks=[
                            "Team workload adjustments needed",
                            "Process changes require adoption time",
                        ],
                    ),
                    metric_references=[f"story_{stage_name}_metrics"],
                    evidence=[
                        f"Average time: {mean_time:.1f} days",
                        f"Expected: ~{_get_expected_time(stage_name):.1f} days",
                        f"{items_exceeding} stories over threshold",
                    ]
                    + (stuck_evidence[:2] if stuck_evidence else []),
                    status="active",
                    created_at=datetime.now(),
                )
            )

    return insights


def _analyze_story_stuck_items(
    bottleneck_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
    selected_team: Optional[str] = None,
) -> List[InsightResponse]:
    """Analyze stuck stories for patterns"""
    insights = []

    stuck_items = bottleneck_data.get("stuck_items", [])

    # Filter by team if specified (critical for team view accuracy)
    if selected_team:
        stuck_items = [
            item
            for item in stuck_items
            if item.get("development_team") == selected_team
        ]

    if len(stuck_items) < 3:
        return insights

    # Calculate total stuck time
    total_stuck_days = sum(item.get("days_in_stage", 0) for item in stuck_items)
    avg_stuck_days = total_stuck_days / len(stuck_items) if stuck_items else 0

    if avg_stuck_days > 10:  # Stories stuck for avg > 10 days is concerning
        scope_desc = _format_scope(selected_arts, selected_pis, selected_team)

        # Get worst offenders
        worst_stuck = sorted(
            stuck_items, key=lambda x: x.get("days_in_stage", 0), reverse=True
        )[:3]

        evidence = [
            f"{item.get('issue_key', 'Unknown')}: {item.get('days_in_stage', 0):.0f} days in {item.get('stage', 'unknown')}"
            for item in worst_stuck
        ]

        insights.append(
            InsightResponse(
                id=0,
                title=f"{len(stuck_items)} Stories Stuck in Workflow",
                severity="warning",
                confidence=0.85,
                scope=scope_desc,
                scope_id=None,
                observation=f"Found {len(stuck_items)} stories stuck in various stages with average stuck time of {avg_stuck_days:.1f} days. Total stuck time: {total_stuck_days:.0f} days.",
                interpretation="Stories stuck for extended periods indicate blockers, dependencies, or resource constraints. This affects sprint predictability and team velocity. Stuck stories should be addressed daily in standups.",
                root_causes=[
                    RootCause(
                        description="Blockers or dependencies not resolved quickly",
                        evidence=evidence,
                        confidence=0.8,
                        reference="Stuck story analysis",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description="Daily review of stuck stories in standup. Assign owner to each blocker and set resolution deadline.",
                        owner="scrum_master",
                        effort="15 min daily",
                        dependencies=[],
                        success_signal="All stuck stories reviewed daily, blockers tracked",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Implement blocker board visible to team. Use swarming technique - team members help unblock stuck stories.",
                        owner="team",
                        effort="1-2 weeks",
                        dependencies=["Team agreement"],
                        success_signal="50% reduction in average stuck time",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=["stuck_stories_count", "average_stuck_days"],
                    leading_indicators=["Blocker resolution time decreasing"],
                    lagging_indicators=["Average stuck time <5 days"],
                    timeline="2-3 weeks",
                    risks=["May reveal systemic dependency issues"],
                ),
                metric_references=["stuck_stories_metrics"],
                evidence=evidence,
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _analyze_story_wip(
    bottleneck_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
    selected_team: Optional[str] = None,
) -> List[InsightResponse]:
    """Analyze story WIP statistics"""
    insights = []

    wip_stats = bottleneck_data.get("wip_statistics", {})
    total_wip = wip_stats.get("total_active_stories", 0)

    # Get flow distribution
    flow_dist = bottleneck_data.get("flow_distribution", {})

    if total_wip > 0:
        # Calculate WIP ratio (WIP per stage)
        stage_analysis = bottleneck_data.get("stage_analysis", {})
        active_stages = ["in_development", "in_review", "in_testing"]

        wip_by_stage = {}
        for stage in active_stages:
            stage_data = stage_analysis.get(stage, {})
            count = flow_dist.get(stage, 0)
            if count > 0:
                wip_by_stage[stage] = count

        # Check if WIP is excessive
        # For a typical sprint team (5-8 people), healthy WIP is 5-12 stories total
        if total_wip > 15:
            scope_desc = _format_scope(selected_arts, selected_pis, selected_team)

            insights.append(
                InsightResponse(
                    id=0,
                    title=f"High Story WIP: {total_wip} Active Stories",
                    severity="warning",
                    confidence=0.8,
                    scope=scope_desc,
                    scope_id=None,
                    observation=f"Team has {total_wip} stories in progress across workflow stages: {', '.join([f'{k}: {v}' for k, v in wip_by_stage.items()])}. Recommended WIP for a team is 5-12 stories.",
                    interpretation="Excessive WIP leads to context switching, slower story completion, and reduced sprint predictability. Teams should focus on finishing stories rather than starting new ones.",
                    root_causes=[
                        RootCause(
                            description="Lack of WIP limits or pull system",
                            evidence=[
                                f"Total WIP: {total_wip}",
                                f"Recommended: 5-12 stories",
                            ],
                            confidence=0.85,
                            reference="WIP analysis",
                        ),
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description="Implement WIP limits per workflow stage. Suggested limits: Development=5, Review=3, Testing=4",
                            owner="scrum_master",
                            effort="1 sprint",
                            dependencies=["Team agreement"],
                            success_signal="WIP reduced to <12 stories",
                        ),
                        Action(
                            timeframe="short_term",
                            description="Adopt 'stop starting, start finishing' mindset. Prioritize completing stories over starting new ones.",
                            owner="team",
                            effort="Ongoing",
                            dependencies=["Team coaching"],
                            success_signal="Lead time per story decreases by 20%",
                        ),
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=["total_wip", "story_lead_time", "throughput"],
                        leading_indicators=[
                            "WIP count decreasing",
                            "Stories completed per day increasing",
                        ],
                        lagging_indicators=[
                            "Sprint predictability improved",
                            "Lead time reduced",
                        ],
                        timeline="2-3 sprints",
                        risks=["Initial velocity may appear to slow"],
                    ),
                    metric_references=["wip_metrics"],
                    evidence=[f"Total WIP: {total_wip}", "Exceeds healthy limit of 12"],
                    status="active",
                    created_at=datetime.now(),
                )
            )

    return insights


def _analyze_story_planning(
    pip_data: List[Dict[str, Any]],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
    selected_team: Optional[str] = None,
) -> List[InsightResponse]:
    """Analyze story planning accuracy"""
    insights = []

    if not pip_data:
        return insights

    # Aggregate metrics
    total_planned = sum(
        d.get("story_metrics", {}).get("planned_stories", 0) for d in pip_data
    )
    total_completed = sum(
        d.get("story_metrics", {}).get("completed_stories", 0) for d in pip_data
    )

    if total_planned > 0:
        completion_rate = (total_completed / total_planned) * 100

        if completion_rate < 70:  # Low story completion
            scope_desc = _format_scope(selected_arts, selected_pis, selected_team)

            insights.append(
                InsightResponse(
                    id=0,
                    title=f"Low Story Completion Rate: {completion_rate:.1f}%",
                    severity="warning" if completion_rate < 60 else "info",
                    confidence=0.85,
                    scope=scope_desc,
                    scope_id=None,
                    observation=f"Team planned {total_planned} stories but completed only {total_completed} ({completion_rate:.1f}%). Healthy teams complete 80-90% of planned stories.",
                    interpretation="Low story completion rate indicates over-commitment, underestimation, or unexpected impediments. This reduces sprint predictability and stakeholder trust.",
                    root_causes=[
                        RootCause(
                            description="Over-commitment in sprint planning",
                            evidence=[
                                f"Completion rate: {completion_rate:.1f}%",
                                "Target: 80-90%",
                            ],
                            confidence=0.8,
                            reference="Planning metrics",
                        ),
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description="Review sprint planning process. Use team velocity from last 3 sprints to guide commitment.",
                            owner="product_owner",
                            effort="1 sprint",
                            dependencies=[],
                            success_signal="Completion rate improves to >80%",
                        ),
                        Action(
                            timeframe="short_term",
                            description="Implement story sizing discipline. Break down large stories. Use Planning Poker for estimates.",
                            owner="team",
                            effort="Ongoing",
                            dependencies=["Estimation training"],
                            success_signal="More consistent story sizes, better estimates",
                        ),
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=["completion_rate", "velocity", "story_sizes"],
                        leading_indicators=[
                            "More accurate estimates",
                            "Smaller story sizes",
                        ],
                        lagging_indicators=[
                            "Completion rate >80%",
                            "Velocity stabilizes",
                        ],
                        timeline="2-3 sprints",
                        risks=[
                            "Initial velocity may appear lower with better planning"
                        ],
                    ),
                    metric_references=["planning_accuracy"],
                    evidence=[
                        f"Planned: {total_planned}",
                        f"Completed: {total_completed}",
                        f"Rate: {completion_rate:.1f}%",
                    ],
                    status="active",
                    created_at=datetime.now(),
                )
            )

    return insights


def _analyze_story_waste(
    waste_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
    selected_team: Optional[str] = None,
) -> List[InsightResponse]:
    """Analyze story-level waste"""
    insights = []

    blocked_stories = waste_data.get("blocked_stories", {})
    blocked_count = blocked_stories.get("count", 0)
    blocked_days = blocked_stories.get("total_blocked_days", 0)

    if blocked_count > 0:
        avg_blocked = blocked_days / blocked_count if blocked_count > 0 else 0

        if avg_blocked > 5:  # Average >5 days blocked is concerning
            scope_desc = _format_scope(selected_arts, selected_pis, selected_team)

            insights.append(
                InsightResponse(
                    id=0,
                    title=f"{blocked_count} Stories Blocked (Avg {avg_blocked:.1f} days)",
                    severity="warning",
                    confidence=0.85,
                    scope=scope_desc,
                    scope_id=None,
                    observation=f"{blocked_count} stories are blocked, totaling {blocked_days:.0f} blocked days. Average blocked time: {avg_blocked:.1f} days per story.",
                    interpretation="Blocked stories represent pure waste - no value is being delivered while stories wait. This impacts team velocity and sprint commitments.",
                    root_causes=[
                        RootCause(
                            description="External dependencies or impediments not resolved quickly",
                            evidence=[
                                f"{blocked_count} blocked stories",
                                f"{blocked_days:.0f} total blocked days",
                            ],
                            confidence=0.8,
                            reference="Waste analysis",
                        ),
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description="Identify all blockers and assign owners. Escalate blockers >3 days to management.",
                            owner="scrum_master",
                            effort="Daily",
                            dependencies=[],
                            success_signal="All blockers have owners and resolution dates",
                        ),
                        Action(
                            timeframe="short_term",
                            description="Implement dependency mapping in refinement. Identify dependencies before sprint starts.",
                            owner="product_owner",
                            effort="2 weeks",
                            dependencies=["Refinement process update"],
                            success_signal="50% reduction in blocked stories",
                        ),
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=["blocked_stories_count", "blocked_days"],
                        leading_indicators=["Faster blocker resolution"],
                        lagging_indicators=["<3 average blocked days per story"],
                        timeline="4-6 weeks",
                        risks=["May reveal systemic dependency issues"],
                    ),
                    metric_references=["waste_metrics"],
                    evidence=[
                        f"{blocked_count} stories blocked",
                        f"Average: {avg_blocked:.1f} days",
                    ],
                    status="active",
                    created_at=datetime.now(),
                )
            )

    return insights


def _analyze_code_review(
    bottleneck_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
    selected_team: Optional[str] = None,
) -> List[InsightResponse]:
    """Analyze code review stage - unique to story-level analysis"""
    insights = []

    stage_analysis = bottleneck_data.get("stage_analysis", {})
    review_data = stage_analysis.get("in_review", {})

    if not review_data:
        return insights

    mean_time = float(review_data.get("mean_time", 0) or 0)
    max_time = float(review_data.get("max_time", 0) or 0)
    items_exceeding = int(review_data.get("items_exceeding_threshold", 0) or 0)

    # Code review should be fast - ideally <1 day, warning if >2 days
    if mean_time > 2:
        scope_desc = _format_scope(selected_arts, selected_pis, selected_team)

        insights.append(
            InsightResponse(
                id=0,
                title=f"Slow Code Reviews: {mean_time:.1f} Days Average",
                severity="warning" if mean_time > 3 else "info",
                confidence=0.85,
                scope=scope_desc,
                scope_id=None,
                observation=f"Code review stage averages {mean_time:.1f} days (max: {max_time:.1f} days). {items_exceeding} stories exceeded threshold. Best practice: code reviews <1 day.",
                interpretation="Slow code reviews create queues, delay feedback, and reduce team flow. Developers context-switch while waiting, reducing productivity. Quick reviews maintain momentum.",
                root_causes=[
                    RootCause(
                        description="Lack of dedicated review time or reviewer availability",
                        evidence=[
                            f"Mean review time: {mean_time:.1f} days",
                            f"{items_exceeding} reviews over threshold",
                        ],
                        confidence=0.85,
                        reference="Code review metrics",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description="Establish team norm: reviews within 4 hours. Use pair/mob programming for complex code.",
                        owner="engineering_manager",
                        effort="1 week",
                        dependencies=["Team agreement"],
                        success_signal="Mean review time <1 day",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Implement review rotation schedule. Block time in calendar for reviews. Set PR size limits (<400 lines).",
                        owner="tech_lead",
                        effort="2 weeks",
                        dependencies=["Process documentation"],
                        success_signal="All PRs reviewed within 1 day",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=["review_mean_time", "review_max_time"],
                    leading_indicators=[
                        "Review queue shrinking",
                        "PRs reviewed same-day",
                    ],
                    lagging_indicators=[
                        "Review time <1 day",
                        "Story lead time reduced",
                    ],
                    timeline="2-3 weeks",
                    risks=["May need training on efficient code review practices"],
                ),
                metric_references=["code_review_metrics"],
                evidence=[
                    f"Mean: {mean_time:.1f} days",
                    f"Target: <1 day",
                    f"{items_exceeding} over threshold",
                ],
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


# Helper functions


def _get_expected_time(stage_name: str) -> float:
    """Get expected duration for a story stage"""
    expected_times = {
        "refinement": 2,
        "ready_for_development": 1,
        "in_development": 5,
        "in_review": 1,
        "ready_for_test": 0.5,
        "in_testing": 3,
        "ready_for_deployment": 0.5,
        "deployed": 0,
    }
    return expected_times.get(stage_name, 2)


def _get_stage_root_cause(stage_name: str) -> str:
    """Get likely root cause for a bottleneck in a specific story stage"""
    causes = {
        "refinement": "Stories not fully refined or acceptance criteria unclear",
        "ready_for_development": "Developer availability or priority conflicts",
        "in_development": "Story complexity, technical debt, or scope creep",
        "in_review": "Lack of reviewer availability or large PR sizes",
        "ready_for_test": "QA resource constraints or test environment issues",
        "in_testing": "Complex test scenarios, defects found, or test environment issues",
        "ready_for_deployment": "Deployment process delays or release coordination",
        "deployed": "N/A",
    }
    return causes.get(stage_name, "Process inefficiencies or resource constraints")


def _get_stage_actions(
    stage_name: str, mean_time: float, items_exceeding: int
) -> List[Action]:
    """Get recommended actions for a specific story stage bottleneck"""

    actions_map = {
        "refinement": [
            Action(
                timeframe="immediate",
                description="Review backlog refinement process. Ensure stories have clear acceptance criteria before sprint planning.",
                owner="product_owner",
                effort="1 week",
                dependencies=[],
                success_signal="All sprint stories have clear acceptance criteria",
            ),
        ],
        "in_development": [
            Action(
                timeframe="immediate",
                description="Implement pair programming for complex stories. Break down large stories into smaller tasks.",
                owner="tech_lead",
                effort="Ongoing",
                dependencies=["Team training"],
                success_signal=f"Development time reduced to <{mean_time * 0.7:.1f} days",
            ),
        ],
        "in_review": [
            Action(
                timeframe="immediate",
                description="Establish <4 hour review SLA. Block time for daily code reviews. Limit PR size to <400 lines.",
                owner="engineering_manager",
                effort="1 week",
                dependencies=[],
                success_signal="All reviews completed within 1 day",
            ),
        ],
        "in_testing": [
            Action(
                timeframe="immediate",
                description="Review test coverage and automation. Ensure test environments are stable and available.",
                owner="qa_lead",
                effort="2 weeks",
                dependencies=["Infrastructure support"],
                success_signal=f"Testing time reduced to <{mean_time * 0.7:.1f} days",
            ),
        ],
    }

    return actions_map.get(
        stage_name,
        [
            Action(
                timeframe="immediate",
                description=f"Investigate root cause of delays in {stage_name.replace('_', ' ')} stage",
                owner="scrum_master",
                effort="1 week",
                dependencies=[],
                success_signal=f"Mean time reduced by 30%",
            ),
        ],
    )
