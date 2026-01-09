#!/usr/bin/env python3
"""
Test script for Little's Law AI Agent

This script demonstrates the separate AI agent that analyzes flow metrics
using Little's Law to provide optimization insights.

Usage:
    ./test_littles_law_agent.py
    python test_littles_law_agent.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from agents.graph import run_evaluation_coach
from agents.state import create_initial_state
from services.leadtime_service import LeadTimeService


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_metrics(metrics: dict):
    """Pretty print Little's Law metrics"""
    print("📊 Little's Law Metrics:")
    print(f"   • PI: {metrics.get('pi', 'N/A')}")
    print(f"   • Features Completed: {metrics.get('total_features', 0)}")
    print(f"   • PI Duration: {metrics.get('pi_duration_days', 84)} days")
    print()
    print("   Little's Law Components (L = λ × W):")
    print(
        f"   • λ (Throughput): {metrics.get('throughput_per_day', 0):.2f} features/day"
    )
    print(f"   • W (Lead Time): {metrics.get('avg_leadtime', 0):.1f} days")
    print(f"   • L (Predicted WIP): {metrics.get('predicted_wip', 0):.1f} features")
    print()
    print("   Flow Analysis:")
    print(f"   • Flow Efficiency: {metrics.get('flow_efficiency', 0):.1f}%")
    print(f"   • Active Time: {metrics.get('avg_active_time', 0):.1f} days")
    print(f"   • Wait Time: {metrics.get('avg_wait_time', 0):.1f} days")
    print()
    print("   Optimization Targets:")
    print(f"   • Target Lead Time: {metrics.get('target_leadtime', 30)} days")
    print(f"   • Optimal WIP: {metrics.get('optimal_wip', 0):.1f} features")
    print(f"   • WIP Reduction Needed: {metrics.get('wip_reduction', 0):.1f} features")
    print()
    print(f"   Assessment: {metrics.get('severity', 'unknown').upper()}")


def print_insight(insight: dict, index: int):
    """Pretty print an insight"""
    print(f"\n{'─' * 80}")
    print(f"Insight #{index + 1}: {insight.get('title', 'Untitled')}")
    print(f"{'─' * 80}")
    print(f"Severity: {insight.get('severity', 'unknown').upper()}")
    print(f"Confidence: {insight.get('confidence', 0):.1f}%")
    print(f"Scope: {insight.get('scope', 'N/A')} - {insight.get('scope_id', 'N/A')}")
    print()
    print("📝 Observation:")
    print(f"   {insight.get('observation', 'N/A')}")
    print()
    print("💡 Interpretation:")
    print(f"   {insight.get('interpretation', 'N/A')}")
    print()

    root_causes = insight.get("root_causes", [])
    if root_causes:
        print("🔍 Root Causes:")
        for i, cause in enumerate(root_causes, 1):
            print(f"   {i}. {cause.get('description', 'N/A')}")
            print(f"      Confidence: {cause.get('confidence', 0):.0f}%")
    print()

    actions = insight.get("recommended_actions", [])
    if actions:
        print("✅ Recommended Actions:")
        for i, action in enumerate(actions, 1):
            timeframe = action.get("timeframe", "N/A").upper()
            description = action.get("description", "N/A")
            owner = action.get("owner", "N/A")
            effort = action.get("effort", "N/A")
            print(f"   {i}. [{timeframe}] {description}")
            print(f"      Owner: {owner} | Effort: {effort}")
    print()


def test_littles_law_agent_standalone():
    """Test the Little's Law agent as a standalone component"""
    print_section("Testing Little's Law Agent - Standalone Mode")

    # Check if LeadTime service is available
    service = LeadTimeService()

    if not service.is_available():
        print("❌ LeadTime service is not available!")
        print("   Please ensure DL Webb App is running on http://localhost:8000")
        print("   and LEADTIME_SERVER_ENABLED=true in your .env file")
        return False

    print("✅ LeadTime service is available")

    # Get available filters
    print("\n📋 Fetching available PIs...")
    filters = service.client.get_available_filters()
    pis = filters.get("pis", [])

    if not pis:
        print("❌ No PIs available in the system")
        return False

    print(f"✅ Found {len(pis)} PIs: {', '.join(pis)}")

    # Use the most recent PI
    pi_to_test = pis[0]
    print(f"\n🎯 Testing with PI: {pi_to_test}")

    # Import the analyzer directly
    from agents.nodes.littles_law_analyzer import (
        _calculate_littles_law_metrics,
        _generate_littles_law_insights,
        littles_law_analyzer_node,
    )

    # Get flow data
    print(f"\n📊 Fetching flow data for PI {pi_to_test}...")
    flow_data = service.get_feature_leadtime_data(pi=pi_to_test)

    if not flow_data:
        print(f"❌ No flow data available for PI {pi_to_test}")
        return False

    print(f"✅ Retrieved {len(flow_data)} features")

    # Calculate metrics
    print("\n🧮 Calculating Little's Law metrics...")
    metrics = _calculate_littles_law_metrics(flow_data, pi_to_test)

    if not metrics:
        print("❌ Could not calculate metrics (insufficient data)")
        return False

    print_metrics(metrics)

    # Create minimal state for insight generation
    minimal_state = {
        "scope": "portfolio",
        "scope_type": "portfolio",
        "scope_id": pi_to_test,
    }

    # Generate insights
    print("\n💭 Generating insights...")
    insights = _generate_littles_law_insights(minimal_state, metrics, pi_to_test)

    if not insights:
        print("❌ No insights generated")
        return False

    print(f"✅ Generated {len(insights)} insights")

    # Display insights
    for i, insight in enumerate(insights):
        print_insight(insight, i)

    return True


def test_littles_law_agent_integrated():
    """Test the Little's Law agent as part of the full workflow"""
    print_section("Testing Little's Law Agent - Integrated Workflow")

    # Check if LeadTime service is available
    service = LeadTimeService()

    if not service.is_available():
        print("❌ LeadTime service is not available!")
        print("   Skipping integrated workflow test")
        return False

    # Get a PI to test with
    filters = service.client.get_available_filters()
    pis = filters.get("pis", [])

    if not pis:
        print("❌ No PIs available")
        return False

    pi_to_test = pis[0]
    print(f"🎯 Running full agent workflow for PI: {pi_to_test}")

    # Run the complete evaluation coach workflow
    print("\n🚀 Starting LangGraph workflow...")

    try:
        result = run_evaluation_coach(
            scope="Portfolio",
            scope_type="Portfolio",
            time_window_start=datetime.now() - timedelta(days=90),
            time_window_end=datetime.now(),
        )

        print("\n✅ Workflow completed successfully!")

        # Check if Little's Law analysis was run
        littles_law_metrics = result.get("littles_law_metrics")
        littles_law_insights = result.get("littles_law_insights", [])

        if littles_law_metrics:
            print("\n📊 Little's Law metrics captured in workflow:")
            print_metrics(littles_law_metrics)
        else:
            print("\n⚠️  No Little's Law metrics in workflow results")

        if littles_law_insights:
            print(
                f"\n💡 {len(littles_law_insights)} Little's Law insights in workflow:"
            )
            for i, insight in enumerate(littles_law_insights):
                print_insight(insight, i)
        else:
            print("\n⚠️  No Little's Law insights in workflow results")

        # Check consolidated insights
        all_insights = result.get("insights", [])
        if all_insights:
            print(f"\n📋 Total insights in final report: {len(all_insights)}")

        return True

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    print("=" * 80)
    print("  LITTLE'S LAW AI AGENT TEST SUITE")
    print("=" * 80)

    results = {}

    # Test 1: Standalone mode
    try:
        results["standalone"] = test_littles_law_agent_standalone()
    except Exception as e:
        print(f"\n❌ Standalone test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["standalone"] = False

    # Test 2: Integrated mode
    try:
        results["integrated"] = test_littles_law_agent_integrated()
    except Exception as e:
        print(f"\n❌ Integrated test crashed: {e}")
        import traceback

        traceback.print_exc()
        results["integrated"] = False

    # Summary
    print_section("TEST SUMMARY")

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():20s} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
