"""
Advanced Insights Generator
Analyzes comprehensive delivery metrics to generate actionable insights
Based on DL Webb App delivery_analysis.html patterns
Enhanced with expert agile coach LLM analysis
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from api_models import InsightResponse, RootCause, Action, ExpectedOutcome

# LLM service for expert commentary (will be injected)
_llm_service = None


def set_llm_service(llm_service):
    """Set the LLM service for expert commentary"""
    global _llm_service
    _llm_service = llm_service


def generate_advanced_insights(
    analysis_summary: Dict[str, Any],
    art_comparison: List[Dict[str, Any]],
    selected_arts: Optional[List[str]] = None,
    selected_pis: Optional[List[str]] = None,
    llm_service=None,
) -> List[InsightResponse]:
    """
    Generate comprehensive insights from analysis summary data

    Args:
        analysis_summary: Data from /api/analysis/summary endpoint
        art_comparison: List of ART performance data
        selected_arts: Filtered ARTs (if any)
        selected_pis: Filtered PIs (if any)
        llm_service: LLM service for expert commentary (optional)

    Returns:
        List of detailed insights with root causes and recommendations
    """
    # Set LLM service for expert commentary
    if llm_service:
        set_llm_service(llm_service)

    insights = []

    # Extract analysis sections
    leadtime = analysis_summary.get("leadtime_analysis", {})
    bottleneck = analysis_summary.get("bottleneck_analysis", {})
    waste = analysis_summary.get("waste_analysis", {})
    planning = analysis_summary.get("planning_accuracy", {})
    throughput = analysis_summary.get("throughput_analysis", {})

    # 1. Bottleneck Analysis Insights
    insights.extend(_analyze_bottlenecks(bottleneck, selected_arts, selected_pis))

    # 2. Stuck Item Pattern Analysis (Hidden Dependencies)
    insights.extend(
        _analyze_stuck_item_patterns(bottleneck, selected_arts, selected_pis)
    )

    # 3. WIP Statistics Analysis
    insights.extend(_analyze_wip_statistics(bottleneck, selected_arts, selected_pis))

    # 4. Waste Analysis Insights
    insights.extend(_analyze_waste(waste, selected_arts, selected_pis))

    # 5. Planning Accuracy Insights
    insights.extend(_analyze_planning_accuracy(planning, selected_arts, selected_pis))

    # 6. Flow Efficiency Insights
    insights.extend(
        _analyze_flow_efficiency(art_comparison, selected_arts, selected_pis)
    )

    # 7. Throughput & Delivery Pattern Insights
    insights.extend(_analyze_throughput(throughput, selected_arts, selected_pis))

    # 8. Lead Time Variability Insights
    insights.extend(
        _analyze_leadtime_variability(leadtime, selected_arts, selected_pis)
    )

    # 9. ART Load Balancing Analysis (Organizational Structure)
    insights.extend(
        _analyze_art_load_balance(art_comparison, selected_arts, selected_pis)
    )

    # 10. Feature Size & Batch Analysis (Way of Working)
    insights.extend(_analyze_feature_sizing(throughput, selected_arts, selected_pis))

    # Enhance insights with expert LLM commentary
    if _llm_service:
        _enhance_insights_with_expert_analysis(insights)

    return insights[:15]  # Limit to top 15 insights


def _enhance_insights_with_expert_analysis(insights: List[InsightResponse]):
    """Enhance insights with expert agile coach commentary using LLM"""
    for insight in insights:
        try:
            # Prepare metrics for LLM context
            metrics = {
                "severity": insight.severity,
                "confidence": f"{insight.confidence * 100:.0f}%",
                "scope": insight.scope,
            }

            # Add metric references
            if insight.metric_references:
                for ref in insight.metric_references[:3]:  # Top 3 metrics
                    metrics[ref] = "tracked"

            # Get expert commentary from LLM
            expert_commentary = _llm_service.enhance_insight_with_expert_analysis(
                insight_title=insight.title,
                observation=insight.observation,
                interpretation=insight.interpretation,
                metrics=metrics,
                root_causes=[
                    {"description": rc.description, "confidence": rc.confidence}
                    for rc in insight.root_causes
                ],
                recommendations=[
                    {"timeframe": action.timeframe, "description": action.description}
                    for action in insight.recommended_actions
                ],
            )

            # Add expert commentary to interpretation
            if expert_commentary:
                insight.interpretation = f"{insight.interpretation}\n\n🎯 **Expert Coach Insight:** {expert_commentary}"
                print(
                    f"  ✅ Enhanced insight '{insight.title[:50]}...' with expert analysis"
                )

        except Exception as e:
            print(f"  ⚠️ Failed to enhance insight '{insight.title}': {e}")
            continue


def _analyze_bottlenecks(
    bottleneck_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """Analyze workflow bottlenecks and generate insights"""
    insights = []

    bottleneck_stages = bottleneck_data.get("bottleneck_stages", [])
    if not bottleneck_stages:
        return insights

    # Sort by bottleneck score (higher = worse bottleneck)
    sorted_bottlenecks = sorted(
        bottleneck_stages, key=lambda x: x.get("bottleneck_score", 0), reverse=True
    )

    # Top bottleneck
    if sorted_bottlenecks:
        top_bottleneck = sorted_bottlenecks[0]
        stage_name = top_bottleneck.get("stage", "Unknown")
        score = float(top_bottleneck.get("bottleneck_score", 0) or 0)
        mean_time = float(top_bottleneck.get("mean_time", 0) or 0)
        max_time = float(top_bottleneck.get("max_time", 0) or 0)
        items_exceeding = top_bottleneck.get("items_exceeding_threshold", 0)

        # Get stuck items for this stage
        stuck_items = bottleneck_data.get("stuck_items", [])

        # Filter by ART if specified
        if selected_arts:
            stuck_items = [
                item for item in stuck_items if item.get("art") in selected_arts
            ]

        stage_stuck_items = [
            item for item in stuck_items if item.get("stage") == stage_name
        ]
        top_stuck = sorted(
            stage_stuck_items, key=lambda x: x.get("days_in_stage", 0), reverse=True
        )[:3]

        if score > 50:  # Significant bottleneck
            scope_desc = _format_scope(selected_arts, selected_pis)

            # Build stuck items evidence
            stuck_evidence = []
            if top_stuck:
                for item in top_stuck:
                    issue_key = item.get("issue_key", "Unknown")
                    days = item.get("days_in_stage", 0)
                    stuck_evidence.append(
                        f"{issue_key}: {days:.1f} days in {stage_name}"
                    )

            insights.append(
                InsightResponse(
                    id=0,
                    title=f"Critical Bottleneck in {stage_name.replace('_', ' ').title()} Stage",
                    severity="critical" if score > 70 else "warning",
                    confidence=0.9,
                    scope=scope_desc,
                    scope_id=None,
                    observation=f"The {stage_name.replace('_', ' ')} stage has a bottleneck score of {score:.1f}%. Average time: {mean_time:.1f} days, with {items_exceeding:,} items exceeding threshold (max: {max_time:.0f} days).",
                    interpretation=f"Features are spending excessive time in {stage_name.replace('_', ' ')}. This stage is a critical constraint in your delivery flow. The high number of items exceeding threshold ({items_exceeding:,}) and extreme outliers (max {max_time:.0f} days) indicate systemic issues requiring immediate attention.",
                    root_causes=[
                        RootCause(
                            description="Severe flow blockage with items stuck in stage",
                            evidence=(
                                stuck_evidence
                                if stuck_evidence
                                else [
                                    f"Mean duration: {mean_time:.1f} days",
                                    f"Maximum observed: {max_time:.0f} days",
                                    f"{items_exceeding:,} items exceeding threshold",
                                ]
                            ),
                            confidence=0.95,
                            reference=f"{stage_name} stage metrics",
                        ),
                        RootCause(
                            description="Process inefficiencies or resource constraints",
                            evidence=[
                                f"Bottleneck score of {score:.1f}% indicates systemic issues",
                                f"High variability: avg {mean_time:.1f} days, max {max_time:.0f} days",
                            ],
                            confidence=0.85,
                            reference="Workflow stage analysis",
                        ),
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description=f"Review top stuck items in {stage_name.replace('_', ' ')} - investigate {', '.join([i.get('issue_key', '') for i in top_stuck[:3]][:3]) if top_stuck else 'longest running items'} to identify common blockers",
                            owner="delivery_manager",
                            effort="2-4 hours",
                            dependencies=[],
                            success_signal=f"Root cause identified and documented for stuck items",
                        ),
                        Action(
                            timeframe="short_term",
                            description=f"Implement strict WIP limits for {stage_name.replace('_', ' ')} stage (recommended: 5-10 items max per team) and establish daily standup focus on blocked items",
                            owner="scrum_master",
                            effort="1 week",
                            dependencies=["Team agreement on WIP limits"],
                            success_signal=f"Mean time reduced to <{mean_time * 0.7:.1f} days within 2 PIs",
                        ),
                        Action(
                            timeframe="medium_term",
                            description="Value stream mapping workshop to identify and eliminate waste in this stage. Consider pairing/swarming practices for stuck items.",
                            owner="engineering_manager",
                            effort="2-4 weeks",
                            dependencies=["Budget approval", "Training materials"],
                            success_signal=f"Max time reduced to <{max_time * 0.5:.0f} days, items exceeding threshold reduced by 40%",
                        ),
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=[
                            f"{stage_name}_mean_time",
                            f"{stage_name}_max_time",
                            f"{stage_name}_items_exceeding_threshold",
                            "overall_lead_time",
                        ],
                        leading_indicators=[
                            "WIP count trending down",
                            "Fewer items exceeding threshold",
                            "Cycle time stabilizing",
                        ],
                        lagging_indicators=[
                            f"Mean time in stage reduced to <{mean_time * 0.7:.1f} days",
                            "Items exceeding threshold reduced by 40%+",
                        ],
                        timeline="4-8 weeks",
                        risks=[
                            "Team resistance to WIP limits",
                            "Initial productivity dip during process changes",
                            "Hidden dependencies may emerge when items move faster",
                        ],
                    ),
                    metric_references=[
                        f"{stage_name}_bottleneck_score",
                        f"{stage_name}_mean_time",
                        f"{stage_name}_max_time",
                    ],
                    evidence=[
                        f"Bottleneck score: {score:.1f}%",
                        f"Mean duration: {mean_time:.1f} days",
                        f"Maximum duration: {max_time:.0f} days",
                        f"Items exceeding threshold: {items_exceeding:,}",
                    ]
                    + (stuck_evidence[:3] if stuck_evidence else []),
                    status="active",
                    created_at=datetime.now(),
                )
            )

    # Multiple bottlenecks
    if len(sorted_bottlenecks) >= 3:
        top_3 = sorted_bottlenecks[:3]
        if all(b.get("bottleneck_score", 0) > 40 for b in top_3):
            stage_names = [b.get("stage", "").replace("_", " ").title() for b in top_3]
            total_mean = sum(b.get("mean_time", 0) for b in top_3)
            total_items = sum(b.get("items_exceeding_threshold", 0) for b in top_3)

            insights.append(
                InsightResponse(
                    id=0,
                    title="Multiple Workflow Bottlenecks Detected",
                    severity="warning",
                    confidence=0.85,
                    scope=_format_scope(selected_arts, selected_pis),
                    scope_id=None,
                    observation=f"Three stages showing bottleneck behavior: {', '.join(stage_names)}. Combined average time: {total_mean:.1f} days, with {total_items:,} items total exceeding thresholds.",
                    interpretation="Multiple bottlenecks indicate systemic workflow issues rather than isolated problems. The entire delivery pipeline needs optimization. This suggests issues with overall process design, resource allocation, or dependencies between stages.",
                    root_causes=[
                        RootCause(
                            description="Workflow design issues - sequential dependencies",
                            evidence=[
                                f"{len(top_3)} stages with bottleneck scores >40"
                            ],
                            confidence=0.8,
                            reference="Bottleneck analysis",
                        )
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description="Conduct value stream mapping workshop to identify waste and handoff delays",
                            owner="agile_coach",
                            effort="1 day workshop",
                            dependencies=["Key stakeholders available"],
                            success_signal="Value stream map created with identified improvement areas",
                        )
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=["overall_lead_time", "flow_efficiency"],
                        leading_indicators=["Reduced handoff times"],
                        lagging_indicators=["30% reduction in total lead time"],
                        timeline="8-12 weeks",
                        risks=["Significant process changes may disrupt current work"],
                    ),
                    metric_references=["bottleneck_scores", "overall_lead_time"],
                    evidence=[
                        f"Three stages with bottleneck scores >40: {', '.join(stage_names)}"
                    ],
                    status="active",
                    created_at=datetime.now(),
                )
            )

    return insights


def _analyze_stuck_item_patterns(
    bottleneck_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """
    Analyze stuck items for patterns - items stuck in multiple stages indicate
    systemic issues or hidden dependencies (inspired by DL Webb APP Delivery Report)
    """
    insights = []

    stuck_items = bottleneck_data.get("stuck_items", [])
    if not stuck_items:
        return insights

    # Filter by ART if specified
    if selected_arts:
        stuck_items = [item for item in stuck_items if item.get("art") in selected_arts]
        if not stuck_items:
            return insights

    # Group stuck items by issue_key to find items stuck in multiple stages
    items_by_key = {}
    for item in stuck_items:
        key = item.get("issue_key")
        if key:
            if key not in items_by_key:
                items_by_key[key] = []
            items_by_key[key].append(item)

    # Find items stuck in multiple stages (indicates complex dependencies or systemic blockers)
    multi_stage_stuck = {
        key: stages
        for key, stages in items_by_key.items()
        if len(stages) >= 2  # Stuck in 2+ stages
    }

    if multi_stage_stuck:
        # Find the worst offenders
        worst_items = sorted(
            multi_stage_stuck.items(),
            key=lambda x: (len(x[1]), sum(s.get("days_in_stage", 0) for s in x[1])),
            reverse=True,
        )[:3]

        scope_desc = _format_scope(selected_arts, selected_pis)

        # Build evidence from worst items
        evidence_list = []
        total_stages_affected = 0
        for issue_key, stages in worst_items:
            stage_names = [s.get("stage", "unknown") for s in stages]
            total_days = sum(s.get("days_in_stage", 0) for s in stages)
            evidence_list.append(
                f"{issue_key}: stuck in {len(stages)} stages ({', '.join(stage_names[:3])}) - total {total_days:.0f} days"
            )
            total_stages_affected += len(stages)

        insights.append(
            InsightResponse(
                id=0,
                title=f"Hidden Dependencies Detected: {len(multi_stage_stuck)} Items Stuck Across Multiple Stages",
                severity="warning",
                confidence=0.85,
                scope=scope_desc,
                scope_id=None,
                observation=f"Found {len(multi_stage_stuck)} items stuck in multiple workflow stages, with top 3 items stuck in {total_stages_affected} total stages. This pattern strongly suggests hidden dependencies, incomplete requirements, or systemic blockers.",
                interpretation="When items get stuck repeatedly across different stages, it indicates deeper issues than simple bottlenecks. These could be: incomplete requirements discovered late, cross-team dependencies not identified early, technical debt blocking progress, or unclear acceptance criteria. This requires investigation beyond process optimization.",
                root_causes=[
                    RootCause(
                        description="Hidden dependencies or incomplete requirements discovered during execution",
                        evidence=evidence_list[:2],
                        confidence=0.9,
                        reference="Multi-stage stuck item analysis",
                    ),
                    RootCause(
                        description="Systemic blockers affecting multiple workflow stages",
                        evidence=[
                            f"{len(multi_stage_stuck)} total items showing multi-stage stuck pattern",
                            "Pattern suggests issues beyond single-stage bottlenecks",
                        ],
                        confidence=0.8,
                        reference="Stuck item pattern detection",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description=f"Deep-dive investigation of {', '.join([item[0] for item in worst_items[:3]])}: Interview teams to understand why these items are stuck in multiple stages. Document dependencies and blockers.",
                        owner="product_owner",
                        effort="4-8 hours",
                        dependencies=[],
                        success_signal="Root causes documented with action plan for each stuck item",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Implement dependency mapping in PI Planning: Use story mapping to identify cross-team dependencies before work starts. Establish 'Definition of Ready' checklist including dependency verification.",
                        owner="rte",
                        effort="2 weeks",
                        dependencies=["Team training on dependency mapping"],
                        success_signal="50% reduction in items stuck in multiple stages within next PI",
                    ),
                    Action(
                        timeframe="medium_term",
                        description="Establish architectural runway: Dedicate 15-20% of capacity to reducing technical debt and resolving systemic blockers that cause cross-stage delays.",
                        owner="architect",
                        effort="Ongoing",
                        dependencies=["Backlog prioritization", "Stakeholder buy-in"],
                        success_signal="Items moving linearly through stages without repeated blockages",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=[
                        "items_stuck_multiple_stages",
                        "dependency_identification_rate",
                        "blocked_item_resolution_time",
                    ],
                    leading_indicators=[
                        "Dependencies identified in PI Planning increase",
                        "Definition of Ready adherence improves",
                    ],
                    lagging_indicators=[
                        "Items stuck in multiple stages reduced by 60%",
                        "Overall lead time reduced by 20-30%",
                    ],
                    timeline="6-12 weeks",
                    risks=[
                        "Deep-dive investigations may uncover organizational issues",
                        "Architectural runway work may reduce feature delivery velocity short-term",
                    ],
                ),
                metric_references=[
                    "stuck_items_multi_stage",
                    "dependency_detection",
                ],
                evidence=evidence_list,
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _analyze_wip_statistics(
    bottleneck_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """
    Analyze WIP statistics to identify stages with excessive work in progress
    (inspired by DL Webb APP Delivery Report WIP analysis)
    """
    insights = []

    wip_stats = bottleneck_data.get("wip_statistics", {})
    if not wip_stats or not isinstance(wip_stats, dict):
        return insights

    # Find stages with high item counts and high items exceeding threshold
    problematic_stages = []
    for stage, stats in wip_stats.items():
        if not isinstance(stats, dict):
            continue

        total_items = stats.get("total_items", 0)
        exceeding = stats.get("items_exceeding_threshold", 0)
        mean_time = stats.get("mean_time", 0)

        # Flag if >25% of items exceed threshold or very high WIP
        if total_items > 1000 and exceeding > 0:
            exceeding_pct = (exceeding / total_items * 100) if total_items > 0 else 0
            if exceeding_pct > 25 or total_items > 5000:
                problematic_stages.append(
                    {
                        "stage": stage,
                        "total_items": total_items,
                        "exceeding": exceeding,
                        "exceeding_pct": exceeding_pct,
                        "mean_time": mean_time,
                    }
                )

    if problematic_stages:
        # Sort by exceeding percentage
        problematic_stages.sort(key=lambda x: x["exceeding_pct"], reverse=True)
        top_3 = problematic_stages[:3]

        scope_desc = _format_scope(selected_arts, selected_pis)

        stage_names = [s["stage"].replace("_", " ").title() for s in top_3]
        total_wip = sum(s["total_items"] for s in top_3)
        total_exceeding = sum(s["exceeding"] for s in top_3)

        insights.append(
            InsightResponse(
                id=0,
                title=f"Excessive WIP Detected in {len(problematic_stages)} Stages",
                severity="warning",
                confidence=0.85,
                scope=scope_desc,
                scope_id=None,
                observation=f"Found {len(problematic_stages)} stages with excessive work in progress. Top stages: {', '.join(stage_names)}. Total WIP in these stages: {total_wip:,} items, with {total_exceeding:,} exceeding thresholds.",
                interpretation="High WIP creates hidden costs: context switching, delayed feedback, increased coordination overhead, and reduced flow efficiency. When many items exceed time thresholds, it indicates work is starting before capacity is available. This is a classic symptom of push-based rather than pull-based workflow.",
                root_causes=[
                    RootCause(
                        description="Starting work before capacity available (push vs pull)",
                        evidence=[
                            f"{top_3[0]['stage']}: {top_3[0]['total_items']:,} items with {top_3[0]['exceeding_pct']:.1f}% exceeding threshold",
                            (
                                f"{top_3[1]['stage']}: {top_3[1]['total_items']:,} items with {top_3[1]['exceeding_pct']:.1f}% exceeding threshold"
                                if len(top_3) > 1
                                else ""
                            ),
                        ],
                        confidence=0.9,
                        reference="WIP statistics analysis",
                    ),
                    RootCause(
                        description="Lack of WIP limits or limits not being enforced",
                        evidence=[
                            f"Total {total_wip:,} items in progress across {len(top_3)} stages",
                            f"{total_exceeding:,} items exceeding time thresholds",
                        ],
                        confidence=0.85,
                        reference="Workflow stage metrics",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description=f"Implement strict WIP limits for {', '.join([s['stage'] for s in top_3])}. Recommended: limit to 2x team size per stage. Stop starting, start finishing.",
                        owner="scrum_master",
                        effort="1 week",
                        dependencies=["Team agreement"],
                        success_signal=f"WIP reduced by 40% within 2 sprints",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Establish pull-based workflow: Teams only pull new work when capacity becomes available. Visualize WIP limits on boards.",
                        owner="agile_coach",
                        effort="2-3 weeks",
                        dependencies=["Visual management boards", "Team training"],
                        success_signal="Items exceeding threshold reduced by 50%",
                    ),
                    Action(
                        timeframe="medium_term",
                        description="Regular WIP audits: Weekly review of items in each stage, age items out or escalate blockers. Focus on completing over starting.",
                        owner="delivery_manager",
                        effort="Ongoing",
                        dependencies=["Reporting dashboards"],
                        success_signal="Mean time in stage reduced by 30%, fewer aged items",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=[
                        "total_wip_by_stage",
                        "items_exceeding_threshold",
                        "mean_time_in_stage",
                    ],
                    leading_indicators=[
                        "WIP limits visualized and enforced",
                        "Pull-based workflow adoption",
                    ],
                    lagging_indicators=[
                        "WIP reduced by 40-50%",
                        "Flow efficiency improves by 20%+",
                        "Items exceeding threshold down 50%",
                    ],
                    timeline="4-8 weeks",
                    risks=[
                        "Teams may resist WIP limits initially",
                        "Short-term perceived productivity drop",
                    ],
                ),
                metric_references=[
                    "wip_by_stage",
                    "items_exceeding_threshold",
                ],
                evidence=[
                    f"{s['stage']}: {s['total_items']:,} items ({s['exceeding']:,} exceeding, {s['exceeding_pct']:.1f}%)"
                    for s in top_3
                ],
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _analyze_waste(
    waste_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """Analyze waste metrics and generate insights"""
    insights = []

    total_waste = float(waste_data.get("total_waste_days", 0) or 0)

    # Calculate waiting waste from waiting_time_waste breakdown
    waiting_data = waste_data.get("waiting_time_waste", {})
    waiting = sum(
        float(stage.get("total_days_wasted", 0) or 0)
        for stage in waiting_data.values()
        if isinstance(stage, dict)
    )

    # Get removed work count (items removed)
    removed_work = waste_data.get("removed_work", {})
    removed = float(
        removed_work.get("duplicates", 0) or 0
    )  # Using duplicates as proxy for removed work

    if total_waste > 100:  # Significant waste

        insights.append(
            InsightResponse(
                id=0,
                title=f"High Waste Detected: {total_waste:.0f} Days Lost",
                severity="critical" if total_waste > 500 else "warning",
                confidence=0.9,
                scope=_format_scope(selected_arts, selected_pis),
                scope_id=None,
                observation=f"Total waste: {total_waste:.0f} days. Breakdown: Waiting waste: {waiting:.0f} days, Removed work: {removed:.0f} days.",
                interpretation="Significant value delivery time is being consumed by non-value-adding activities. This directly impacts time-to-market and team efficiency.",
                root_causes=[
                    RootCause(
                        description="Excessive waiting time in queue states",
                        evidence=[
                            f"Waiting waste accounts for {waiting:.0f} days ({(waiting/total_waste*100):.1f}% of total)"
                        ],
                        confidence=0.9,
                        reference="Waste analysis",
                    ),
                    RootCause(
                        description="Poor prioritization or changing requirements",
                        evidence=[
                            f"Removed work waste: {removed:.0f} days of effort on undelivered features"
                        ],
                        confidence=0.75,
                        reference="Feature removal patterns",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description="Implement daily standup focused on unblocking waiting items",
                        owner="scrum_master",
                        effort="Ongoing",
                        dependencies=[],
                        success_signal="Waiting waste reduced by 20% in next PI",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Review and strengthen Definition of Ready to reduce rework and removal",
                        owner="product_owner",
                        effort="1 week",
                        dependencies=["Team workshop"],
                        success_signal="Removed work waste <10% of total waste",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=[
                        "total_waste_days",
                        "waiting_waste",
                        "removed_work_waste",
                    ],
                    leading_indicators=[
                        "Reduced queue times",
                        "Fewer feature removals",
                    ],
                    lagging_indicators=["40% reduction in total waste within 2 PIs"],
                    timeline="1-2 PIs (10-20 weeks)",
                    risks=[
                        "Requires consistent discipline",
                        "May slow initial feature intake",
                    ],
                ),
                metric_references=[
                    "total_waste_days",
                    "waiting_waste",
                    "removed_work_waste",
                ],
                evidence=[
                    f"Total waste: {total_waste:.0f} days",
                    f"Waiting waste: {waiting:.0f} days",
                    f"Removed work: {removed:.0f} days",
                ],
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _analyze_planning_accuracy(
    planning_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """Analyze planning accuracy and generate insights"""
    insights = []

    accuracy_pct = float(planning_data.get("accuracy_percentage", 0) or 0)
    committed = int(planning_data.get("committed_count", 0) or 0)
    delivered = int(planning_data.get("delivered_count", 0) or 0)

    if accuracy_pct < 70 and committed > 10:  # Low predictability with enough data
        insights.append(
            InsightResponse(
                id=0,
                title=f"Low PI Predictability: {accuracy_pct:.1f}%",
                severity="critical" if accuracy_pct < 50 else "warning",
                confidence=0.9,
                scope=_format_scope(selected_arts, selected_pis),
                scope_id=None,
                observation=f"Only {delivered} of {committed} committed features were delivered ({accuracy_pct:.1f}% predictability). SAFe target is ≥80%.",
                interpretation="Teams are consistently overcommitting or underdelivering, indicating planning process issues or execution challenges.",
                root_causes=[
                    RootCause(
                        description="Inaccurate story sizing or velocity estimates",
                        evidence=[
                            f"Delivered {delivered}/{committed} features ({(committed-delivered)} shortfall)",
                            "Pattern suggests systematic estimation errors",
                        ],
                        confidence=0.8,
                        reference="PI planning data",
                    ),
                    RootCause(
                        description="Mid-PI scope changes or dependencies",
                        evidence=["Significant gap between commitment and delivery"],
                        confidence=0.7,
                        reference="Planning vs actuals",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description="Conduct retrospective to understand root causes of missed commitments",
                        owner="rte",
                        effort="2 hours",
                        dependencies=[],
                        success_signal="Top 3 root causes identified and documented",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Implement PI planning capacity buffer (15-20% contingency)",
                        owner="product_management",
                        effort="Next PI planning",
                        dependencies=["Leadership buy-in"],
                        success_signal="Predictability improves to >75%",
                    ),
                    Action(
                        timeframe="medium_term",
                        description="Establish historical velocity baseline and use for future planning",
                        owner="scrum_master",
                        effort="2-3 PIs",
                        dependencies=["Consistent velocity tracking"],
                        success_signal="Predictability ≥80% for 2 consecutive PIs",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=[
                        "pi_predictability",
                        "committed_count",
                        "delivered_count",
                    ],
                    leading_indicators=[
                        "Improved estimation accuracy",
                        "Reduced mid-PI changes",
                    ],
                    lagging_indicators=[
                        "PI Predictability ≥80%",
                        "Stakeholder confidence increased",
                    ],
                    timeline="2-3 PIs (20-30 weeks)",
                    risks=[
                        "May need to commit to fewer features initially",
                        "Requires discipline to hold scope",
                    ],
                ),
                metric_references=[
                    "pi_predictability",
                    "committed_count",
                    "delivered_count",
                ],
                evidence=[
                    f"Committed: {committed} features",
                    f"Delivered: {delivered} features",
                    f"Predictability: {accuracy_pct:.1f}%",
                ],
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _analyze_flow_efficiency(
    art_comparison: List[Dict[str, Any]],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """Analyze flow efficiency across ARTs"""
    insights = []

    if not art_comparison:
        return insights

    # Find ARTs with low flow efficiency
    low_flow_arts = [
        art for art in art_comparison if art.get("flow_efficiency", 0) < 30
    ]

    if low_flow_arts:
        art_names = [art.get("art_name", "Unknown") for art in low_flow_arts[:5]]
        avg_flow = sum(art.get("flow_efficiency", 0) for art in low_flow_arts) / len(
            low_flow_arts
        )

        insights.append(
            InsightResponse(
                id=0,
                title=f"Low Flow Efficiency in {len(low_flow_arts)} ART(s)",
                severity="warning",
                confidence=0.85,
                scope=_format_scope(selected_arts, selected_pis),
                scope_id=None,
                observation=f"ARTs with flow efficiency <30%: {', '.join(art_names)}. Average: {avg_flow:.1f}%.",
                interpretation="These ARTs are spending >70% of cycle time in waiting states (backlog, planned) vs. active development. Industry target is >40% flow efficiency.",
                root_causes=[
                    RootCause(
                        description="Excessive work in progress (WIP)",
                        evidence=[
                            f"{len(low_flow_arts)} ARTs below 30% efficiency threshold"
                        ],
                        confidence=0.8,
                        reference="Flow efficiency metrics",
                    ),
                    RootCause(
                        description="Frequent context switching or unclear priorities",
                        evidence=["Low percentage of value-add time"],
                        confidence=0.75,
                        reference="Stage time distribution",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description="Implement WIP limits: 2-3 features per team in active development",
                        owner="scrum_master",
                        effort="1 week",
                        dependencies=["Team agreement"],
                        success_signal="WIP limits visible and enforced",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Reduce batch size - break large features into smaller increments",
                        owner="product_owner",
                        effort="Ongoing",
                        dependencies=["Story splitting training"],
                        success_signal="Average feature size reduced by 30%",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=["flow_efficiency", "cycle_time", "throughput"],
                    leading_indicators=[
                        "Reduced WIP count",
                        "Faster feature completion",
                    ],
                    lagging_indicators=[
                        "Flow efficiency >40%",
                        "Cycle time reduced by 20%",
                    ],
                    timeline="1-2 PIs (10-20 weeks)",
                    risks=[
                        "Initial throughput may appear lower",
                        "Requires team discipline",
                    ],
                ),
                metric_references=["flow_efficiency", "cycle_time"],
                evidence=[
                    f"{len(low_flow_arts)} ARTs below 30% efficiency",
                    f"Average flow efficiency: {avg_flow:.1f}%",
                    f"ARTs: {', '.join(art_names)}",
                ],
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _analyze_throughput(
    throughput_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """Analyze delivery throughput patterns"""
    insights = []

    features_delivered = int(throughput_data.get("total_features_delivered", 0) or 0)
    avg_per_week = float(throughput_data.get("average_per_week", 0) or 0)
    trend = throughput_data.get("trend", "stable")
    trend = throughput_data.get("trend", "stable")

    if trend == "declining" and features_delivered > 20:
        insights.append(
            InsightResponse(
                id=0,
                title="Declining Delivery Throughput Detected",
                severity="warning",
                confidence=0.8,
                scope=_format_scope(selected_arts, selected_pis),
                scope_id=None,
                observation=f"Throughput is declining. Currently averaging {avg_per_week:.1f} features/week (total: {features_delivered} features).",
                interpretation="Decreasing delivery rate may indicate accumulating technical debt, increasing complexity, or team capacity issues.",
                root_causes=[
                    RootCause(
                        description="Technical debt slowing development",
                        evidence=["Declining throughput trend"],
                        confidence=0.7,
                        reference="Throughput analysis",
                    ),
                    RootCause(
                        description="Increasing feature complexity",
                        evidence=["Slower delivery rate over time"],
                        confidence=0.65,
                        reference="Delivery trends",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description="Allocate 20% of capacity to technical debt reduction",
                        owner="engineering_manager",
                        effort="Ongoing",
                        dependencies=["Product owner agreement"],
                        success_signal="Technical debt backlog reduced by 25%",
                    )
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=["throughput", "velocity", "defect_rate"],
                    leading_indicators=["Code quality metrics improving"],
                    lagging_indicators=["Throughput stabilizes or increases"],
                    timeline="2-3 PIs",
                    risks=["Short-term feature delivery reduction"],
                ),
                metric_references=[
                    "total_features_delivered",
                    "average_per_week",
                    "trend",
                ],
                evidence=[
                    f"Total features delivered: {features_delivered}",
                    f"Average per week: {avg_per_week:.1f}",
                    f"Trend: {trend}",
                ],
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _analyze_leadtime_variability(
    leadtime_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """Analyze lead time variability and predictability"""
    insights = []

    stage_stats = leadtime_data.get("stage_statistics", {})
    total_stats = stage_stats.get("total_leadtime", {})

    if total_stats:
        mean = float(total_stats.get("mean", 0) or 0)
        median = float(total_stats.get("median", 0) or 0)
        p85 = float(total_stats.get("p85", 0) or 0)
        p95 = float(total_stats.get("p95", 0) or 0)

        # High variability if p85 is >2x median
        if median > 0 and p85 > median * 2:
            variability_ratio = p85 / median

            insights.append(
                InsightResponse(
                    id=0,
                    title="High Lead Time Variability Detected",
                    severity="warning",
                    confidence=0.85,
                    scope=_format_scope(selected_arts, selected_pis),
                    scope_id=None,
                    observation=f"Lead time variability is high. Median: {median:.0f} days, 85th percentile: {p85:.0f} days ({variability_ratio:.1f}x difference).",
                    interpretation="High variability makes delivery dates unpredictable. Some features take significantly longer than typical, indicating inconsistent processes.",
                    root_causes=[
                        RootCause(
                            description="Inconsistent feature sizing or complexity",
                            evidence=[
                                f"85th percentile ({p85:.0f}d) is {variability_ratio:.1f}x median ({median:.0f}d)"
                            ],
                            confidence=0.8,
                            reference="Lead time distribution",
                        ),
                        RootCause(
                            description="External dependencies causing delays",
                            evidence=["Long tail in distribution"],
                            confidence=0.7,
                            reference="Stage time analysis",
                        ),
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description="Implement feature sizing guidelines - target <2 week delivery cycles",
                            owner="product_owner",
                            effort="1 week",
                            dependencies=["Team training"],
                            success_signal="80% of features delivered within 2 weeks",
                        ),
                        Action(
                            timeframe="short_term",
                            description="Track and actively manage external dependencies",
                            owner="scrum_master",
                            effort="Ongoing",
                            dependencies=["Dependency tracking tool"],
                            success_signal="Dependencies resolved within 3 days average",
                        ),
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=[
                            "p85_leadtime",
                            "median_leadtime",
                            "variability_ratio",
                        ],
                        leading_indicators=[
                            "More consistent cycle times",
                            "Fewer outliers",
                        ],
                        lagging_indicators=[
                            "P85 within 1.5x of median",
                            "Improved forecast accuracy",
                        ],
                        timeline="2-3 PIs",
                        risks=["May require decomposing large features"],
                    ),
                    metric_references=[
                        "median_leadtime",
                        "p85_leadtime",
                        "variability_ratio",
                    ],
                    evidence=[
                        f"Median lead time: {median:.0f} days",
                        f"85th percentile: {p85:.0f} days",
                        f"Variability ratio: {variability_ratio:.1f}x",
                    ],
                    status="active",
                    created_at=datetime.now(),
                )
            )

    return insights


def _analyze_art_load_balance(
    art_comparison: List[Dict[str, Any]],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """
    Analyze load distribution across ARTs to identify imbalances that suggest
    need for team restructuring or resource reallocation
    """
    insights = []

    if not art_comparison or len(art_comparison) < 3:
        return insights

    # Calculate load metrics per ART
    art_metrics = []
    for art in art_comparison:
        art_name = art.get("art_name", "Unknown")
        features = art.get("features_delivered", 0)
        avg_leadtime = art.get("avg_leadtime", 0)

        if features > 0:  # Only consider ARTs with actual delivery
            art_metrics.append(
                {
                    "name": art_name,
                    "features": features,
                    "avg_leadtime": avg_leadtime,
                    "throughput_per_day": (
                        features / 90 if features > 0 else 0
                    ),  # Assuming ~90 day period
                }
            )

    if len(art_metrics) < 3:
        return insights

    # Calculate statistics
    throughputs = [m["throughput_per_day"] for m in art_metrics]
    avg_throughput = sum(throughputs) / len(throughputs)
    max_throughput = max(throughputs)
    min_throughput = min(throughputs)

    # Identify imbalance (if max is >3x min, there's significant imbalance)
    if max_throughput > 0 and min_throughput > 0:
        imbalance_ratio = max_throughput / min_throughput

        if imbalance_ratio > 3.0:
            # Find highest and lowest throughput ARTs
            sorted_arts = sorted(
                art_metrics, key=lambda x: x["throughput_per_day"], reverse=True
            )
            highest = sorted_arts[0]
            lowest = sorted_arts[-1]

            scope_desc = _format_scope(selected_arts, selected_pis)

            insights.append(
                InsightResponse(
                    id=0,
                    title=f"Significant Load Imbalance Across ARTs: {imbalance_ratio:.1f}x Variance",
                    severity="warning",
                    confidence=0.80,
                    scope=scope_desc,
                    scope_id=None,
                    observation=f"ART throughput varies by {imbalance_ratio:.1f}x. {highest['name']} delivers {highest['throughput_per_day']:.2f} features/day while {lowest['name']} delivers {lowest['throughput_per_day']:.2f} features/day ({highest['features']} vs {lowest['features']} total features).",
                    interpretation=f"Extreme variance in throughput suggests structural issues: team size differences, capability gaps, domain complexity differences, or misaligned work allocation. This imbalance may indicate need for organizational restructuring, cross-training, or load rebalancing. High-performing ARTs may have best practices worth spreading; low-performing ARTs may need support.",
                    root_causes=[
                        RootCause(
                            description="Unbalanced team capacity or capability distribution",
                            evidence=[
                                f"{highest['name']}: {highest['features']} features delivered",
                                f"{lowest['name']}: {lowest['features']} features delivered",
                                f"Throughput variance: {imbalance_ratio:.1f}x",
                            ],
                            confidence=0.85,
                            reference="ART comparison analysis",
                        ),
                        RootCause(
                            description="Domain complexity or technical debt differences",
                            evidence=[
                                f"{highest['name']} avg lead time: {highest['avg_leadtime']:.1f} days",
                                f"{lowest['name']} avg lead time: {lowest['avg_leadtime']:.1f} days",
                            ],
                            confidence=0.70,
                            reference="Lead time analysis",
                        ),
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description=f"Conduct comparative study: Interview {highest['name']} and {lowest['name']} to understand practices, team structure, tooling, and impediments. Document key differences.",
                            owner="agile_coach",
                            effort="1 week",
                            dependencies=["Access to teams", "Leadership support"],
                            success_signal="Comparative analysis report completed with identified practices to spread and issues to address",
                        ),
                        Action(
                            timeframe="short_term",
                            description=f"Implement Communities of Practice: Create cross-ART guilds for engineering practices, testing, automation. Enable {highest['name']} to mentor {lowest['name']}.",
                            owner="engineering_manager",
                            effort="2-4 weeks setup",
                            dependencies=["Team commitment", "Time allocation"],
                            success_signal="CoPs established with regular meetings, knowledge sharing visible",
                        ),
                        Action(
                            timeframe="medium_term",
                            description=f"Consider organizational restructuring: Evaluate if {lowest['name']} needs more resources, different value stream alignment, or team composition changes. May need to rebalance teams across ARTs.",
                            owner="portfolio_manager",
                            effort="1-2 PIs",
                            dependencies=["Executive approval", "HR involvement"],
                            success_signal=f"Throughput variance reduced to <2x, {lowest['name']} throughput improved by 40%+",
                        ),
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=[
                            "art_throughput_variance",
                            "features_per_art",
                            "avg_leadtime_by_art",
                        ],
                        leading_indicators=[
                            "Knowledge sharing sessions increase",
                            "Cross-ART collaboration visible",
                        ],
                        lagging_indicators=[
                            "Throughput variance reduces to <2.5x",
                            "Low-performing ARTs improve by 30-50%",
                        ],
                        timeline="2-3 PIs",
                        risks=[
                            "Organizational restructuring may cause short-term disruption",
                            "Team members may resist changes",
                        ],
                    ),
                    metric_references=[
                        "art_throughput_variance",
                        "features_delivered_by_art",
                    ],
                    evidence=[
                        f"Highest: {highest['name']} - {highest['features']} features",
                        f"Lowest: {lowest['name']} - {lowest['features']} features",
                        f"Imbalance ratio: {imbalance_ratio:.1f}x",
                        f"Average throughput: {avg_throughput:.2f} features/day",
                    ],
                    status="active",
                    created_at=datetime.now(),
                )
            )

    return insights


def _analyze_feature_sizing(
    throughput_data: Dict[str, Any],
    selected_arts: Optional[List[str]],
    selected_pis: Optional[List[str]],
) -> List[InsightResponse]:
    """
    Analyze feature sizing patterns - large batches lead to longer lead times,
    more risk, and reduced flow efficiency
    """
    insights = []

    # Get lead time distribution data
    features = throughput_data.get("features", [])
    if not features or len(features) < 10:
        return insights

    # Calculate lead time statistics
    lead_times = [
        f.get("lead_time_days", 0) for f in features if f.get("lead_time_days", 0) > 0
    ]
    if not lead_times:
        return insights

    lead_times.sort()
    median_lt = lead_times[len(lead_times) // 2]
    p85_lt = lead_times[int(len(lead_times) * 0.85)]
    p95_lt = lead_times[int(len(lead_times) * 0.95)]

    # Count features by size buckets
    small = len([lt for lt in lead_times if lt <= 21])  # <=3 weeks
    medium = len([lt for lt in lead_times if 21 < lt <= 60])  # 3-8 weeks
    large = len([lt for lt in lead_times if lt > 60])  # >8 weeks

    total = len(lead_times)
    large_pct = (large / total * 100) if total > 0 else 0

    # If >30% of features take >60 days, there's a batch size problem
    if large_pct > 30:
        scope_desc = _format_scope(selected_arts, selected_pis)

        insights.append(
            InsightResponse(
                id=0,
                title=f"Large Batch Problem: {large_pct:.0f}% of Features Exceed 60 Days",
                severity="warning",
                confidence=0.85,
                scope=scope_desc,
                scope_id=None,
                observation=f"Feature size distribution shows poor batching: {small} small (≤21d), {medium} medium (21-60d), {large} large (>60d). {large_pct:.0f}% of features take >60 days. Median: {median_lt:.0f}d, 85th percentile: {p85_lt:.0f}d, 95th percentile: {p95_lt:.0f}d.",
                interpretation="Large batch sizes increase risk, delay feedback, reduce agility, and hide problems. When features take >60 days, you lose the ability to respond to market changes, accumulate unvalidated assumptions, and create integration nightmares. SAFe recommends features completable within a single PI (~90 days max), ideally 2-4 weeks. Your current distribution suggests inadequate decomposition practices.",
                root_causes=[
                    RootCause(
                        description="Inadequate story decomposition and refinement practices",
                        evidence=[
                            f"{large} features ({large_pct:.0f}%) exceed 60 days",
                            f"95th percentile: {p95_lt:.0f} days (should be <90)",
                        ],
                        confidence=0.90,
                        reference="Lead time distribution analysis",
                    ),
                    RootCause(
                        description="Waterfall thinking: trying to complete everything before releasing",
                        evidence=[
                            f"Median lead time: {median_lt:.0f} days (should be <21)",
                            "High variance indicates inconsistent sizing",
                        ],
                        confidence=0.75,
                        reference="Batch size patterns",
                    ),
                ],
                recommended_actions=[
                    Action(
                        timeframe="immediate",
                        description=f"Story splitting workshop: Train teams on INVEST criteria and story splitting patterns. Practice decomposing the {large} large features into smaller, independently deliverable slices.",
                        owner="agile_coach",
                        effort="2-3 days workshop + ongoing coaching",
                        dependencies=["Team availability", "Example stories"],
                        success_signal="Teams can consistently split features into <21 day slices",
                    ),
                    Action(
                        timeframe="short_term",
                        description="Implement 'Definition of Small': Features must be <21 days or justified. Add sizing checkpoints in backlog refinement. Reject oversized features from PI Planning.",
                        owner="product_owner",
                        effort="2 weeks to establish, ongoing enforcement",
                        dependencies=["Refinement process", "Team buy-in"],
                        success_signal="80% of new features sized ≤21 days within 1 PI",
                    ),
                    Action(
                        timeframe="medium_term",
                        description="Shift to continuous delivery mindset: Release smaller increments more frequently. Focus on MVF (Minimum Viable Feature). Measure and celebrate small batch delivery.",
                        owner="engineering_manager",
                        effort="2-3 PIs cultural shift",
                        dependencies=["CI/CD pipeline", "Stakeholder education"],
                        success_signal="Median lead time <21 days, 85th percentile <40 days",
                    ),
                ],
                expected_outcomes=ExpectedOutcome(
                    metrics_to_watch=[
                        "median_leadtime",
                        "p85_leadtime",
                        "features_over_60_days",
                    ],
                    leading_indicators=[
                        "Story splitting patterns improve",
                        "Refinement cycle time reduces",
                    ],
                    lagging_indicators=[
                        "Median lead time reduces to <21 days",
                        "Features >60 days reduces to <10%",
                        "Flow efficiency improves by 30%+",
                    ],
                    timeline="2-3 PIs",
                    risks=[
                        "Teams may initially push back on smaller batches",
                        "Stakeholders may resist incremental delivery",
                    ],
                ),
                metric_references=[
                    "leadtime_distribution",
                    "batch_size_metrics",
                ],
                evidence=[
                    f"Small features (≤21d): {small} ({small/total*100:.0f}%)",
                    f"Medium features (21-60d): {medium} ({medium/total*100:.0f}%)",
                    f"Large features (>60d): {large} ({large_pct:.0f}%)",
                    f"Median: {median_lt:.0f}d, P85: {p85_lt:.0f}d, P95: {p95_lt:.0f}d",
                ],
                status="active",
                created_at=datetime.now(),
            )
        )

    return insights


def _format_scope(
    selected_arts: Optional[List[str]], selected_pis: Optional[List[str]]
) -> str:
    """Format scope description from filters"""
    parts = []
    if selected_arts:
        if len(selected_arts) == 1:
            parts.append(f"ART: {selected_arts[0]}")
        else:
            parts.append(f"{len(selected_arts)} ARTs")
    else:
        parts.append("Portfolio")

    if selected_pis:
        if len(selected_pis) == 1:
            parts.append(f"PI: {selected_pis[0]}")
        elif len(selected_pis) <= 3:
            parts.append(f"PIs: {', '.join(selected_pis)}")
        else:
            parts.append(f"{len(selected_pis)} PIs")

    return " | ".join(parts) if parts else "Portfolio"
