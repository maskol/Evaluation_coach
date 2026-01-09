"""
Little's Law Analyzer Node

This node analyzes flow metrics using Little's Law to provide insights about:
- Work in Progress (WIP) levels
- Throughput rates
- Lead time optimization
- Flow efficiency

Little's Law: L = λ × W
Where:
- L = Average WIP (Work in Progress)
- λ = Throughput (rate of completion)
- W = Average Lead Time (cycle time)

Enhanced with expert agile coach LLM analysis and RAG
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.leadtime_service import LeadTimeService
from agents.state import AgentState

# Global LLM service for RAG enhancement (injected from main.py)
_llm_service = None


def set_llm_service(llm_service):
    """Set the LLM service for expert RAG enhancement"""
    global _llm_service
    _llm_service = llm_service
    print("🤖 Little's Law analyzer: LLM service configured for RAG enhancement")


def littles_law_analyzer_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyze flow metrics using Little's Law.

    This node:
    1. Retrieves lead time data from the DL Webb App API
    2. Calculates Little's Law metrics (L, λ, W)
    3. Analyzes flow efficiency
    4. Identifies WIP optimization opportunities
    5. Generates actionable recommendations

    Args:
        state: Current agent state with metrics and data

    Returns:
        Updated state with Little's Law analysis results
    """
    print("\n" + "=" * 80)
    print("🔬 LITTLE'S LAW ANALYZER NODE")
    print("=" * 80)

    updates = {
        "littles_law_analysis_timestamp": datetime.utcnow(),
        "littles_law_insights": [],
        "littles_law_metrics": None,
    }

    try:
        # Initialize LeadTime service
        leadtime_service = LeadTimeService()

        if not leadtime_service.is_available():
            print("⚠️  LeadTime service not available - skipping Little's Law analysis")
            updates["warnings"] = [
                "LeadTime service unavailable - Little's Law analysis skipped"
            ]
            return updates

        # Determine which PI to analyze
        pi_to_analyze = _determine_pi_to_analyze(state, leadtime_service)

        if not pi_to_analyze:
            print("⚠️  No PI identified for analysis")
            updates["warnings"] = [
                "No PI could be determined for Little's Law analysis"
            ]
            return updates

        print(f"📊 Analyzing PI: {pi_to_analyze}")

        # Get flow data for the PI
        flow_data = leadtime_service.get_feature_leadtime_data(pi=pi_to_analyze)

        if not flow_data:
            print(f"⚠️  No flow data available for PI {pi_to_analyze}")
            updates["warnings"] = [f"No flow data available for PI {pi_to_analyze}"]
            return updates

        print(f"✅ Retrieved {len(flow_data)} features for flow analysis")

        # Get PI planning data (pip_data)
        print(f"📋 Fetching PI planning data for {pi_to_analyze}...")
        pip_data = leadtime_service.client.get_pip_data(pi=pi_to_analyze)

        if pip_data:
            print(f"✅ Retrieved {len(pip_data)} planning records")
        else:
            print("⚠️  No planning data available")

        # Get planning accuracy analysis
        print("🎯 Fetching planning accuracy metrics...")
        planning_accuracy = leadtime_service.get_planning_accuracy(pis=[pi_to_analyze])

        if planning_accuracy and not planning_accuracy.get("error"):
            print("✅ Planning accuracy metrics retrieved")
        else:
            print("⚠️  Planning accuracy metrics unavailable")

        # Calculate Little's Law metrics
        metrics = _calculate_littles_law_metrics(flow_data, pi_to_analyze)

        if not metrics:
            print("⚠️  Insufficient data for Little's Law calculation")
            updates["warnings"] = [
                "Insufficient data for meaningful Little's Law analysis"
            ]
            return updates

        # Calculate planning metrics
        planning_metrics = _calculate_planning_metrics(
            pip_data, planning_accuracy, pi_to_analyze
        )

        # Combine metrics
        combined_metrics = {**metrics, **planning_metrics}
        updates["littles_law_metrics"] = combined_metrics
        print("📈 Little's Law Metrics:")
        print(f"   • Throughput (λ): {metrics['throughput_per_day']:.2f} features/day")
        print(f"   • Lead Time (W): {metrics['avg_leadtime']:.1f} days")
        print(f"   • Predicted WIP (L): {metrics['predicted_wip']:.1f} features")
        print(f"   • Flow Efficiency: {metrics['flow_efficiency']:.1f}%")

        if planning_metrics.get("total_planned"):
            print("\n📋 Planning Metrics:")
            print(
                f"   • Planning Accuracy: {planning_metrics.get('planning_accuracy', 0):.1f}%"
            )
            print(f"   • Committed: {planning_metrics.get('committed_count', 0)}")
            print(f"   • Uncommitted: {planning_metrics.get('uncommitted_count', 0)}")
            print(
                f"   • Added Post-Planning: {planning_metrics.get('post_planning_count', 0)}"
            )

        # Generate insights using combined data
        insights = _generate_comprehensive_insights(
            state, combined_metrics, pi_to_analyze
        )

        if insights:
            updates["littles_law_insights"] = insights
            print(f"\n✅ Generated {len(insights)} Little's Law insights")

            # Add to reasoning chain
            updates["reasoning_chain"] = [
                f"Applied Little's Law analysis for PI {pi_to_analyze}",
                f"Identified WIP optimization opportunity: {metrics['wip_reduction']:.1f} features",
                f"Flow efficiency at {metrics['flow_efficiency']:.1f}% indicates {'high' if metrics['flow_efficiency'] < 50 else 'moderate'} waste",
            ]

        print("\n" + "=" * 80)
        print("✅ LITTLE'S LAW ANALYSIS COMPLETE")
        print("=" * 80 + "\n")

        return updates

    except Exception as exc:  # pylint: disable=broad-except
        print("\n❌ Error in Little's Law analysis")
        import traceback

        traceback.print_exc()

        updates["errors"] = [f"Little's Law analysis failed: {str(exc)}"]
        return updates


def _determine_pi_to_analyze(
    state: AgentState, leadtime_service: LeadTimeService
) -> Optional[str]:
    """
    Determine which PI to analyze based on scope and available data.

    Priority:
    1. If scope_id is a PI identifier, use that
    2. If analyzing portfolio, use the most recent PI
    3. Extract PI from time window
    """
    scope_id = state.get("scope_id")
    scope_type = state.get("scope_type", "").lower()

    # If scope_id looks like a PI (e.g., "24Q4", "21Q3"), use it
    if scope_id and _is_pi_identifier(scope_id):
        return scope_id

    # For portfolio scope, get most recent PI
    if scope_type == "portfolio" or scope_type == "pi":
        try:
            filters = leadtime_service.client.get_available_filters()
            pis = filters.get("pis", [])
            if pis:
                # Return most recent PI (assuming sorted)
                sorted_pis = sorted(pis, reverse=True)
                return sorted_pis[0] if sorted_pis else None
        except Exception:  # pylint: disable=broad-except
            print("⚠️  Could not retrieve PI list")

    # Try to extract from program_increments in state
    pis = state.get("program_increments", [])
    if pis:
        # Use the most recent PI
        return getattr(pis[0], "pi_name", None) or getattr(pis[0], "name", None)

    return None


def _is_pi_identifier(value: str) -> bool:
    """Check if a string looks like a PI identifier (e.g., 24Q4, 2024Q1)."""
    import re

    # Match patterns like: 24Q4, 2024Q1, 21Q3, etc.
    pattern = r"^\d{2,4}Q[1-4]$"
    return bool(re.match(pattern, value))


def _calculate_littles_law_metrics(
    flow_data: List[dict], pi: str, pi_duration_days: int = 84
) -> Optional[Dict[str, Any]]:
    """
    Calculate Little's Law metrics from flow data.

    Args:
        flow_data: List of features with lead time data
        pi: Program Increment identifier
        pi_duration_days: Duration of PI in days (default 84 = 6 weeks)

    Returns:
        Dictionary with calculated metrics or None if insufficient data
    """
    # Filter completed features
    completed_features = [
        f
        for f in flow_data
        if f.get("status") in ["Done", "Deployed", "Completed"]
        and f.get("total_leadtime", 0) > 0
    ]

    if len(completed_features) < 5:  # Minimum threshold for meaningful analysis
        return None

    # Calculate W: Average Lead Time (days)
    lead_times = [f["total_leadtime"] for f in completed_features]
    avg_leadtime = sum(lead_times) / len(lead_times)
    max_leadtime = max(lead_times)
    min_leadtime = min(lead_times)

    # Calculate standard deviation for variability
    mean_sq_diff = sum((lt - avg_leadtime) ** 2 for lt in lead_times) / len(lead_times)
    leadtime_stddev = mean_sq_diff**0.5

    # Calculate λ: Throughput (features per day)
    total_features = len(completed_features)
    throughput_per_day = total_features / pi_duration_days

    # Calculate L: Predicted WIP using Little's Law (L = λ × W)
    predicted_wip = throughput_per_day * avg_leadtime

    # Calculate actual active time (time in active work states)
    active_times = []
    for f in completed_features:
        active_time = (
            f.get("in_progress", 0)
            + f.get("in_analysis", 0)
            + f.get("in_reviewing", 0)
            + f.get("in_development", 0)
            + f.get("in_test", 0)
        )
        active_times.append(active_time)

    avg_active_time = (
        sum(active_times) / len(active_times) if active_times else avg_leadtime
    )
    avg_wait_time = avg_leadtime - avg_active_time

    # Calculate flow efficiency (% of time in active work)
    flow_efficiency = (avg_active_time / avg_leadtime * 100) if avg_leadtime > 0 else 0

    # Calculate stage-level metrics for WIP mapping
    stage_names = [
        "in_analysis",
        "in_backlog",
        "in_planned",
        "in_progress",
        "ready_for_sit",
        "in_sit",
        "ready_for_uat",
        "in_uat",
        "ready_for_deployment",
        "in_deployment",
    ]

    stage_metrics = {}
    for stage in stage_names:
        # Calculate average time in each stage
        stage_times = [
            f.get(stage, 0) for f in completed_features if f.get(stage, 0) > 0
        ]
        if stage_times:
            avg_stage_time = sum(stage_times) / len(stage_times)
            # Calculate WIP for this stage using Little's Law
            stage_wip = throughput_per_day * avg_stage_time
            stage_metrics[stage] = {
                "avg_time": avg_stage_time,
                "predicted_wip": stage_wip,
                "recommended_limit": max(1, round(stage_wip * 1.2)),  # 20% buffer
            }

    # Calculate optimal WIP for target lead time of 30 days
    target_leadtime = 30
    optimal_wip = throughput_per_day * target_leadtime
    wip_reduction = predicted_wip - optimal_wip

    # Determine severity
    if avg_leadtime > 60 or flow_efficiency < 30:
        severity = "critical"
    elif avg_leadtime > 45 or flow_efficiency < 40:
        severity = "warning"
    elif avg_leadtime > 30 or flow_efficiency < 50:
        severity = "info"
    else:
        severity = "success"

    return {
        "pi": pi,
        "total_features": total_features,
        "pi_duration_days": pi_duration_days,
        # Little's Law components
        "throughput_per_day": throughput_per_day,  # λ
        "avg_leadtime": avg_leadtime,  # W
        "predicted_wip": predicted_wip,  # L
        # Variability metrics
        "leadtime_stddev": leadtime_stddev,
        "leadtime_min": min_leadtime,
        "leadtime_max": max_leadtime,
        # Flow efficiency
        "avg_active_time": avg_active_time,
        "avg_wait_time": avg_wait_time,
        "flow_efficiency": flow_efficiency,
        # Stage-level WIP mapping
        "stage_metrics": stage_metrics,
        # Optimization targets
        "target_leadtime": target_leadtime,
        "optimal_wip": optimal_wip,
        "wip_reduction": wip_reduction,
        # Assessment
        "severity": severity,
        "confidence": 88.0,
    }


def _calculate_planning_metrics(
    pip_data: List[dict], planning_accuracy_data: Dict[str, Any], pi: str
) -> Dict[str, Any]:
    """
    Calculate planning and commitment metrics from pip_data.

    Analyzes:
    - Committed vs uncommitted features
    - Features added after PI planning
    - Planning accuracy
    - Delivery success rates
    - Reasons for missed deliveries

    Args:
        pip_data: PI planning data from get_pip_data()
        planning_accuracy_data: Planning accuracy analysis
        pi: Program Increment identifier

    Returns:
        Dictionary with planning metrics
    """
    if not pip_data:
        return {
            "total_planned": 0,
            "committed_count": 0,
            "uncommitted_count": 0,
            "post_planning_count": 0,
            "planning_accuracy": 0,
            "delivered_committed": 0,
            "missed_committed": 0,
        }

    # Analyze pip_data records
    committed = []
    uncommitted = []
    post_planning = []
    delivered_committed = []
    missed_committed = []

    for item in pip_data:
        planned_committed = item.get("planned_committed", 0)
        planned_uncommitted = item.get("planned_uncommitted", 0)
        plc_delivery = item.get("plc_delivery", 0)

        # Categorize items
        if planned_committed == 1:
            committed.append(item)
            if plc_delivery == 1:
                delivered_committed.append(item)
            else:
                missed_committed.append(item)
        elif planned_uncommitted == 1:
            uncommitted.append(item)
        elif planned_committed == 0 and planned_uncommitted == 0:
            # Item added after planning
            post_planning.append(item)

    # Calculate percentages
    total_planned = len(committed) + len(uncommitted)
    committed_count = len(committed)
    uncommitted_count = len(uncommitted)
    post_planning_count = len(post_planning)

    # Planning accuracy (from committed items)
    planning_accuracy = 0
    if committed_count > 0:
        planning_accuracy = (len(delivered_committed) / committed_count) * 100

    # Extract overall planning accuracy if available
    overall_accuracy = planning_accuracy_data.get(
        "overall_planning_accuracy", planning_accuracy
    )
    if isinstance(overall_accuracy, dict):
        overall_accuracy = overall_accuracy.get("accuracy", planning_accuracy)

    # Analyze reasons for missed deliveries
    missed_reasons = _analyze_missed_deliveries(missed_committed, pip_data)

    # Determine severity based on planning accuracy
    if planning_accuracy < 60 or post_planning_count > committed_count * 0.3:
        severity = "critical"
    elif planning_accuracy < 75 or post_planning_count > committed_count * 0.2:
        severity = "warning"
    elif planning_accuracy < 85 or post_planning_count > committed_count * 0.1:
        severity = "info"
    else:
        severity = "success"

    return {
        "pi": pi,
        "total_planned": total_planned,
        "committed_count": committed_count,
        "uncommitted_count": uncommitted_count,
        "post_planning_count": post_planning_count,
        "delivered_committed_count": len(delivered_committed),
        "missed_committed_count": len(missed_committed),
        "planning_accuracy": planning_accuracy,
        "overall_planning_accuracy": overall_accuracy,
        "committed_percentage": (
            (committed_count / total_planned * 100) if total_planned > 0 else 0
        ),
        "uncommitted_percentage": (
            (uncommitted_count / total_planned * 100) if total_planned > 0 else 0
        ),
        "post_planning_percentage": (
            (post_planning_count / (total_planned + post_planning_count) * 100)
            if (total_planned + post_planning_count) > 0
            else 0
        ),
        "planning_severity": severity,
        "missed_reasons": missed_reasons,
        "delivered_committed_items": [
            item.get("issue_key") for item in delivered_committed[:10]
        ],
        "missed_committed_items": [
            item.get("issue_key") for item in missed_committed[:10]
        ],
    }


def _analyze_missed_deliveries(
    missed_items: List[dict], all_pip_data: List[dict]
) -> Dict[str, Any]:
    """
    Analyze reasons why committed items were not delivered.

    Looks for patterns in missed deliveries to identify root causes.
    """
    if not missed_items:
        return {
            "total_missed": 0,
            "reasons": [],
        }

    # Common patterns to look for
    reasons = []

    total_missed = len(missed_items)

    # Group by ART to see if specific ARTs have issues
    art_misses = {}
    for item in missed_items:
        art = item.get("art", "Unknown")
        art_misses[art] = art_misses.get(art, 0) + 1

    # Identify ARTs with high miss rates
    if art_misses:
        max_misses = max(art_misses.values())
        problematic_arts = [
            art for art, count in art_misses.items() if count >= max_misses * 0.5
        ]

        if problematic_arts:
            reasons.append(
                {
                    "category": "ART Performance",
                    "description": f"ARTs with high miss rates: {', '.join(problematic_arts)}",
                    "impact": "high",
                    "count": sum(art_misses[art] for art in problematic_arts),
                }
            )

    # If more than 30% of committed items missed, it's a systematic issue
    all_committed = [
        item for item in all_pip_data if item.get("planned_committed") == 1
    ]
    if all_committed:
        miss_rate = (total_missed / len(all_committed)) * 100
        if miss_rate > 30:
            reasons.append(
                {
                    "category": "Systematic Planning Issue",
                    "description": f"High miss rate ({miss_rate:.1f}%) indicates over-commitment or capacity issues",
                    "impact": "critical",
                    "count": total_missed,
                }
            )
        elif miss_rate > 20:
            reasons.append(
                {
                    "category": "Capacity Planning",
                    "description": f"Miss rate of {miss_rate:.1f}% suggests capacity estimation problems",
                    "impact": "high",
                    "count": total_missed,
                }
            )

    # Default reason if no specific patterns found
    if not reasons:
        reasons.append(
            {
                "category": "Delivery Execution",
                "description": "Committed items not delivered - requires detailed investigation",
                "impact": "medium",
                "count": total_missed,
            }
        )

    return {
        "total_missed": total_missed,
        "miss_rate": (total_missed / len(all_committed) * 100) if all_committed else 0,
        "reasons": reasons,
        "art_breakdown": art_misses,
    }


def _generate_comprehensive_insights(
    _state: AgentState, metrics: Dict[str, Any], pi: str
) -> List[Dict[str, Any]]:
    """
    Generate comprehensive insights combining Little's Law and planning analysis.

    Includes:
    - Flow metrics (WIP, throughput, lead time)
    - Planning accuracy
    - Commitment levels
    - Reasons for missed deliveries

    Enhanced with RAG for richer expert analysis.
    """
    insights = []

    # Prepare context for RAG enhancement
    rag_context = {"metrics": metrics, "pi": pi}

    # Generate flow insights (Little's Law)
    flow_insight = _generate_flow_insight(metrics, pi)
    if flow_insight:
        # Enhance with RAG if available
        flow_insight = _enhance_insight_with_rag(flow_insight, rag_context)
        insights.append(flow_insight)

    # Generate planning accuracy insight
    if metrics.get("total_planned", 0) > 0:
        planning_insight = _generate_planning_insight(metrics, pi)
        if planning_insight:
            # Enhance with RAG if available
            planning_insight = _enhance_insight_with_rag(planning_insight, rag_context)
            insights.append(planning_insight)

    # Generate commitment analysis insight
    if metrics.get("committed_count", 0) > 0:
        commitment_insight = _generate_commitment_insight(metrics, pi)
        if commitment_insight:
            # Enhance with RAG if available
            commitment_insight = _enhance_insight_with_rag(
                commitment_insight, rag_context
            )
            insights.append(commitment_insight)

    return insights


def _format_stage_metrics(stage_metrics: Dict[str, Any]) -> str:
    """Format stage metrics for prompt display."""
    if not stage_metrics:
        return "No stage-level data available"

    lines = []
    for stage, data in stage_metrics.items():
        stage_name = stage.replace("_", " ").title()
        lines.append(
            f"  • {stage_name}: {data['avg_time']:.1f} days avg, "
            f"WIP={data['predicted_wip']:.1f}, Limit ≤{data['recommended_limit']}"
        )
    return "\n".join(lines) if lines else "No stage data"


def _enhance_insight_with_rag(
    insight: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhance Little's Law insight with expert agile coach analysis using RAG.

    Args:
        insight: Base insight generated from templates
        context: Additional context (metrics, PI, etc.)

    Returns:
        Enhanced insight with richer observations and recommendations
    """
    if not _llm_service:
        print("⚠️  No LLM service available - returning template insight")
        return insight

    try:
        print(f"🤖 Enhancing insight with RAG: {insight['title']}")

        # Build context for LLM
        metrics = context.get("metrics", {})
        pi = context.get("pi", "Unknown")

        # Create a rich prompt for the LLM with scenario modeling format
        prompt = f"""You are an expert Agile coach with 15+ years of experience analyzing flow metrics using Little's Law.

**Current Insight:**
Title: {insight['title']}
Observation: {insight['observation']}
Interpretation: {insight['interpretation']}

**Flow Metrics (Little's Law Analysis):**
- PI: {pi}
- Throughput (λ): {metrics.get('throughput_per_day', 0):.2f} features/day
- Average Lead Time (W): {metrics.get('avg_leadtime', 0):.1f} days
- Predicted WIP (L): {metrics.get('predicted_wip', 0):.1f} features
- Flow Efficiency: {metrics.get('flow_efficiency', 0):.1f}%
- Active Time: {metrics.get('avg_active_time', 0):.1f} days
- Wait Time: {metrics.get('avg_wait_time', 0):.1f} days
- Total Features: {metrics.get('total_features', 0)}
- Lead Time Std Dev: {metrics.get('leadtime_stddev', 0):.1f} days
- Lead Time Range: {metrics.get('leadtime_min', 0):.1f}-{metrics.get('leadtime_max', 0):.1f} days

**Stage-Level Breakdown:**
{_format_stage_metrics(metrics.get('stage_metrics', dict()))}

**Planning Metrics:**
- Planning Accuracy: {metrics.get('planning_accuracy', 0):.1f}%
- Committed Features: {metrics.get('committed_count', 0)}
- Uncommitted Features: {metrics.get('uncommitted_count', 0)}
- Post-Planning Additions: {metrics.get('post_planning_count', 0)}
- Delivered Committed: {metrics.get('delivered_committed_count', 0)}
- Missed Committed: {metrics.get('missed_committed_count', 0)}

**Task:**
Provide a comprehensive Little's Law analysis in the following format:

1. **Scenario Modeling** - Create 2-3 throughput scenarios (e.g., current, improved, degraded) showing:
   - WIP = Throughput × Lead Time calculations
   - Impact on lead time if WIP changes
   - Practical interpretation for each scenario

2. **Stage-Level WIP Mapping** - If process stages are known, break down WIP by stage:
   - Calculate WIP per stage proportional to time spent
   - Suggest WIP limits per stage (e.g., "In Progress ≤ 4 Features")
   - Show how stage-level constraints affect total system WIP

3. **Impact Analysis** - Show "what happens if" scenarios:
   - Table showing WIP increases vs resulting lead time
   - Break-even points and tipping points
   - Risk zones and optimal operating ranges

4. **Flow Control Rules** - Provide actionable policies:
   - Hard WIP limits (non-negotiable, with specific numbers)
   - Aging signals (e.g., "Any feature > 1.5× target days → escalation")
   - Escalation triggers and governance rules

5. **SAFe-Specific Context** - Connect to SAFe practices:
   - How this affects PI planning capacity
   - Team maturity indicators
   - RTE/PM talking points with mathematical justification
   - Common anti-patterns observed in the data

Focus on:
- Little's Law relationships (L = λ × W) with concrete calculations
- Multiple scenarios showing sensitivity to changes
- Specific numeric recommendations (not vague guidance)
- Tables and structured data where helpful
- Making lead time predictable through WIP control
- Preventing PI overcommitment with math-based evidence

Be specific, insightful, and actionable. Reference actual numbers from the metrics. Use scenario modeling to show teams the consequences of their choices."""

        # Get enhanced analysis from LLM with RAG
        enhanced_text = _llm_service.enhance_insight_with_expert_analysis(
            insight_data=prompt, insight_type="littles_law_flow_analysis"
        )

        if enhanced_text and len(enhanced_text) > 100:
            # Parse the enhanced text and update the insight
            # For now, append the enhanced analysis to the interpretation
            insight["interpretation"] = (
                f"{insight['interpretation']}\n\n**Expert Analysis:** {enhanced_text}"
            )
            print("✅ Insight enhanced with RAG")
        else:
            print("⚠️  RAG enhancement returned minimal content")

    except Exception as e:
        print(f"⚠️  RAG enhancement failed: {e}")
        # Return original insight if enhancement fails

    return insight


def _generate_flow_insight(
    metrics: Dict[str, Any], pi: str
) -> Optional[Dict[str, Any]]:
    """Generate Little's Law flow optimization insight."""

    # Build observation
    observation_parts = [
        f"PI {pi} completed {metrics['total_features']} features in {metrics['pi_duration_days']} days.",
        f"Throughput (λ) = {metrics['throughput_per_day']:.2f} features/day.",
        f"Average Lead Time (W) = {metrics['avg_leadtime']:.1f} days (range: {metrics['leadtime_min']:.1f}-{metrics['leadtime_max']:.1f}).",
        f"Predicted WIP (L) = {metrics['predicted_wip']:.1f} features.",
        f"Flow Efficiency = {metrics['flow_efficiency']:.1f}% (active work time / total lead time).",
    ]

    # Build interpretation
    interpretation_parts = []

    if metrics["flow_efficiency"] < 40:
        interpretation_parts.append(
            f"Low flow efficiency ({metrics['flow_efficiency']:.1f}%) indicates features spend "
            f"{metrics['avg_wait_time']:.1f} days waiting vs {metrics['avg_active_time']:.1f} days in active work. "
            "This reveals significant waste due to queuing, dependencies, or blockers."
        )
    elif metrics["flow_efficiency"] < 60:
        interpretation_parts.append(
            f"Moderate flow efficiency ({metrics['flow_efficiency']:.1f}%) shows room for improvement. "
            f"Features wait {metrics['avg_wait_time']:.1f} days on average."
        )
    else:
        interpretation_parts.append(
            f"Good flow efficiency ({metrics['flow_efficiency']:.1f}%) indicates relatively smooth flow."
        )

    if metrics["avg_leadtime"] > 45:
        interpretation_parts.append(
            f"Average lead time of {metrics['avg_leadtime']:.1f} days exceeds best practice (30-45 days). "
            "Reducing WIP is the most effective lever for improving lead time."
        )

    if metrics["wip_reduction"] > 2:
        interpretation_parts.append(
            f"To achieve 30-day lead time while maintaining current throughput, "
            f"reduce WIP from {metrics['predicted_wip']:.1f} to {metrics['optimal_wip']:.1f} features "
            f"({metrics['wip_reduction']:.1f} feature reduction)."
        )

    # Root causes
    root_causes = []

    if metrics["flow_efficiency"] < 50:
        root_causes.append(
            {
                "description": f"High wait time ({metrics['avg_wait_time']:.1f} days) caused by bottlenecks, dependencies, or blocked work",
                "evidence": [
                    f"flow_efficiency_{metrics['flow_efficiency']:.0f}pct",
                    f"avg_wait_time_{metrics['avg_wait_time']:.1f}days",
                ],
                "confidence": 90.0,
                "reference": "littles_law_flow_analysis",
            }
        )

    if metrics["predicted_wip"] > 10:
        root_causes.append(
            {
                "description": "Excessive WIP causes context switching, delays, and increased cycle time",
                "evidence": [
                    f"predicted_wip_{metrics['predicted_wip']:.1f}",
                    f"optimal_wip_{metrics['optimal_wip']:.1f}",
                ],
                "confidence": 85.0,
                "reference": "littles_law_wip_analysis",
            }
        )

    if metrics["leadtime_stddev"] > metrics["avg_leadtime"] * 0.5:
        root_causes.append(
            {
                "description": "High lead time variability indicates unpredictable flow and potential process issues",
                "evidence": [
                    f"leadtime_stddev_{metrics['leadtime_stddev']:.1f}",
                    f"leadtime_range_{metrics['leadtime_min']:.1f}_to_{metrics['leadtime_max']:.1f}",
                ],
                "confidence": 75.0,
                "reference": "littles_law_variability_analysis",
            }
        )

    # Recommended actions
    actions = []

    if metrics["wip_reduction"] > 2:
        actions.append(
            {
                "timeframe": "short-term",
                "description": f"Implement strict WIP limits: cap active features at {metrics['optimal_wip']:.0f} per team/ART",
                "owner": "Scrum Masters & Product Owners",
                "effort": "Low",
                "dependencies": ["Team agreement on WIP policy"],
                "success_signal": f"WIP reduced to {metrics['optimal_wip']:.0f}, lead time trending toward 30 days within 1 PI",
            }
        )

    if metrics["flow_efficiency"] < 50:
        actions.append(
            {
                "timeframe": "medium-term",
                "description": "Conduct value stream mapping to identify and eliminate wait time sources (blockers, dependencies, handoffs)",
                "owner": "ART Leadership & RTEs",
                "effort": "Medium",
                "dependencies": ["VSM workshop", "Cross-team coordination"],
                "success_signal": "Flow efficiency improves to >50% within 2 PIs",
            }
        )

    if metrics["leadtime_stddev"] > metrics["avg_leadtime"] * 0.4:
        actions.append(
            {
                "timeframe": "medium-term",
                "description": "Standardize feature sizing and decomposition to reduce lead time variability",
                "owner": "Product Management & Architects",
                "effort": "Medium",
                "dependencies": [
                    "Feature sizing guidelines",
                    "Story splitting patterns",
                ],
                "success_signal": "Lead time standard deviation reduced by 30%",
            }
        )

    actions.append(
        {
            "timeframe": "ongoing",
            "description": f"Monitor Little's Law dashboard weekly: track λ={metrics['throughput_per_day']:.2f}/day, W→30 days, L={metrics['optimal_wip']:.0f}",
            "owner": "RTE & Scrum Masters",
            "effort": "Low",
            "dependencies": ["Metrics dashboard", "Weekly review ritual"],
            "success_signal": "Consistent delivery with W≤30 days and stable throughput",
        }
    )

    # Create the main insight
    main_insight = {
        "title": f"Little's Law Analysis: PI {pi} Flow Optimization",
        "severity": metrics["severity"],
        "confidence": metrics["confidence"],
        "scope": "pi",
        "scope_id": pi,
        "observation": " ".join(observation_parts),
        "interpretation": " ".join(interpretation_parts),
        "root_causes": (
            root_causes
            if root_causes
            else [
                {
                    "description": "Systematic flow analysis using Little's Law (L = λ × W)",
                    "evidence": ["flow_leadtime_data"],
                    "confidence": 88.0,
                    "reference": "littles_law_formula",
                }
            ]
        ),
        "recommended_actions": actions,
        "expected_outcomes": {
            "metrics_to_watch": [
                "Average Lead Time (W)",
                "Throughput (λ)",
                "WIP (L)",
                "Flow Efficiency",
            ],
            "leading_indicators": [
                "Daily WIP count",
                "Blocked items count",
                "Features in progress",
            ],
            "lagging_indicators": [
                "Average lead time trend",
                "Flow efficiency trend",
                "Delivery predictability",
            ],
            "timeline": "1-2 PIs for significant improvement",
            "risks": [
                "Resistance to WIP limits",
                "Dependency management challenges",
            ],
        },
        "metric_references": [
            "littles_law",
            "flow_efficiency",
            "lead_time",
            "throughput",
        ],
        "evidence": [
            f"pi_{pi}_flow_data",
            "littles_law_calculation",
            f"{metrics['total_features']}_completed_features",
        ],
    }

    return main_insight


def _generate_planning_insight(
    metrics: Dict[str, Any], pi: str
) -> Optional[Dict[str, Any]]:
    """Generate planning accuracy and predictability insight."""

    planning_accuracy = metrics.get("planning_accuracy", 0)
    committed_count = metrics.get("committed_count", 0)
    uncommitted_count = metrics.get("uncommitted_count", 0)
    post_planning_count = metrics.get("post_planning_count", 0)
    delivered_count = metrics.get("delivered_committed_count", 0)
    missed_count = metrics.get("missed_committed_count", 0)

    # Build observation
    observation_parts = [
        f"PI {pi} planning data:",
        f"{committed_count} committed features, {uncommitted_count} uncommitted features.",
        f"{post_planning_count} features added after PI planning.",
        f"Planning accuracy: {planning_accuracy:.1f}% ({delivered_count} delivered, {missed_count} missed).",
    ]

    # Build interpretation
    interpretation_parts = []

    if planning_accuracy < 75:
        interpretation_parts.append(
            f"Low planning accuracy ({planning_accuracy:.1f}%) indicates systematic issues with "
            "capacity estimation or commitment discipline."
        )
    elif planning_accuracy < 85:
        interpretation_parts.append(
            f"Planning accuracy ({planning_accuracy:.1f}%) is below SAFe targets (>85%). "
            "This affects predictability and stakeholder confidence."
        )
    else:
        interpretation_parts.append(
            f"Good planning accuracy ({planning_accuracy:.1f}%) demonstrates reliable planning and execution."
        )

    # Analyze post-planning additions
    if post_planning_count > committed_count * 0.2:
        interpretation_parts.append(
            f"High post-planning additions ({post_planning_count} features, "
            f"{metrics.get('post_planning_percentage', 0):.1f}% of total) disrupt PI predictability."
        )

    # Analyze missed deliveries
    missed_reasons = metrics.get("missed_reasons", {})
    if missed_reasons.get("reasons"):
        top_reason = missed_reasons["reasons"][0]
        interpretation_parts.append(
            f"Primary reason for missed deliveries: {top_reason['description']}"
        )

    # Root causes
    root_causes = []

    if planning_accuracy < 75:
        root_causes.append(
            {
                "description": "Over-commitment: Team capacity not accurately estimated during PI planning",
                "evidence": [
                    f"planning_accuracy_{planning_accuracy:.0f}pct",
                    f"{missed_count}_missed_commitments",
                ],
                "confidence": 90.0,
                "reference": "planning_accuracy_analysis",
            }
        )

    if post_planning_count > committed_count * 0.15:
        root_causes.append(
            {
                "description": "Scope management: Excessive mid-PI additions reduce focus on committed work",
                "evidence": [
                    f"{post_planning_count}_post_planning_items",
                    f"post_planning_rate_{metrics.get('post_planning_percentage', 0):.0f}pct",
                ],
                "confidence": 85.0,
                "reference": "scope_management_analysis",
            }
        )

    # Add specific reasons from missed delivery analysis
    for reason in missed_reasons.get("reasons", [])[:2]:
        root_causes.append(
            {
                "description": reason["description"],
                "evidence": [
                    f"{reason['category']}_pattern",
                    f"{reason['count']}_items",
                ],
                "confidence": 80.0 if reason["impact"] == "high" else 70.0,
                "reference": "missed_delivery_analysis",
            }
        )

    # Recommended actions
    actions = []

    if planning_accuracy < 75:
        actions.append(
            {
                "timeframe": "short-term",
                "description": "Conduct PI retrospective to identify commitment vs. delivery gaps",
                "owner": "RTE & Scrum Masters",
                "effort": "Low",
                "dependencies": ["PI retrospective session"],
                "success_signal": f"Identify top 3 reasons for {missed_count} missed commitments",
            }
        )

        actions.append(
            {
                "timeframe": "medium-term",
                "description": "Implement capacity-based planning with historical velocity data",
                "owner": "Product Management & Teams",
                "effort": "Medium",
                "dependencies": ["Velocity tracking", "Capacity planning training"],
                "success_signal": "Planning accuracy improves to >80% in next PI",
            }
        )

    if post_planning_count > committed_count * 0.15:
        actions.append(
            {
                "timeframe": "short-term",
                "description": "Establish PI planning commitment discipline: limit mid-PI additions to emergencies only",
                "owner": "Product Management & Leadership",
                "effort": "Low",
                "dependencies": ["Management buy-in"],
                "success_signal": "Reduce post-planning additions by 50%",
            }
        )

    actions.append(
        {
            "timeframe": "ongoing",
            "description": "Track planning accuracy weekly and adjust commitments in real-time",
            "owner": "RTE",
            "effort": "Low",
            "dependencies": ["Weekly metrics review"],
            "success_signal": "Maintain planning accuracy >85% consistently",
        }
    )

    # Determine severity
    if planning_accuracy < 60 or post_planning_count > committed_count * 0.3:
        severity = "critical"
    elif planning_accuracy < 75 or post_planning_count > committed_count * 0.2:
        severity = "warning"
    elif planning_accuracy < 85 or post_planning_count > committed_count * 0.1:
        severity = "info"
    else:
        severity = "success"

    return {
        "title": f"PI {pi} Planning Accuracy & Predictability",
        "severity": severity,
        "confidence": 92.0,
        "scope": "pi",
        "scope_id": pi,
        "observation": " ".join(observation_parts),
        "interpretation": " ".join(interpretation_parts),
        "root_causes": (
            root_causes
            if root_causes
            else [
                {
                    "description": "Planning and commitment analysis based on PI planning data",
                    "evidence": ["pip_data"],
                    "confidence": 92.0,
                    "reference": "planning_accuracy_analysis",
                }
            ]
        ),
        "recommended_actions": actions,
        "expected_outcomes": {
            "metrics_to_watch": [
                "Planning Accuracy",
                "Committed vs Delivered",
                "Post-Planning Additions",
                "PI Predictability",
            ],
            "leading_indicators": [
                "Sprint-level commitment accuracy",
                "Mid-PI scope change requests",
                "Team velocity stability",
            ],
            "lagging_indicators": [
                "PI Objectives achievement",
                "Stakeholder confidence",
            ],
            "timeline": "1-2 PIs for improvement",
            "risks": [
                "Pressure to over-commit",
                "Emergency work disruption",
            ],
        },
        "metric_references": [
            "planning_accuracy",
            "pi_predictability",
            "scope_management",
        ],
        "evidence": [
            f"pi_{pi}_planning_data",
            f"{committed_count}_committed",
            f"{missed_count}_missed",
        ],
    }


def _generate_commitment_insight(
    metrics: Dict[str, Any], pi: str
) -> Optional[Dict[str, Any]]:
    """Generate commitment discipline and scope management insight."""

    committed_count = metrics.get("committed_count", 0)
    uncommitted_count = metrics.get("uncommitted_count", 0)
    total_planned = metrics.get("total_planned", 0)
    committed_pct = metrics.get("committed_percentage", 0)

    if total_planned == 0:
        return None

    # Build observation
    observation_parts = [
        f"PI {pi} commitment breakdown:",
        f"{committed_pct:.1f}% committed ({committed_count} features),",
        f"{100 - committed_pct:.1f}% uncommitted ({uncommitted_count} features).",
    ]

    # Build interpretation
    interpretation_parts = []

    if committed_pct < 70:
        interpretation_parts.append(
            f"Low commitment rate ({committed_pct:.1f}%) suggests teams lack confidence "
            "in their ability to deliver, indicating capacity or dependency issues."
        )
    elif committed_pct < 80:
        interpretation_parts.append(
            f"Commitment rate ({committed_pct:.1f}%) is below recommended 80-90%. "
            "This may indicate risk-averse planning or unclear priorities."
        )
    elif committed_pct > 95:
        interpretation_parts.append(
            f"Very high commitment rate ({committed_pct:.1f}%) leaves no buffer for "
            "emergencies or learning, risking lower planning accuracy."
        )
    else:
        interpretation_parts.append(
            f"Healthy commitment rate ({committed_pct:.1f}%) balances predictability with flexibility."
        )

    # Root causes
    root_causes = []

    if committed_pct < 75:
        root_causes.append(
            {
                "description": "Teams hesitant to commit due to past delivery challenges or unclear capacity",
                "evidence": [
                    f"commitment_rate_{committed_pct:.0f}pct",
                    f"{uncommitted_count}_uncommitted",
                ],
                "confidence": 85.0,
                "reference": "commitment_analysis",
            }
        )

    if committed_pct > 95:
        root_causes.append(
            {
                "description": "Over-commitment without buffer capacity increases delivery risk",
                "evidence": [
                    f"commitment_rate_{committed_pct:.0f}pct",
                    "no_flex_capacity",
                ],
                "confidence": 80.0,
                "reference": "capacity_buffer_analysis",
            }
        )

    # Recommended actions
    actions = []

    if committed_pct < 75:
        actions.append(
            {
                "timeframe": "medium-term",
                "description": "Build team confidence through improved velocity tracking and dependency management",
                "owner": "Scrum Masters & RTE",
                "effort": "Medium",
                "dependencies": ["Historical velocity data", "Dependency mapping"],
                "success_signal": "Commitment rate increases to 80-90% range",
            }
        )

    if committed_pct > 95:
        actions.append(
            {
                "timeframe": "short-term",
                "description": "Reserve 10-15% capacity for emergencies, learning, and improvement",
                "owner": "Product Management",
                "effort": "Low",
                "dependencies": ["Leadership agreement"],
                "success_signal": "Commitment rate balanced at 80-90%",
            }
        )

    actions.append(
        {
            "timeframe": "ongoing",
            "description": "Monitor commitment patterns and adjust PI planning approach based on delivery history",
            "owner": "RTE & Product Management",
            "effort": "Low",
            "dependencies": ["Metrics tracking"],
            "success_signal": "Stable 80-90% commitment rate with >85% accuracy",
        }
    )

    # Determine severity
    if committed_pct < 65 or committed_pct > 98:
        severity = "warning"
    elif committed_pct < 75 or committed_pct > 95:
        severity = "info"
    else:
        severity = "success"

    return {
        "title": f"PI {pi} Commitment Discipline",
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
                    "description": "Commitment pattern analysis from PI planning data",
                    "evidence": ["pip_data"],
                    "confidence": 88.0,
                    "reference": "commitment_analysis",
                }
            ]
        ),
        "recommended_actions": actions,
        "expected_outcomes": {
            "metrics_to_watch": [
                "Commitment Rate",
                "Planning Accuracy",
                "Team Confidence",
            ],
            "leading_indicators": [
                "Sprint commitment patterns",
                "Team velocity stability",
            ],
            "lagging_indicators": [
                "Planning accuracy trends",
                "Team morale",
            ],
            "timeline": "2-3 PIs for cultural shift",
            "risks": [
                "Pressure to over-commit",
                "Risk-averse under-commitment",
            ],
        },
        "metric_references": [
            "commitment_rate",
            "planning_discipline",
        ],
        "evidence": [
            f"pi_{pi}_planning_data",
            f"{committed_count}_committed",
            f"{uncommitted_count}_uncommitted",
        ],
    }
