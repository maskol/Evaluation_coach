#!/usr/bin/env python3
"""
Debug script to investigate why lead time is 148.5 instead of 163.5 for PI 26Q1
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from services.leadtime_service import LeadTimeService


def debug_pi_26q1_leadtime():
    """Check the lead time calculation for PI 26Q1"""

    print("=" * 80)
    print("DEBUG: PI 26Q1 Lead Time Calculation")
    print("=" * 80)
    print()

    # Initialize service
    leadtime_service = LeadTimeService()

    if not leadtime_service.is_available():
        print("❌ LeadTime service not available")
        return

    print("✅ LeadTime service available")
    print()

    # Get flow data for PI 26Q1
    print("📊 Fetching flow_leadtime data for PI 26Q1...")
    flow_data = leadtime_service.client.get_flow_leadtime(pi="26Q1", limit=10000)
    print(f"   Total features retrieved: {len(flow_data)}")
    print()

    # Filter for completed features (Done/Deployed with leadtime > 0)
    completed_features = [
        f
        for f in flow_data
        if f.get("status") in ["Done", "Deployed"] and f.get("total_leadtime", 0) > 0
    ]

    print(f"📋 Completed features filter:")
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
    print(f"{'#':<4} {'Issue Key':<20} {'Status':<12} {'Lead Time':<12} {'ART':<10}")
    print("-" * 80)

    for idx, feature in enumerate(completed_features, 1):
        issue_key = feature.get("issue_key", feature.get("key", "UNKNOWN"))
        status = feature.get("status", "N/A")
        leadtime = feature.get("total_leadtime", 0)
        art = feature.get("art", "N/A")
        print(f"{idx:<4} {issue_key:<20} {status:<12} {leadtime:<12.1f} {art:<10}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total lead time (sum): {sum(lead_times):.1f} days")
    print(f"Number of features: {len(lead_times)}")
    print(
        f"Average: {sum(lead_times):.1f} / {len(lead_times)} = {avg_leadtime:.1f} days"
    )
    print()

    # Check if 163.5 is the correct value
    if abs(avg_leadtime - 148.5) < 1:
        print("✅ Current calculation matches 148.5 days")
    elif abs(avg_leadtime - 163.5) < 1:
        print("✅ Calculation shows 163.5 days (expected value)")
    else:
        print(f"⚠️  Calculation shows {avg_leadtime:.1f} days (neither 148.5 nor 163.5)")

    print()

    # Additional analysis: check if there's a different filter that gives 163.5
    print("🔍 ADDITIONAL ANALYSIS:")
    print()

    # Try with only "Done" status
    done_only = [
        f
        for f in flow_data
        if f.get("status") == "Done" and f.get("total_leadtime", 0) > 0
    ]
    if done_only:
        done_avg = sum(f["total_leadtime"] for f in done_only) / len(done_only)
        print(f"   Only 'Done' status ({len(done_only)} features): {done_avg:.1f} days")

    # Try including ALL features with leadtime > 0 (any status)
    all_with_leadtime = [f for f in flow_data if f.get("total_leadtime", 0) > 0]
    if all_with_leadtime:
        all_avg = sum(f["total_leadtime"] for f in all_with_leadtime) / len(
            all_with_leadtime
        )
        print(
            f"   All features with leadtime > 0 ({len(all_with_leadtime)} features): {all_avg:.1f} days"
        )

    # Check status distribution
    print()
    print("📊 Status distribution in flow_data:")
    statuses = {}
    for f in flow_data:
        status = f.get("status", "Unknown")
        statuses[status] = statuses.get(status, 0) + 1
    for status, count in sorted(statuses.items(), key=lambda x: x[1], reverse=True):
        print(f"   {status}: {count} features")


if __name__ == "__main__":
    debug_pi_26q1_leadtime()
