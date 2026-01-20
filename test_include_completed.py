"""
Test script to verify include_completed parameter is working correctly.

This script tests the integration between Evaluation Coach and DL Webb APP
to ensure completed items are included in historical analysis.
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

from integrations.leadtime_client import LeadTimeClient
from datetime import datetime


def test_include_completed_parameter():
    """Test if DL Webb APP respects the include_completed parameter"""

    print("=" * 80)
    print("TESTING INCLUDE_COMPLETED PARAMETER")
    print("=" * 80)
    print()

    client = LeadTimeClient(base_url="http://localhost:8000")

    # Test 1: Historical PIs WITHOUT include_completed parameter
    print("Test 1: Historical PIs WITHOUT include_completed parameter")
    print("-" * 80)
    print("Request: GET /api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART")
    print()

    try:
        response1 = client.get_analysis_summary(
            pis=["25Q1", "25Q2", "25Q3", "25Q4"],
            arts=["C4ART"],
            include_completed=None,  # Don't send parameter
        )

        stuck_items1 = response1.get("bottleneck_analysis", {}).get("stuck_items", [])
        print(f"✅ Response received: {len(stuck_items1)} stuck items")

        if stuck_items1:
            print(f"\nTop 5 stuck items:")
            for i, item in enumerate(stuck_items1[:5], 1):
                print(
                    f"  {i}. {item.get('feature_key')}: {item.get('days_in_stage'):.1f} days ({item.get('status')})"
                )

            # Check for completed items
            completed_count = sum(
                1
                for item in stuck_items1
                if item.get("status", "").upper() in ["DONE", "CLOSED", "RESOLVED"]
            )
            print(
                f"\n📊 Completed items in response: {completed_count}/{len(stuck_items1)}"
            )

            # Check if C4ART-87 is present
            c4art87 = next(
                (
                    item
                    for item in stuck_items1
                    if item.get("feature_key") == "C4ART-87"
                ),
                None,
            )
            if c4art87:
                print(
                    f"✅ C4ART-87 FOUND: {c4art87.get('days_in_stage'):.1f} days ({c4art87.get('status')})"
                )
            else:
                print(
                    f"❌ C4ART-87 NOT FOUND (this is expected without include_completed)"
                )

    except Exception as e:
        print(f"❌ Error: {e}")

    print()
    print("=" * 80)
    print()

    # Test 2: Historical PIs WITH include_completed=true parameter
    print("Test 2: Historical PIs WITH include_completed=true parameter")
    print("-" * 80)
    print(
        "Request: GET /api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART&include_completed=true"
    )
    print()

    try:
        response2 = client.get_analysis_summary(
            pis=["25Q1", "25Q2", "25Q3", "25Q4"],
            arts=["C4ART"],
            include_completed=True,  # Send parameter
        )

        stuck_items2 = response2.get("bottleneck_analysis", {}).get("stuck_items", [])
        print(f"✅ Response received: {len(stuck_items2)} stuck items")

        if stuck_items2:
            print(f"\nTop 5 stuck items:")
            for i, item in enumerate(stuck_items2[:5], 1):
                print(
                    f"  {i}. {item.get('feature_key')}: {item.get('days_in_stage'):.1f} days ({item.get('status')})"
                )
                print(f"      Available keys: {list(item.keys())}")
                if i == 1:
                    print(f"      Full item: {item}")

            # Check for completed items
            completed_count = sum(
                1
                for item in stuck_items2
                if item.get("status", "").upper() in ["DONE", "CLOSED", "RESOLVED"]
            )
            print(
                f"\n📊 Completed items in response: {completed_count}/{len(stuck_items2)}"
            )

            # Check if C4ART-87 is present
            c4art87 = next(
                (
                    item
                    for item in stuck_items2
                    if item.get("feature_key") == "C4ART-87"
                ),
                None,
            )
            if c4art87:
                print(
                    f"✅ C4ART-87 FOUND: {c4art87.get('days_in_stage'):.1f} days ({c4art87.get('status')})"
                )
                print(f"   🎯 This is the 256-day item!")
            else:
                print(
                    f"❌ C4ART-87 NOT FOUND (BUG: should be present with include_completed=true)"
                )

    except Exception as e:
        print(f"❌ Error: {e}")

    print()
    print("=" * 80)
    print()

    # Compare results
    print("COMPARISON")
    print("-" * 80)
    print(f"Without include_completed: {len(stuck_items1)} items")
    print(f"With include_completed=true: {len(stuck_items2)} items")
    print(f"Difference: {len(stuck_items2) - len(stuck_items1)} items")
    print()

    if len(stuck_items2) > len(stuck_items1):
        print(
            "✅ WORKING: include_completed parameter adds more items (completed ones)"
        )
    elif len(stuck_items2) == len(stuck_items1):
        print("⚠️  SUSPICIOUS: Same number of items - parameter may not be working")
    else:
        print("❌ ERROR: Fewer items with parameter - something is wrong")

    print()
    print("=" * 80)
    print()

    # Final verdict
    c4art87_test1 = next(
        (item for item in stuck_items1 if item.get("feature_key") == "C4ART-87"), None
    )
    c4art87_test2 = next(
        (item for item in stuck_items2 if item.get("feature_key") == "C4ART-87"), None
    )

    print("FINAL VERDICT")
    print("-" * 80)
    if c4art87_test2:
        print("✅ SUCCESS: C4ART-87 appears with include_completed=true")
        print("   DL Webb APP has correctly implemented the feature!")
    else:
        print("❌ FAILURE: C4ART-87 does NOT appear even with include_completed=true")
        print("   DL Webb APP either:")
        print("   1. Hasn't deployed the feature yet")
        print("   2. Has a bug in the implementation")
        print("   3. C4ART-87 doesn't exist in the database")
        print()
        print("   ACTION REQUIRED:")
        print("   - Check DL Webb APP implementation")
        print("   - Verify database has C4ART-87 with status DONE")
        print("   - Check DL Webb APP logs for errors")

    print("=" * 80)


if __name__ == "__main__":
    test_include_completed_parameter()
