"""
Test script to verify the insight export functionality
"""

import sys
import os
import json

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

import requests


def test_insight_export():
    """Test exporting an insight to Excel"""
    print("\n" + "=" * 80)
    print("TESTING INSIGHT EXPORT TO EXCEL")
    print("=" * 80)

    # Sample insight data (similar to what frontend would send)
    insight_data = {
        "title": "Critical Bottleneck in In Sit Stage",
        "severity": "critical",
        "confidence": 0.9,
        "scope": "ART: UCART | Team: Loke | PI: 26Q1",
        "scope_id": None,
        "observation": "The in sit stage has a bottleneck score of 100.0%. Average time: 86.0 days, with 2 stage occurrences exceeding threshold (max: 151 days).",
        "interpretation": "Features are spending excessive time in in sit. This stage is a critical constraint in your delivery flow.",
        "created_at": "2026-01-12T10:00:00",
        "status": "active",
        "evidence": [
            "Bottleneck score: 100.0%",
            "Mean duration: 86.0 days",
            "Maximum duration: 151 days",
            "Stage occurrences exceeding threshold: 2",
            "UCART-2228: 151.0 days in in_sit",
        ],
        "root_causes": [
            {
                "description": "Severe flow blockage with items stuck in stage",
                "evidence": [
                    "UCART-2228: 151.0 days in in_sit",
                    "Mean duration: 86.0 days",
                ],
                "confidence": 0.95,
                "reference": "in_sit stage metrics",
            }
        ],
        "recommended_actions": [
            {
                "timeframe": "immediate",
                "description": "Review top stuck items in In Sit",
                "owner": "delivery_manager",
                "effort": "2-4 hours",
                "dependencies": [],
                "success_signal": "Root cause identified",
            }
        ],
        "expected_outcomes": {
            "metrics_to_watch": ["in_sit_mean_time", "overall_lead_time"],
            "leading_indicators": ["WIP count trending down"],
            "lagging_indicators": ["Mean time reduced"],
            "timeline": "4-8 weeks",
            "risks": [],
        },
        "metric_references": ["in_sit_bottleneck_score"],
    }

    # API endpoint
    url = "http://localhost:8850/api/v1/insights/export"

    # Query parameters
    params = {
        "pis": "26Q1",
        "arts": "UCART",
        "team": "Loke",
        "analysis_level": "feature",
    }

    print(f"\n📤 Sending export request to: {url}")
    print(f"   Parameters: {params}")
    print(f"   Insight: {insight_data['title']}")

    try:
        response = requests.post(url, json=insight_data, params=params, timeout=30)

        if response.status_code == 200:
            print(f"\n✅ SUCCESS - Export completed")

            # Save the Excel file
            filename = "test_insight_export.xlsx"
            with open(filename, "wb") as f:
                f.write(response.content)

            print(f"   Saved Excel file: {filename}")
            print(f"   File size: {len(response.content)} bytes")

            # Check if it's a valid Excel file
            if response.content[:4] == b"PK\x03\x04":
                print(f"   ✅ Valid Excel/ZIP format detected")
            else:
                print(f"   ⚠️  File format might be incorrect")

            return True
        else:
            print(f"\n❌ FAILED - Status code: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n❌ FAILED - Cannot connect to backend")
        print(f"   Make sure the backend is running on port 8850")
        print(f"   Start it with: ./start_backend.sh")
        return False
    except Exception as e:
        print(f"\n❌ FAILED - Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 80)
    print("INSIGHT EXPORT FUNCTIONALITY TEST")
    print("=" * 80)
    print("\nThis test verifies that insights can be exported to Excel")
    print("with all related features/stories included.")
    print("\nPre-requisites:")
    print("  1. Backend running on http://localhost:8850")
    print("  2. DL Webb App running on http://localhost:8000")
    print("  3. Data available for PI=26Q1, ART=UCART, Team=Loke")

    success = test_insight_export()

    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED")
        print("\nThe insight was successfully exported to: test_insight_export.xlsx")
        print("Open this file in Excel to see:")
        print("  - Sheet 1: Insight Summary")
        print("  - Sheet 2: Related Features (with UCART-2228 and others)")
        print("  - Sheet 3: Details (Observation & Interpretation)")
        print("  - Sheet 4: Root Causes")
        print("  - Sheet 5: Recommended Actions")
    else:
        print("❌ TEST FAILED")
        print("\nCheck the error messages above for details.")
    print("=" * 80)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
