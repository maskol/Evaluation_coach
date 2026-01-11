#!/usr/bin/env python3
"""
Debug script to investigate why planning accuracy shows 0.0% for UCART in 25Q4
when it should be 76.0%
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from services.leadtime_service import LeadTimeService


def debug_planning_accuracy():
    """Check the planning accuracy calculation for PI 25Q4"""

    print("=" * 80)
    print("DEBUG: PI 25Q4 Planning Accuracy - UCART")
    print("=" * 80)
    print()

    # Initialize service
    leadtime_service = LeadTimeService()

    if not leadtime_service.is_available():
        print("❌ LeadTime service not available")
        return

    print("✅ LeadTime service available")
    print()

    # Get pip data for PI 25Q4
    print("📊 Fetching pip_data for PI 25Q4, ART UCART...")
    pip_data = leadtime_service.client.get_pip_data(pi="25Q4", art="UCART")
    print(f"   Total features retrieved: {len(pip_data)}")
    print()

    # Analyze the data
    committed = []
    uncommitted = []
    delivered_committed = []
    missed_committed = []

    for item in pip_data:
        planned_committed = item.get("planned_committed", 0)
        planned_uncommitted = item.get("planned_uncommitted", 0)
        plc_delivery = item.get("plc_delivery", 0)

        print(f"Feature: {item.get('issue_key', 'UNKNOWN')}")
        print(
            f"  planned_committed: {planned_committed} (type: {type(planned_committed)})"
        )
        print(
            f"  planned_uncommitted: {planned_uncommitted} (type: {type(planned_uncommitted)})"
        )
        print(f"  plc_delivery: {plc_delivery} (type: {type(plc_delivery)})")

        # Categorize items (CURRENT BUGGY LOGIC)
        if planned_committed == 1:
            committed.append(item)
            print(f"  -> Categorized as: COMMITTED")
            if plc_delivery == 1:  # THIS IS THE BUG - comparing to integer
                delivered_committed.append(item)
                print(f"     -> DELIVERED (integer comparison)")
            else:
                missed_committed.append(item)
                print(f"     -> MISSED (integer comparison)")
        elif planned_uncommitted == 1:
            uncommitted.append(item)
            print(f"  -> Categorized as: UNCOMMITTED")

        # Now try with string comparison
        if planned_committed == 1:
            if plc_delivery == "1":  # CORRECT - comparing to string
                print(f"     -> Would be DELIVERED (string comparison)")

        print()

    print("=" * 80)
    print("RESULTS WITH CURRENT BUGGY LOGIC (integer comparison):")
    print("=" * 80)
    committed_count = len(committed)
    delivered_count = len(delivered_committed)
    missed_count = len(missed_committed)

    planning_accuracy = 0
    if committed_count > 0:
        planning_accuracy = (delivered_count / committed_count) * 100

    print(f"Committed features: {committed_count}")
    print(f"Delivered (with int comparison): {delivered_count}")
    print(f"Missed (with int comparison): {missed_count}")
    print(f"Planning Accuracy: {planning_accuracy:.1f}%")
    print()

    # Now calculate with correct string comparison
    print("=" * 80)
    print("CORRECTED RESULTS (string comparison):")
    print("=" * 80)
    delivered_committed_fixed = []
    missed_committed_fixed = []

    for item in committed:
        plc_delivery = item.get("plc_delivery", 0)
        # Correct logic: handle string values
        if str(plc_delivery) == "1" or plc_delivery == 1:
            delivered_committed_fixed.append(item)
        else:
            missed_committed_fixed.append(item)

    delivered_count_fixed = len(delivered_committed_fixed)
    missed_count_fixed = len(missed_committed_fixed)

    planning_accuracy_fixed = 0
    if committed_count > 0:
        planning_accuracy_fixed = (delivered_count_fixed / committed_count) * 100

    print(f"Committed features: {committed_count}")
    print(f"Delivered (with string comparison): {delivered_count_fixed}")
    print(f"Missed (with string comparison): {missed_count_fixed}")
    print(f"Planning Accuracy: {planning_accuracy_fixed:.1f}%")
    print()

    if abs(planning_accuracy_fixed - 76.0) < 1:
        print("✅ Corrected calculation matches expected 76.0%")
    else:
        print(
            f"⚠️  Corrected calculation shows {planning_accuracy_fixed:.1f}% (expected 76.0%)"
        )


if __name__ == "__main__":
    debug_planning_accuracy()
