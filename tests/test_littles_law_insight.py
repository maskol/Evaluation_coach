#!/usr/bin/env python3
"""
Test script for Little's Law insight generation

This script tests the new Little's Law analysis feature that uses
flow_leadtime data from the DL Webb App server.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from services.insights_service import InsightsService
from services.leadtime_service import LeadTimeService


def test_littles_law_insight():
    """Test Little's Law insight generation with real data"""

    print("=" * 80)
    print("Little's Law Insight Test")
    print("=" * 80)
    print()

    # Initialize services
    insights_service = InsightsService()
    leadtime_service = LeadTimeService()

    # Check if leadtime service is available
    print("1️⃣ Checking lead-time service availability...")
    if not leadtime_service.is_available():
        print("❌ Lead-time server is not available.")
        print("   Please ensure DL Webb App is running on http://localhost:8000")
        return False
    print("✅ Lead-time service is available")
    print()

    # Get available PIs
    print("2️⃣ Fetching available PIs...")
    try:
        filters = leadtime_service.client.get_available_filters()
        available_pis = filters.get("pis", [])
        print(
            f"✅ Found {len(available_pis)} PIs: {', '.join(sorted(available_pis, reverse=True)[:5])}"
        )

        if not available_pis:
            print("❌ No PIs available in the data")
            return False

    except Exception as e:
        print(f"❌ Error fetching filters: {e}")
        return False
    print()

    # Select a PI to analyze (most recent)
    pi_to_test = sorted(available_pis, reverse=True)[0]
    print(f"3️⃣ Analyzing PI: {pi_to_test}")
    print()

    # Fetch flow_leadtime data
    print("4️⃣ Fetching flow_leadtime data...")
    try:
        flow_data = leadtime_service.client.get_flow_leadtime(
            pi=pi_to_test, limit=10000
        )
        print(f"✅ Retrieved {len(flow_data)} features")

        # Show sample data
        if flow_data:
            sample = flow_data[0]
            print(f"\n   Sample feature:")
            print(f"   - Issue Key: {sample.get('issue_key', 'N/A')}")
            print(f"   - Status: {sample.get('status', 'N/A')}")
            print(f"   - Total Lead Time: {sample.get('total_leadtime', 0):.1f} days")
            print(f"   - In Progress: {sample.get('in_progress', 0):.1f} days")

    except Exception as e:
        print(f"❌ Error fetching flow data: {e}")
        return False
    print()

    # Generate Little's Law insight
    print("5️⃣ Generating Little's Law insight...")
    try:
        insight = insights_service._generate_littles_law_insight(
            pi=pi_to_test, flow_data=flow_data, pi_duration_days=84
        )

        if not insight:
            print("❌ Could not generate insight (insufficient data)")
            return False

        print("✅ Insight generated successfully!")
        print()

        # Display insight details
        print("=" * 80)
        print(f"📊 {insight['title']}")
        print("=" * 80)
        print()
        print(f"🎯 Severity: {insight['severity'].upper()}")
        print(f"📈 Confidence: {insight['confidence']}%")
        print(f"🔍 Scope: {insight['scope']} ({insight['scope_id']})")
        print()
        print("📝 Observation:")
        print(f"   {insight['observation']}")
        print()
        print("💡 Interpretation:")
        print(f"   {insight['interpretation']}")
        print()
        print(f"🔍 Root Causes ({len(insight['root_causes'])}):")
        for i, rc in enumerate(insight["root_causes"], 1):
            print(f"   {i}. {rc['description']}")
            print(f"      Confidence: {rc['confidence']}%")
        print()
        print(f"✅ Recommended Actions ({len(insight['recommended_actions'])}):")
        for i, action in enumerate(insight["recommended_actions"], 1):
            print(f"   {i}. [{action['timeframe']}] {action['description']}")
            print(f"      Owner: {action['owner']}")
            print(f"      Success Signal: {action['success_signal']}")
        print()
        print("📊 Metrics to Watch:")
        for metric in insight["expected_outcomes"]["metrics_to_watch"]:
            print(f"   - {metric}")
        print()
        print(f"⏱️  Timeline: {insight['expected_outcomes']['timeline']}")
        print()

        return True

    except Exception as e:
        print(f"❌ Error generating insight: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    print("\n")
    success = test_littles_law_insight()
    print("\n")

    if success:
        print("=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
