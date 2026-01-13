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
import json

from services.leadtime_service import LeadTimeService
from agents.state import AgentState
from database import SessionLocal, RuntimeConfiguration

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

        # Get ART filter if analyzing specific ART
        art_filter = (
            state.get("selected_art") or state.get("scope")
            if state.get("scope_type") == "ART"
            else None
        )

        if art_filter and art_filter not in ["Portfolio", "portfolio"]:
            print(f"🎯 Filtering for ART: {art_filter}")

        # Determine analysis level (story vs feature)
        analysis_level = state.get("analysis_level", "feature")
        use_story_level = analysis_level == "story"
        item_type = "stories" if use_story_level else "features"

        print(f"📊 Analysis Level: {analysis_level} ({item_type})")

        # Get analysis summary (provides accurate aggregated metrics from DL Webb APP)
        print(f"📊 Fetching analysis summary for PI {pi_to_analyze}...")
        summary_params = {"pis": [pi_to_analyze]}
        if art_filter and art_filter not in ["Portfolio", "portfolio"]:
            summary_params["arts"] = [art_filter]

        # Use story or feature analysis summary based on level
        if use_story_level:
            analysis_summary = leadtime_service.client.get_story_analysis_summary(
                **summary_params
            )
        else:
            analysis_summary = leadtime_service.client.get_analysis_summary(
                **summary_params
            )

        if analysis_summary:
            print(f"✅ Retrieved analysis summary with accurate metrics")
        else:
            print("⚠️  No analysis summary available")

        # Get flow data with stage breakdown (with ART filter if applicable)
        # Fetch without PI filter and filter client-side based on resolved_date for Done items
        print(f"📊 Fetching flow data with stage breakdown for PI {pi_to_analyze}...")

        # Use story or feature flow data based on analysis level
        if use_story_level:
            all_flow_data = leadtime_service.get_story_leadtime_data(
                art=(
                    art_filter
                    if art_filter and art_filter not in ["Portfolio", "portfolio"]
                    else None
                ),
            )
        else:
            all_flow_data = leadtime_service.get_feature_leadtime_data(
                art=(
                    art_filter
                    if art_filter and art_filter not in ["Portfolio", "portfolio"]
                    else None
                ),
            )

        if not all_flow_data:
            print(f"⚠️  No flow data available")
            updates["warnings"] = [f"No flow data available for PI {pi_to_analyze}"]
            return updates

        # Filter by PI - for Done items use resolved_date, for others use pi field
        flow_data = []
        for f in all_flow_data:
            feature_pi = None
            if f.get("status") == "Done" and f.get("resolved_date"):
                # Calculate PI from resolved_date for Done items
                feature_pi = _calculate_pi_from_date(f.get("resolved_date"))
            else:
                # Use stored pi field for non-Done items
                feature_pi = f.get("pi")

            if feature_pi == pi_to_analyze:
                flow_data.append(f)

        if not flow_data:
            print(f"⚠️  No flow data available for PI {pi_to_analyze}")
            updates["warnings"] = [f"No flow data available for PI {pi_to_analyze}"]
            return updates

        print(
            f"✅ Retrieved {len(flow_data)} {item_type} for PI {pi_to_analyze} (filtered by resolved date for Done {item_type})"
        )

        # Get throughput data for accurate total lead times
        # Note: For features, throughput data (leadtime_thr_data table) already has correct Delivered PI
        # For stories, we use story_flow_leadtime data directly
        print(f"📊 Fetching throughput data for accurate lead times...")

        if use_story_level:
            # For stories, use the flow_data itself as throughput data (already have lead times)
            throughput_data = [f for f in flow_data if f.get("status") == "Done"]
        else:
            # For features, fetch from throughput endpoint
            throughput_data = leadtime_service.client.get_throughput_data(
                pi=pi_to_analyze,
                art=(
                    art_filter
                    if art_filter and art_filter not in ["Portfolio", "portfolio"]
                    else None
                ),
                limit=10000,
            )

        # Create lookup for accurate lead times by issue_key
        accurate_leadtimes = {}
        if throughput_data:
            for item in throughput_data:
                issue_key = item.get("issue_key")
                lead_time = item.get("lead_time_days") or item.get("total_leadtime", 0)
                if issue_key and lead_time > 0:
                    accurate_leadtimes[issue_key] = lead_time
            print(
                f"✅ Retrieved {len(accurate_leadtimes)} accurate lead times from throughput data"
            )
            print(f"🔍 Throughput lead times: {accurate_leadtimes}")

        # Merge accurate lead times into flow_data
        merged_count = 0
        for item in flow_data:
            issue_key = item.get("issue_key") or item.get("key")
            old_leadtime = item.get("total_leadtime", 0)
            if issue_key and issue_key in accurate_leadtimes:
                item["total_leadtime"] = accurate_leadtimes[issue_key]
                merged_count += 1
                print(
                    f"🔄 Merged {issue_key}: {old_leadtime:.1f} → {accurate_leadtimes[issue_key]:.1f} days"
                )

        if merged_count > 0:
            print(f"✅ Merged {merged_count} accurate lead times into flow_data")
        else:
            print(f"⚠️  No lead times were merged - check issue_key matching")

        # Log which items are being analyzed
        if flow_data:
            print(f"📝 {item_type.capitalize()} in analysis (Done status only):")
            done_items = [f for f in flow_data if f.get("status") == "Done"]
            for idx, item in enumerate(done_items[:10], 1):  # Show first 10
                item_id = (
                    item.get("issue_key")
                    or item.get("key")
                    or item.get("id")
                    or item.get("feature_id")
                    or "N/A"
                )
                art = item.get("art", "N/A")
                status = item.get("status", "N/A")
                leadtime = item.get("total_leadtime", 0)
                print(
                    f"   {idx}. {item_id} | ART: {art} | Status: {status} | Lead Time: {leadtime:.1f} days"
                )
            if len(done_items) > 10:
                print(f"   ... and {len(done_items) - 10} more Done {item_type}")
            print(f"📊 Total {item_type}: {len(flow_data)}, Done: {len(done_items)}")

        # Get PI planning data (pip_data) - also filter by ART
        print(f"📋 Fetching PI planning data for {pi_to_analyze}...")
        pip_params = {"pi": pi_to_analyze}
        if art_filter and art_filter not in ["Portfolio", "portfolio"]:
            pip_params["art"] = art_filter

        # Use story or feature planning data based on analysis level
        pip_data = None
        try:
            if use_story_level:
                # Story-level PIP data endpoint may not be available yet
                pip_data = leadtime_service.client.get_story_pip_data(**pip_params)
            else:
                pip_data = leadtime_service.client.get_pip_data(**pip_params)
        except Exception as pip_error:
            print(
                f"⚠️  Could not fetch {'story' if use_story_level else 'feature'} PIP data: {pip_error}"
            )
            print(f"   Continuing without planning accuracy data...")

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

        # Calculate historical capacity baseline
        historical_baseline = _calculate_historical_capacity_baseline(
            leadtime_service, pi_to_analyze, art_filter, lookback_pis=8
        )

        # Calculate Little's Law metrics (with historical baseline and item type)
        metrics = _calculate_littles_law_metrics(
            flow_data,
            pi_to_analyze,
            analysis_summary,
            historical_baseline=historical_baseline,
            item_type=item_type,  # Pass item type for proper labeling
        )

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
        print(
            f"   • Throughput (λ): {metrics['throughput_per_day']:.2f} {item_type}/day"
        )
        print(f"   • Lead Time (W): {metrics['avg_leadtime']:.1f} days")
        print(f"   • Predicted WIP (L): {metrics['predicted_wip']:.1f} {item_type}")
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

        # Generate insights using combined data (pass item_type for proper labeling)
        insights = _generate_comprehensive_insights(
            state, combined_metrics, pi_to_analyze, item_type=item_type
        )

        if insights:
            updates["littles_law_insights"] = insights
            print(f"\n✅ Generated {len(insights)} Little's Law insights")

            # Add to reasoning chain
            updates["reasoning_chain"] = [
                f"Applied Little's Law analysis for PI {pi_to_analyze}",
                f"Identified WIP optimization opportunity: {metrics['wip_reduction']:.1f} {item_type}",
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


def _calculate_pi_from_date(resolved_date: str) -> Optional[str]:
    """Calculate PI based on resolved date using PI configurations.

    Args:
        resolved_date: ISO format date string (e.g., '2026-01-07')

    Returns:
        PI identifier (e.g., '26Q1') or None if date doesn't fall in any configured PI
    """
    if not resolved_date:
        return None

    try:
        # Parse the resolved date
        if isinstance(resolved_date, str):
            resolved_dt = datetime.strptime(resolved_date[:10], "%Y-%m-%d")
        else:
            resolved_dt = resolved_date

        # Get PI configurations from database
        db = SessionLocal()
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "pi_configurations")
            .first()
        )

        if config_entry and config_entry.config_value:
            pi_configurations = json.loads(config_entry.config_value)

            # Find which PI the resolved date falls into
            for pi_config in pi_configurations:
                start_date = datetime.strptime(pi_config["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(pi_config["end_date"], "%Y-%m-%d")

                if start_date <= resolved_dt <= end_date:
                    db.close()
                    return pi_config.get("pi")

        db.close()
        return None

    except Exception as e:
        print(f"⚠️  Error calculating PI from date {resolved_date}: {e}")
        return None


def _get_pi_duration_from_config(pi: str) -> int:
    """
    Get PI duration from database configuration.

    Args:
        pi: PI identifier (e.g., 26Q1)

    Returns:
        Duration in days (defaults to 84 if not configured)
    """
    try:
        db = SessionLocal()
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "pi_configurations")
            .first()
        )

        if config_entry and config_entry.config_value:
            pi_configurations = json.loads(config_entry.config_value)

            # Find matching PI configuration
            for pi_config in pi_configurations:
                if pi_config.get("pi") == pi:
                    start_date = datetime.strptime(pi_config["start_date"], "%Y-%m-%d")
                    end_date = datetime.strptime(pi_config["end_date"], "%Y-%m-%d")
                    duration = (end_date - start_date).days
                    print(
                        f"✅ Found PI {pi} configuration: {duration} days ({pi_config['start_date']} → {pi_config['end_date']})"
                    )
                    db.close()
                    return duration

        db.close()
        print(f"⚠️  No configuration found for PI {pi}, using default 84 days")
        return 84

    except Exception as e:
        print(f"⚠️  Error loading PI configuration: {e}, using default 84 days")
        return 84


def _calculate_littles_law_metrics(
    flow_data: List[dict],
    pi: str,
    analysis_summary: Optional[Dict[str, Any]] = None,
    pi_duration_days: Optional[int] = None,
    historical_baseline: Optional[Dict[str, Any]] = None,
    item_type: str = "features",
) -> Optional[Dict[str, Any]]:
    """
    Calculate Little's Law metrics from flow data.

    Args:
        flow_data: List of items (features or stories) with lead time data
        pi: Program Increment identifier
        analysis_summary: Pre-calculated summary metrics from DL Webb APP (if available)
        pi_duration_days: Duration of PI in days (fetched from config if not provided)
        historical_baseline: Historical capacity baseline from past PIs
        item_type: Type of items being analyzed ("features" or "stories")

    Returns:
        Dictionary with calculated metrics or None if insufficient data
    """
    # Get PI duration from configuration if not provided
    if pi_duration_days is None:
        pi_duration_days = _get_pi_duration_from_config(pi)

    # If we have analysis_summary with accurate metrics, use those directly
    if analysis_summary and "leadtime_analysis" in analysis_summary:
        leadtime_data = analysis_summary.get("leadtime_analysis", {})
        throughput_data = analysis_summary.get("throughput", {})

        # Extract correct values from DL Webb APP
        avg_leadtime = leadtime_data.get("avg_leadtime") or leadtime_data.get(
            "mean_total"
        )
        median_leadtime = leadtime_data.get("median_leadtime") or leadtime_data.get(
            "median_total"
        )
        total_features = throughput_data.get("total_throughput") or throughput_data.get(
            "total_delivered"
        )

        # If we have the summary data, use it for throughput calculation
        if avg_leadtime and total_features:
            print(
                f"📊 Using DL Webb APP summary: {total_features} features, {avg_leadtime:.1f} days avg lead time"
            )

            # Log which Done features contributed to the average
            completed_features = [
                f
                for f in flow_data
                if f.get("status") == "Done" and f.get("total_leadtime", 0) > 0
            ]
            if completed_features:
                print(
                    f"📈 Done features used in average calculation ({len(completed_features)} features):"
                )
                for idx, f in enumerate(completed_features, 1):
                    feature_id = (
                        f.get("issue_key")
                        or f.get("key")
                        or f.get("id")
                        or f.get("feature_id")
                        or f"Feature_{idx}"
                    )
                    art = f.get("art", "N/A")
                    leadtime = f.get("total_leadtime", 0)
                    print(
                        f"   {idx}. {feature_id} | ART: {art} | Lead Time: {leadtime:.1f} days"
                    )

            # Calculate throughput: features delivered / PI duration
            throughput_per_day = total_features / pi_duration_days

            # Use summary data for lead time
            min_leadtime = leadtime_data.get("min_total", 0)
            max_leadtime = leadtime_data.get("max_total", avg_leadtime * 2)
            leadtime_stddev = leadtime_data.get("stddev_total", 0)

            # Calculate predicted WIP using Little's Law (L = λ × W)
            predicted_wip = throughput_per_day * avg_leadtime

            # Get flow efficiency if available
            flow_efficiency = throughput_data.get("flow_efficiency") or 0

            # If flow efficiency not in summary, calculate from flow_data
            if not flow_efficiency and flow_data:
                completed_features = [
                    f
                    for f in flow_data
                    if f.get("status") == "Done" and f.get("total_leadtime", 0) > 0
                ]

                if completed_features:
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
                        sum(active_times) / len(active_times)
                        if active_times
                        else avg_leadtime
                    )
                    flow_efficiency = (
                        (avg_active_time / avg_leadtime * 100)
                        if avg_leadtime > 0
                        else 0
                    )

            avg_wait_time = (
                avg_leadtime * (1 - flow_efficiency / 100)
                if flow_efficiency
                else avg_leadtime / 2
            )

            return {
                "pi": pi,
                "total_features": int(total_features),
                "avg_leadtime": avg_leadtime,
                "median_leadtime": median_leadtime or avg_leadtime,
                "min_leadtime": min_leadtime,
                "max_leadtime": max_leadtime,
                "leadtime_stddev": leadtime_stddev,
                "throughput_per_day": throughput_per_day,
                "predicted_wip": predicted_wip,
                "flow_efficiency": flow_efficiency,
                "avg_wait_time": avg_wait_time,
                "pi_duration_days": pi_duration_days,
            }

    # Fallback: calculate from flow_data if summary not available
    # Filter for Done features only (most accurate for throughput calculation)
    completed_features = [
        f
        for f in flow_data
        if f.get("status") == "Done" and f.get("total_leadtime", 0) > 0
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

    # Analyze current vs historical capacity
    capacity_analysis = {}
    if historical_baseline and historical_baseline.get("available"):
        historical_throughput = historical_baseline.get("avg_throughput_per_day", 0)
        historical_leadtime = historical_baseline.get("avg_historical_leadtime", 0)

        # Compare current to historical
        throughput_vs_baseline = (
            ((throughput_per_day / historical_throughput) - 1) * 100
            if historical_throughput > 0
            else 0
        )
        leadtime_vs_baseline = (
            ((avg_leadtime / historical_leadtime) - 1) * 100
            if historical_leadtime > 0
            else 0
        )

        # Calculate capacity utilization
        historical_capacity = historical_baseline.get("avg_throughput_per_pi", 0)
        current_capacity_utilization = (
            (total_features / historical_capacity) * 100
            if historical_capacity > 0
            else 0
        )

        capacity_analysis = {
            "historical_avg_throughput_per_day": historical_throughput,
            "historical_avg_leadtime": historical_leadtime,
            "throughput_vs_baseline_pct": throughput_vs_baseline,
            "leadtime_vs_baseline_pct": leadtime_vs_baseline,
            "capacity_utilization_pct": current_capacity_utilization,
            "pis_in_baseline": historical_baseline.get("num_pis", 0),
            "baseline_range": f"{historical_baseline.get('min_throughput_per_pi', 0):.0f}-{historical_baseline.get('max_throughput_per_pi', 0):.0f} features/PI",
        }

        print(f"\n📊 Capacity vs Historical Baseline:")
        print(
            f"   Historical Avg: {historical_throughput:.2f} features/day ({historical_baseline.get('avg_throughput_per_pi', 0):.1f} features/PI)"
        )
        print(
            f"   Current: {throughput_per_day:.2f} features/day ({total_features} features/PI)"
        )
        print(f"   Throughput Change: {throughput_vs_baseline:+.1f}%")
        print(f"   Lead Time Change: {leadtime_vs_baseline:+.1f}%")
        print(
            f"   Capacity Utilization: {current_capacity_utilization:.1f}% of historical average"
        )

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
        # Historical capacity analysis
        "capacity_analysis": capacity_analysis,
        "historical_baseline": historical_baseline,
        # Assessment
        "severity": severity,
        "confidence": 0.88,
    }


def _calculate_historical_capacity_baseline(
    leadtime_service: LeadTimeService,
    current_pi: str,
    art_filter: Optional[str] = None,
    lookback_pis: int = 8,
) -> Dict[str, Any]:
    """
    Calculate historical capacity baseline from past PIs using throughput data.

    Uses leadtime_thr_data to get accurate throughput across multiple PIs,
    providing a capacity proxy for planning and comparison.

    Args:
        leadtime_service: LeadTime service instance
        current_pi: Current PI being analyzed
        art_filter: Optional ART filter
        lookback_pis: Number of historical PIs to analyze (default 8)

    Returns:
        Dictionary with historical capacity metrics
    """
    print(f"\n📊 Calculating historical capacity baseline ({lookback_pis} PIs)...")

    try:
        # Get all available PIs to determine historical range
        filters = leadtime_service.client.get_available_filters()
        all_pis = filters.get("pis", [])

        # Find current PI position and get historical PIs
        try:
            current_idx = all_pis.index(current_pi)
            # Get PIs before current (historical data)
            historical_pis = all_pis[max(0, current_idx - lookback_pis) : current_idx]
        except ValueError:
            # Current PI not in list, use last N PIs
            historical_pis = (
                all_pis[-lookback_pis:] if len(all_pis) >= lookback_pis else all_pis
            )

        if not historical_pis:
            print("⚠️  No historical PIs available")
            return {"available": False}

        print(f"📋 Historical PIs: {', '.join(historical_pis)}")

        # Fetch throughput data for all historical PIs
        historical_throughput = []
        pi_throughputs = {}

        for pi in historical_pis:
            params = {"pi": pi, "limit": 10000}
            if art_filter and art_filter not in ["Portfolio", "portfolio"]:
                params["art"] = art_filter

            thr_data = leadtime_service.client.get_throughput_data(**params)

            if thr_data:
                pi_throughputs[pi] = len(thr_data)
                historical_throughput.extend(thr_data)
                print(f"  ✅ {pi}: {len(thr_data)} features delivered")
            else:
                print(f"  ⚠️  {pi}: No throughput data")

        if not historical_throughput:
            print("⚠️  No historical throughput data available")
            return {"available": False}

        # Calculate capacity baseline metrics
        total_historical_features = len(historical_throughput)
        num_pis_with_data = len(pi_throughputs)

        # Average throughput per PI
        avg_throughput_per_pi = (
            total_historical_features / num_pis_with_data
            if num_pis_with_data > 0
            else 0
        )

        # Throughput per day (assuming 84-day PIs)
        avg_throughput_per_day = (
            avg_throughput_per_pi / 84 if avg_throughput_per_pi > 0 else 0
        )

        # Calculate variability (stddev of PI throughputs)
        throughput_values = list(pi_throughputs.values())
        mean_throughput = (
            sum(throughput_values) / len(throughput_values) if throughput_values else 0
        )
        variance = (
            sum((x - mean_throughput) ** 2 for x in throughput_values)
            / len(throughput_values)
            if throughput_values
            else 0
        )
        stddev_throughput = variance**0.5

        # Min/max throughput across PIs
        min_throughput = min(throughput_values) if throughput_values else 0
        max_throughput = max(throughput_values) if throughput_values else 0

        # Calculate lead times from historical data
        lead_times = [
            f.get("lead_time_days", 0)
            for f in historical_throughput
            if f.get("lead_time_days", 0) > 0
        ]
        avg_historical_leadtime = sum(lead_times) / len(lead_times) if lead_times else 0

        print(f"\n✅ Historical Capacity Baseline:")
        print(f"   PIs Analyzed: {num_pis_with_data} ({', '.join(historical_pis)})")
        print(f"   Total Features Delivered: {total_historical_features}")
        print(f"   Avg Throughput per PI: {avg_throughput_per_pi:.1f} features")
        print(f"   Avg Throughput per Day: {avg_throughput_per_day:.2f} features/day")
        print(f"   Throughput Range: {min_throughput}-{max_throughput} features/PI")
        print(f"   Throughput StdDev: {stddev_throughput:.1f} features")
        print(f"   Avg Historical Lead Time: {avg_historical_leadtime:.1f} days")

        return {
            "available": True,
            "pis_analyzed": historical_pis,
            "num_pis": num_pis_with_data,
            "total_features": total_historical_features,
            "avg_throughput_per_pi": avg_throughput_per_pi,
            "avg_throughput_per_day": avg_throughput_per_day,
            "min_throughput_per_pi": min_throughput,
            "max_throughput_per_pi": max_throughput,
            "stddev_throughput": stddev_throughput,
            "avg_historical_leadtime": avg_historical_leadtime,
            "pi_breakdown": pi_throughputs,
        }

    except Exception as e:
        print(f"⚠️  Error calculating historical baseline: {e}")
        return {"available": False, "error": str(e)}


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
            # plc_delivery can be string "1" or integer 1, handle both
            if str(plc_delivery) == "1" or plc_delivery == 1:
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
    # Only report ART performance issues if analyzing multiple ARTs
    if art_misses and len(art_misses) > 1:
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
    _state: AgentState, metrics: Dict[str, Any], pi: str, item_type: str = "features"
) -> List[Dict[str, Any]]:
    """
    Generate comprehensive insights combining Little's Law and planning analysis.

    Includes:
    - Flow metrics (WIP, throughput, lead time)
    - Planning accuracy
    - Commitment levels
    - Reasons for missed deliveries

    Enhanced with RAG for richer expert analysis.

    Args:
        _state: Agent state
        metrics: Calculated metrics
        pi: PI identifier
        item_type: Type of items being analyzed ("features" or "stories")
    """
    insights = []

    # Prepare context for RAG enhancement
    rag_context = {"metrics": metrics, "pi": pi, "item_type": item_type}

    # Check if LLM enhancement should be skipped (for performance)
    # Can be controlled via state parameter
    skip_llm_enhancement = _state.get("skip_littles_law_llm_enhancement", True)

    if skip_llm_enhancement:
        print(
            "ℹ️  Skipping LLM enhancement for faster response (set skip_littles_law_llm_enhancement=False to enable)"
        )

    # Generate flow insights (Little's Law)
    flow_insight = _generate_flow_insight(metrics, pi, item_type)
    if flow_insight:
        # Enhance with RAG if available and not skipped
        if not skip_llm_enhancement:
            flow_insight = _enhance_insight_with_rag(flow_insight, rag_context)
        insights.append(flow_insight)

    # Generate planning accuracy insight
    if metrics.get("total_planned", 0) > 0:
        planning_insight = _generate_planning_insight(metrics, pi, item_type)
        if planning_insight:
            # Enhance with RAG if available and not skipped
            if not skip_llm_enhancement:
                planning_insight = _enhance_insight_with_rag(
                    planning_insight, rag_context
                )
            insights.append(planning_insight)

    # Generate commitment analysis insight
    if metrics.get("committed_count", 0) > 0:
        commitment_insight = _generate_commitment_insight(metrics, pi, item_type)
        if commitment_insight:
            # Enhance with RAG if available and not skipped
            if not skip_llm_enhancement:
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
        item_type = context.get("item_type", "features")

        # Use a concise coaching template instead of RAG retrieval
        # RAG retrieval can be slow and the full template is too large for the prompt
        coaching_template = """Provide a comprehensive Little's Law analysis:

## Analysis Structure:
1. **Little's Law Formula**: State L = λ × W with actual values
2. **Historical Context**: Compare current vs historical capacity (if available)
3. **System WIP Calculation**: Calculate predicted WIP from throughput and lead time
4. **Scenario Analysis**: Show WIP impact for current, +50%, and -30% throughput scenarios
5. **Stage-Level Breakdown**: Map WIP to workflow stages (if data available)
6. **WIP Impact Table**: Show how increased WIP affects lead time
7. **Actionable Recommendations**: Provide 2-3 specific actions with owners and timelines

## Requirements:
- Use ACTUAL numbers from metrics (not placeholders)
- Show all calculations explicitly (e.g., "0.2 × 70 = 14")
- Create markdown tables for clarity
- Focus on Little's Law relationships
- Make it actionable for RTEs, PMs, and Scrum Masters
- Connect to SAFe practices (PI Planning, ART Sync, flow metrics)"""

        # Create prompt with metrics and retrieved template
        prompt = f"""You are an expert Agile coach analyzing flow metrics using Little's Law for SAFe organizations.

**Current Insight:**
Title: {insight['title']}
Observation: {insight['observation']}
Interpretation: {insight['interpretation']}

**Flow Metrics (Little's Law Analysis):**
- PI: {pi}
- Throughput (λ): {metrics.get('throughput_per_day', 0):.2f} {item_type}/day
- Average Lead Time (W): {metrics.get('avg_leadtime', 0):.1f} days
- Predicted WIP (L): {metrics.get('predicted_wip', 0):.1f} {item_type}
- Flow Efficiency: {metrics.get('flow_efficiency', 0):.1f}%
- Active Time: {metrics.get('avg_active_time', 0):.1f} days
- Wait Time: {metrics.get('avg_wait_time', 0):.1f} days
- Total {item_type.capitalize()}: {metrics.get('total_features', 0)}
- Lead Time Std Dev: {metrics.get('leadtime_stddev', 0):.1f} days
- Lead Time Range: {metrics.get('leadtime_min', 0):.1f}-{metrics.get('leadtime_max', 0):.1f} days

**Historical Capacity Baseline:**
- Based on: {metrics.get('capacity_analysis', dict()).get('pis_in_baseline', 0)} previous PIs
- Historical Avg Throughput: {metrics.get('capacity_analysis', dict()).get('historical_avg_throughput_per_day', 0):.2f} {item_type}/day
- Historical Avg Lead Time: {metrics.get('capacity_analysis', dict()).get('historical_avg_leadtime', 0):.1f} days
- Throughput vs Baseline: {metrics.get('capacity_analysis', dict()).get('throughput_vs_baseline_pct', 0):+.1f}%
- Lead Time vs Baseline: {metrics.get('capacity_analysis', dict()).get('leadtime_vs_baseline_pct', 0):+.1f}%
- Capacity Utilization: {metrics.get('capacity_analysis', dict()).get('capacity_utilization_pct', 0):.1f}%
- Historical Range: {metrics.get('capacity_analysis', dict()).get('baseline_range', 'N/A')}

**Stage-Level Breakdown:**
{_format_stage_metrics(metrics.get('stage_metrics', dict()))}

**Planning Metrics:**
- Planning Accuracy: {metrics.get('planning_accuracy', 0):.1f}%
- Committed {item_type.capitalize()}: {metrics.get('committed_count', 0)}
- Uncommitted {item_type.capitalize()}: {metrics.get('uncommitted_count', 0)}
- Post-Planning Additions: {metrics.get('post_planning_count', 0)}
- Delivered Committed: {metrics.get('delivered_committed_count', 0)}
- Missed Committed: {metrics.get('missed_committed_count', 0)}

**COACHING TEMPLATE:**
{coaching_template}

**TASK:**
Using the coaching template above, provide a comprehensive Little's Law analysis with ACTUAL numbers from the metrics.
Replace all placeholders (X, Y, Z) with real calculated values. Show all math explicitly."""

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
    metrics: Dict[str, Any], pi: str, item_type: str = "features"
) -> Optional[Dict[str, Any]]:
    """Generate Little's Law flow optimization insight."""

    # Build observation
    observation_parts = [
        f"During PI {pi} ({metrics['pi_duration_days']}-day period), {metrics['total_features']} {item_type} were completed.",
        f"Throughput (λ) = {metrics['throughput_per_day']:.2f} {item_type}/day.",
        f"Average Lead Time (W) = {metrics['avg_leadtime']:.1f} days (range: {metrics['leadtime_min']:.1f}-{metrics['leadtime_max']:.1f}).",
        f"Predicted WIP (L) = {metrics['predicted_wip']:.1f} {item_type}.",
        f"Flow Efficiency = {metrics['flow_efficiency']:.1f}% (active work time / total lead time).",
    ]

    # Add historical capacity comparison if available
    capacity_analysis = metrics.get("capacity_analysis", {})
    if capacity_analysis:
        historical_throughput = capacity_analysis.get(
            "historical_avg_throughput_per_day", 0
        )
        throughput_change = capacity_analysis.get("throughput_vs_baseline_pct", 0)
        capacity_util = capacity_analysis.get("capacity_utilization_pct", 0)
        num_historical_pis = capacity_analysis.get("pis_in_baseline", 0)

        observation_parts.append(
            f"Historical Baseline ({num_historical_pis} PIs): {historical_throughput:.2f} {item_type}/day average. "
            f"Current throughput is {abs(throughput_change):.1f}% {'above' if throughput_change > 0 else 'below'} historical capacity "
            f"({capacity_util:.1f}% capacity utilization)."
        )

    # Build interpretation
    interpretation_parts = []

    # Add capacity trend interpretation
    if capacity_analysis:
        throughput_change = capacity_analysis.get("throughput_vs_baseline_pct", 0)
        leadtime_change = capacity_analysis.get("leadtime_vs_baseline_pct", 0)
        historical_leadtime = capacity_analysis.get("historical_avg_leadtime", 0)

        if throughput_change < -20:
            interpretation_parts.append(
                f"Throughput has decreased {abs(throughput_change):.1f}% compared to historical baseline. "
                "This indicates potential capacity constraints or increased complexity."
            )
        elif throughput_change > 20:
            interpretation_parts.append(
                f"Throughput has increased {throughput_change:.1f}% above historical baseline, "
                "demonstrating improved delivery capacity."
            )

        if leadtime_change > 20 and historical_leadtime > 0:
            interpretation_parts.append(
                f"Lead time has increased {leadtime_change:.1f}% from historical average ({historical_leadtime:.1f} days), "
                "suggesting growing inefficiency in the delivery process."
            )
        elif leadtime_change < -10 and historical_leadtime > 0:
            interpretation_parts.append(
                f"Lead time has improved {abs(leadtime_change):.1f}% compared to historical baseline ({historical_leadtime:.1f} days)."
            )

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
                "confidence": 0.90,
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
                "confidence": 0.85,
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
                "confidence": 0.75,
                "reference": "littles_law_variability_analysis",
            }
        )

    # Recommended actions
    actions = []

    # Add capacity-based recommendations
    if capacity_analysis:
        throughput_change = capacity_analysis.get("throughput_vs_baseline_pct", 0)
        capacity_util = capacity_analysis.get("capacity_utilization_pct", 0)

        if throughput_change < -20:
            actions.append(
                {
                    "timeframe": "immediate",
                    "description": f"Investigate {abs(throughput_change):.1f}% throughput decline vs historical baseline: review team capacity, dependencies, and impediments",
                    "owner": "RTE & ART Leadership",
                    "effort": "Low",
                    "dependencies": [
                        "Historical throughput data",
                        "Team retrospectives",
                    ],
                    "success_signal": "Root causes identified and mitigation plan created within 1 sprint",
                }
            )

        if capacity_util > 120:
            actions.append(
                {
                    "timeframe": "short-term",
                    "description": f"Current delivery ({capacity_util:.0f}% of historical capacity) is unsustainable: reduce commitments to historical baseline ({capacity_analysis.get('historical_avg_throughput_per_day', 0):.2f} features/day)",
                    "owner": "Product Management & RTEs",
                    "effort": "Low",
                    "dependencies": ["Stakeholder alignment"],
                    "success_signal": "Commitment levels aligned with sustainable capacity within 1 PI",
                }
            )
        elif capacity_util < 70:
            actions.append(
                {
                    "timeframe": "short-term",
                    "description": f"Operating below historical capacity ({capacity_util:.0f}%): investigate underutilization or capacity loss",
                    "owner": "RTE & Scrum Masters",
                    "effort": "Medium",
                    "dependencies": ["Team capacity review"],
                    "success_signal": "Return to 80-100% of historical baseline capacity",
                }
            )

    if metrics["wip_reduction"] > 2:
        actions.append(
            {
                "timeframe": "short-term",
                "description": f"Implement strict WIP limits: cap active {item_type} at {metrics['optimal_wip']:.0f} per team/ART",
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
    level_label = "Story-Level" if item_type == "stories" else "Feature-Level"
    main_insight = {
        "title": f"Little's Law Analysis: PI {pi} {level_label} Flow Optimization",
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
                    "confidence": 0.88,
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
    metrics: Dict[str, Any], pi: str, item_type: str = "features"
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
        f"{committed_count} committed {item_type}, {uncommitted_count} uncommitted {item_type}.",
        f"{post_planning_count} {item_type} added after PI planning.",
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
                "confidence": 0.90,
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
                "confidence": 0.85,
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
                "confidence": 0.80 if reason["impact"] == "high" else 0.70,
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
        "confidence": 0.92,
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
                    "confidence": 0.92,
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
    metrics: Dict[str, Any], pi: str, item_type: str = "features"
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
        f"{committed_pct:.1f}% committed ({committed_count} {item_type}),",
        f"{100 - committed_pct:.1f}% uncommitted ({uncommitted_count} {item_type}).",
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
                "confidence": 0.85,
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
                "confidence": 0.80,
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
        "confidence": 0.88,
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
                    "confidence": 0.88,
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
