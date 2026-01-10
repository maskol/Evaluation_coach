#!/usr/bin/env python3
"""
Debug script - Calculate average for the 6 FTART features
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from services.leadtime_service import LeadTimeService


def debug_ftart_pi_26q1():
    """Check the lead time calculation for FTART PI 26Q1"""

    print("=" * 80)
    print("DEBUG: FTART PI 26Q1 Lead Time Calculation")
    print("=" * 80)
    print()

    # Initialize service
    leadtime_service = LeadTimeService()

    if not leadtime_service.is_available():
        print("❌ LeadTime service not available")
        return

    # Get flow data for PI 26Q1, FTART only
    print("📊 Fetching flow_leadtime data for PI 26Q1, FTART...")
    flow_data = leadtime_service.client.get_flow_leadtime(
        pi="26Q1", art="FTART", limit=10000
    )
    print(f"   Total features retrieved: {len(flow_data)}")
    print()

    # Filter for completed features (Done/Deployed with leadtime > 0)
    completed_features = [
        f
        for f in flow_data
        if f.get("status") in ["Done", "Deployed"] and f.get("total_leadtime", 0) > 0
    ]

    print(f"📋 Completed FTART features:")
    print(
        f"   Features with status Done/Deployed and leadtime > 0: {len(completed_features)}"
    )
    print()

    if not completed_features:
        print("❌ No completed features found")
        return

    # Calculate averages
    lead_times = [f["total_leadtime"] for f in completed_features]
    avg_leadtime = sum(lead_times) / len(lead_times)
    min_leadtime = min(lead_times)
    max_leadtime = max(lead_times)

    print(f"🎯 CALCULATED METRICS:")
    print(f"   Average Lead Time: {avg_leadtime:.1f} days")
    print(f"   Min Lead Time: {min_leadtime:.1f} days")
    print(f"   Max Lead Time: {max_leadtime:.1f} days")
    print(f"   Number of features: {len(completed_features)}")
    print()

    # Show details of all completed features
    print("📝 DETAILED FEATURE LIST:")
    for idx, feature in enumerate(completed_features, 1):
        issue_key = feature.get("issue_key", feature.get("key", "UNKNOWN"))
        status = feature.get("status", "N/A")
        leadtime = feature.get("total_leadtime", 0)
        print(f"   {idx}. {issue_key}: {leadtime:.1f} days (status: {status})")

    print()
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print(f"Total lead time (sum): {sum(lead_times):.1f} days")
    print(f"Number of features: {len(lead_times)}")
    print(
        f"Average: {sum(lead_times):.1f} / {len(lead_times)} = {avg_leadtime:.1f} days"
    )
    print()

    # Check against expected values
    if abs(avg_leadtime - 148.5) < 1:
        print("✅ Matches expected 148.5 days!")
    elif abs(avg_leadtime - 163.5) < 1:
        print("✅ Matches expected 163.5 days!")
    else:
        print(f"⚠️  Got {avg_leadtime:.1f} days (expected 148.5 or 163.5)")

    # Calculate what we'd get with 163.5 average
    print()
    print("🔍 INVESTIGATION:")
    print(f"   If average should be 163.5 days for {len(lead_times)} features:")
    print(
        f"   Total would be: 163.5 × {len(lead_times)} = {163.5 * len(lead_times):.1f} days"
    )
    print(f"   Actual total is: {sum(lead_times):.1f} days")
    print(f"   Difference: {(163.5 * len(lead_times)) - sum(lead_times):.1f} days")


if __name__ == "__main__":
    debug_ftart_pi_26q1()
