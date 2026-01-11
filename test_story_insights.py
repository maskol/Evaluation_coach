"""
Test script for story-level insights implementation

This script tests:
1. LeadTimeClient story-level API methods
2. Story insights generator
3. Integration with main API endpoint
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

from integrations.leadtime_client import LeadTimeClient
from agents.nodes.story_insights import generate_story_insights


def test_leadtime_client_story_methods():
    """Test that LeadTimeClient has story-level methods"""
    print("\n" + "=" * 80)
    print("TEST 1: LeadTimeClient Story Methods")
    print("=" * 80)

    client = LeadTimeClient(base_url="http://localhost:8000")

    # Check methods exist
    assert hasattr(
        client, "get_story_analysis_summary"
    ), "Missing get_story_analysis_summary method"
    assert hasattr(client, "get_story_pip_data"), "Missing get_story_pip_data method"
    assert hasattr(
        client, "get_story_waste_analysis"
    ), "Missing get_story_waste_analysis method"

    print("✅ All story-level API methods exist on LeadTimeClient")


def test_story_insights_generator():
    """Test that story insights generator can be imported and has correct signature"""
    print("\n" + "=" * 80)
    print("TEST 2: Story Insights Generator")
    print("=" * 80)

    # Test with empty data
    test_summary = {
        "bottleneck_analysis": {
            "stage_analysis": {},
            "stuck_items": [],
            "wip_statistics": {},
        }
    }

    test_pip_data = []
    test_waste = {"waste_metrics": {}}

    insights = generate_story_insights(
        story_analysis_summary=test_summary,
        story_pip_data=test_pip_data,
        story_waste_analysis=test_waste,
        selected_arts=None,
        selected_pis=None,
        selected_team=None,
    )

    assert isinstance(insights, list), "generate_story_insights should return a list"
    print(
        f"✅ Story insights generator works - returned {len(insights)} insights (empty data)"
    )


def test_story_insights_with_data():
    """Test story insights with sample data"""
    print("\n" + "=" * 80)
    print("TEST 3: Story Insights with Sample Data")
    print("=" * 80)

    # Sample data simulating API response
    test_summary = {
        "bottleneck_analysis": {
            "stage_analysis": {
                "in_development": {
                    "mean_time": 7.5,
                    "max_time": 15.0,
                    "items_exceeding_threshold": 5,
                },
                "in_review": {
                    "mean_time": 3.2,
                    "max_time": 8.0,
                    "items_exceeding_threshold": 3,
                },
            },
            "stuck_items": [
                {
                    "issue_key": "STORY-123",
                    "stage": "in_development",
                    "days_in_stage": 12,
                },
                {
                    "issue_key": "STORY-456",
                    "stage": "in_review",
                    "days_in_stage": 6,
                },
            ],
            "wip_statistics": {
                "total_active_stories": 18,
            },
            "flow_distribution": {
                "in_development": 8,
                "in_review": 5,
                "in_testing": 5,
            },
        }
    }

    test_pip_data = [
        {
            "art_name": "UCART",
            "development_team": "Loke",
            "pi": "26Q1",
            "story_metrics": {
                "planned_stories": 50,
                "completed_stories": 35,
                "completion_rate": 70.0,
            },
        }
    ]

    test_waste = {
        "waste_metrics": {
            "blocked_stories": {
                "count": 4,
                "total_blocked_days": 28.0,
            }
        }
    }

    insights = generate_story_insights(
        story_analysis_summary=test_summary,
        story_pip_data=test_pip_data,
        story_waste_analysis=test_waste,
        selected_arts=["UCART"],
        selected_pis=["26Q1"],
        selected_team="Loke",
    )

    assert isinstance(insights, list), "Should return list of insights"
    print(f"✅ Generated {len(insights)} insights from sample data")

    # Print insight details
    for i, insight in enumerate(insights, 1):
        print(f"\n  Insight {i}:")
        print(f"    Title: {insight.title}")
        print(f"    Severity: {insight.severity}")
        print(f"    Confidence: {insight.confidence}")
        print(f"    Actions: {len(insight.recommended_actions)}")


def test_integration_imports():
    """Test that main.py can import the story insights module"""
    print("\n" + "=" * 80)
    print("TEST 4: Integration - Import Check")
    print("=" * 80)

    try:
        from agents.nodes.story_insights import generate_story_insights

        print("✅ Story insights can be imported from main application")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        raise


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("STORY-LEVEL INSIGHTS IMPLEMENTATION TEST SUITE")
    print("=" * 80)

    try:
        test_leadtime_client_story_methods()
        test_story_insights_generator()
        test_story_insights_with_data()
        test_integration_imports()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nStory-level insights implementation is ready!")
        print("\nNext steps:")
        print("1. Start the Evaluation Coach backend server")
        print("2. Select 'Story Level' in the analysis dropdown")
        print("3. View story-level insights in the dashboard")
        print("\nEndpoints used:")
        print("  - GET /api/story_analysis_summary")
        print("  - GET /api/story_pip_data")
        print("  - GET /api/story_waste_analysis")

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 80)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
