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

    # 2. Waste Analysis Insights
    insights.extend(_analyze_waste(waste, selected_arts, selected_pis))

    # 3. Planning Accuracy Insights
    insights.extend(_analyze_planning_accuracy(planning, selected_arts, selected_pis))

    # 4. Flow Efficiency Insights
    insights.extend(
        _analyze_flow_efficiency(art_comparison, selected_arts, selected_pis)
    )

    # 5. Throughput & Delivery Pattern Insights
    insights.extend(_analyze_throughput(throughput, selected_arts, selected_pis))

    # 6. Lead Time Variability Insights
    insights.extend(
        _analyze_leadtime_variability(leadtime, selected_arts, selected_pis)
    )

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
        mean_days = float(top_bottleneck.get("mean_days", 0) or 0)
        median_days = float(top_bottleneck.get("median_days", 0) or 0)
        p85_days = float(top_bottleneck.get("p85_days", 0) or 0)

        if score > 50:  # Significant bottleneck
            scope_desc = _format_scope(selected_arts, selected_pis)

            insights.append(
                InsightResponse(
                    id=0,
                    title=f"Critical Bottleneck in {stage_name.replace('_', ' ').title()} Stage",
                    severity="critical" if score > 70 else "warning",
                    confidence=0.9,
                    scope=scope_desc,
                    scope_id=None,
                    observation=f"The {stage_name.replace('_', ' ')} stage has a bottleneck score of {score:.1f}, with an average of {mean_days:.1f} days (85th percentile: {p85_days:.1f} days).",
                    interpretation=f"Features are spending excessive time in {stage_name.replace('_', ' ')}. The high variability (median: {median_days:.1f} vs p85: {p85_days:.1f}) indicates inconsistent process execution.",
                    root_causes=[
                        RootCause(
                            description="Limited resource capacity or availability",
                            evidence=[
                                f"Mean duration ({mean_days:.1f} days) significantly higher than median ({median_days:.1f} days)",
                                f"High 85th percentile ({p85_days:.1f} days) shows severe outliers",
                            ],
                            confidence=0.85,
                            reference=f"{stage_name} stage metrics",
                        ),
                        RootCause(
                            description="Process inefficiencies or unclear handoffs",
                            evidence=[
                                f"Bottleneck score of {score:.1f} indicates systemic issues",
                                "High variability suggests ad-hoc handling",
                            ],
                            confidence=0.75,
                            reference="Workflow stage analysis",
                        ),
                    ],
                    recommended_actions=[
                        Action(
                            timeframe="immediate",
                            description=f"Analyze top 10 features stuck in {stage_name.replace('_', ' ')} to identify common blockers",
                            owner="delivery_manager",
                            effort="2-4 hours",
                            dependencies=[],
                            success_signal=f"Root cause identified for >50% of delayed features in {stage_name}",
                        ),
                        Action(
                            timeframe="short_term",
                            description=f"Implement WIP limits for {stage_name.replace('_', ' ')} stage (recommended: 5-10 items)",
                            owner="scrum_master",
                            effort="1 week",
                            dependencies=["Team agreement on WIP limits"],
                            success_signal=f"Reduced mean time in {stage_name} by 20%",
                        ),
                        Action(
                            timeframe="medium_term",
                            description="Add dedicated resources or cross-train team members for this stage",
                            owner="engineering_manager",
                            effort="2-4 weeks",
                            dependencies=["Budget approval", "Training materials"],
                            success_signal=f"85th percentile time reduced to <{p85_days * 0.7:.1f} days",
                        ),
                    ],
                    expected_outcomes=ExpectedOutcome(
                        metrics_to_watch=[
                            f"{stage_name}_mean_days",
                            f"{stage_name}_p85_days",
                            "overall_lead_time",
                        ],
                        leading_indicators=[
                            "WIP count trending down",
                            "Cycle time stabilizing",
                        ],
                        lagging_indicators=[
                            "Mean time in stage reduced by 25%",
                            "Variability decreased",
                        ],
                        timeline="4-8 weeks",
                        risks=[
                            "Team resistance to WIP limits",
                            "Initial productivity dip during process changes",
                        ],
                    ),
                    metric_references=[
                        f"{stage_name}_bottleneck_score",
                        f"{stage_name}_mean_days",
                        f"{stage_name}_p85_days",
                    ],
                    evidence=[
                        f"Bottleneck score: {score:.1f}",
                        f"Mean duration: {mean_days:.1f} days",
                        f"85th percentile: {p85_days:.1f} days",
                    ],
                    status="active",
                    created_at=datetime.now(),
                )
            )

    # Multiple bottlenecks
    if len(sorted_bottlenecks) >= 3:
        top_3 = sorted_bottlenecks[:3]
        if all(b.get("bottleneck_score", 0) > 40 for b in top_3):
            stage_names = [b.get("stage", "").replace("_", " ").title() for b in top_3]
            total_days = sum(b.get("mean_days", 0) for b in top_3)

            insights.append(
                InsightResponse(
                    id=0,
                    title="Multiple Workflow Bottlenecks Detected",
                    severity="warning",
                    confidence=0.85,
                    scope=_format_scope(selected_arts, selected_pis),
                    scope_id=None,
                    observation=f"Three stages showing bottleneck behavior: {', '.join(stage_names)}. Combined average time: {total_days:.1f} days.",
                    interpretation="Multiple bottlenecks indicate systemic workflow issues rather than isolated problems. The entire delivery pipeline needs optimization.",
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
