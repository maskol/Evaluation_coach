"""
Debug script for story-level insights API error

This script helps diagnose the 500 error when calling story-level insights
"""

import sys
import os
import traceback

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

from integrations.leadtime_client import LeadTimeClient


def test_story_endpoints():
    """Test the story-level API endpoints directly"""
    print("\n" + "=" * 80)
    print("TESTING STORY-LEVEL API ENDPOINTS")
    print("=" * 80)

    # Initialize client
    client = LeadTimeClient(base_url="http://localhost:8000")

    # Test parameters from the error
    test_params = {
        "arts": ["UCART"],
        "pis": ["26Q1"],
        "team": "Loke",
        "threshold_days": 30,
    }

    print(f"\nTest parameters: {test_params}")

    # Test 1: Story Analysis Summary
    print("\n" + "-" * 80)
    print("TEST 1: get_story_analysis_summary()")
    print("-" * 80)
    try:
        result = client.get_story_analysis_summary(**test_params)
        print(f"✅ SUCCESS - Returned: {type(result)}")
        if isinstance(result, dict):
            print(f"   Keys: {list(result.keys())}")
            bottleneck = result.get("bottleneck_analysis", {})
            if bottleneck:
                print(f"   Has bottleneck_analysis: {list(bottleneck.keys())}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        traceback.print_exc()

    # Test 2: Story PIP Data (requires PI parameter)
    print("\n" + "-" * 80)
    print("TEST 2: get_story_pip_data()")
    print("-" * 80)
    try:
        pip_params = {"pi": "26Q1", "art": "UCART", "team": "Loke"}
        result = client.get_story_pip_data(**pip_params)
        print(f"✅ SUCCESS - Returned: {type(result)}")
        if isinstance(result, list):
            print(f"   Count: {len(result)} records")
            if result:
                print(f"   First record keys: {list(result[0].keys())}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        traceback.print_exc()

    # Test 3: Story Waste Analysis
    print("\n" + "-" * 80)
    print("TEST 3: get_story_waste_analysis()")
    print("-" * 80)
    try:
        waste_params = {"arts": ["UCART"], "pis": ["26Q1"], "team": "Loke"}
        result = client.get_story_waste_analysis(**waste_params)
        print(f"✅ SUCCESS - Returned: {type(result)}")
        if isinstance(result, dict):
            print(f"   Keys: {list(result.keys())}")
            waste_metrics = result.get("waste_metrics", {})
            if waste_metrics:
                print(f"   Has waste_metrics: {list(waste_metrics.keys())}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        traceback.print_exc()

    print("\n" + "=" * 80)


def test_story_insights_generation():
    """Test the full story insights generation flow"""
    print("\n" + "=" * 80)
    print("TESTING STORY INSIGHTS GENERATION FLOW")
    print("=" * 80)

    from agents.nodes.story_insights import generate_story_insights

    # Get real data from API
    client = LeadTimeClient(base_url="http://localhost:8000")

    test_params = {
        "arts": ["UCART"],
        "pis": ["26Q1"],
        "team": "Loke",
        "threshold_days": 30,
    }

    try:
        # Get story data
        print("\n📊 Fetching story analysis data...")
        story_analysis_summary = client.get_story_analysis_summary(**test_params)
        print(f"✅ Got analysis summary")

        print("\n📊 Fetching story planning data...")
        story_pip_data = client.get_story_pip_data(pi="26Q1", art="UCART", team="Loke")
        print(
            f"✅ Got planning data: {len(story_pip_data) if isinstance(story_pip_data, list) else 'N/A'} records"
        )

        print("\n📊 Fetching story waste data...")
        story_waste_analysis = client.get_story_waste_analysis(
            arts=["UCART"], pis=["26Q1"], team="Loke"
        )
        print(f"✅ Got waste data")

        # Generate insights
        print("\n🤖 Generating insights...")
        insights = generate_story_insights(
            story_analysis_summary=story_analysis_summary,
            story_pip_data=story_pip_data,
            story_waste_analysis=story_waste_analysis,
            selected_arts=["UCART"],
            selected_pis=["26Q1"],
            selected_team="Loke",
            llm_service=None,
        )

        print(f"\n✅ Generated {len(insights)} insights")

        for i, insight in enumerate(insights, 1):
            print(f"\n  Insight {i}:")
            print(f"    Title: {insight.title}")
            print(f"    Severity: {insight.severity}")
            print(f"    Confidence: {insight.confidence}")

        print("\n" + "=" * 80)
        print("✅ STORY INSIGHTS GENERATION SUCCESSFUL")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        traceback.print_exc()
        print("\n" + "=" * 80)
        print("❌ STORY INSIGHTS GENERATION FAILED")
        print("=" * 80)


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("STORY-LEVEL INSIGHTS API DEBUG")
    print("=" * 80)
    print("\nThis script tests the story-level API endpoints to diagnose")
    print("the 500 error when generating story-level insights.")
    print("\nPre-requisites:")
    print("  1. DL Webb App backend running on http://localhost:8000")
    print("  2. Story data exists for PI=26Q1, ART=UCART, Team=Loke")

    try:
        test_story_endpoints()
        test_story_insights_generation()

        print("\n" + "=" * 80)
        print("DEBUG COMPLETE")
        print("=" * 80)
        print("\nIf all tests passed, the issue may be in:")
        print("  1. Backend configuration (check LEADTIME_SERVER_URL)")
        print("  2. Network connectivity to DL Webb App")
        print("  3. Data availability in DL Webb App database")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
