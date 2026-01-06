"""
Test script to verify strategic targets functionality
This script tests:
1. Loading configuration with strategic targets
2. Updating strategic targets via API
3. Generating insights that analyze against targets
"""

import asyncio
import json

import requests

# Configuration
API_BASE_URL = "http://localhost:8850"


def test_get_config():
    """Test fetching current configuration"""
    print("=" * 70)
    print("TEST 1: Fetching Current Configuration")
    print("=" * 70)

    response = requests.get(f"{API_BASE_URL}/api/admin/config")
    if response.status_code == 200:
        config = response.json()
        print("✅ Configuration fetched successfully")
        print(f"\n📊 Strategic Targets:")
        print(
            f"  Feature Lead-Time 2026: {config['thresholds'].get('leadtime_target_2026', 'Not set')}"
        )
        print(
            f"  Feature Lead-Time 2027: {config['thresholds'].get('leadtime_target_2027', 'Not set')}"
        )
        print(
            f"  Feature Lead-Time True North: {config['thresholds'].get('leadtime_target_true_north', 'Not set')}"
        )
        print(
            f"  Planning Accuracy 2026: {config['thresholds'].get('planning_accuracy_target_2026', 'Not set')}%"
        )
        print(
            f"  Planning Accuracy 2027: {config['thresholds'].get('planning_accuracy_target_2027', 'Not set')}%"
        )
        print(
            f"  Planning Accuracy True North: {config['thresholds'].get('planning_accuracy_target_true_north', 'Not set')}%"
        )
        return config
    else:
        print(f"❌ Failed to fetch configuration: {response.status_code}")
        print(response.text)
        return None


def test_update_targets():
    """Test updating strategic targets"""
    print("\n" + "=" * 70)
    print("TEST 2: Updating Strategic Targets")
    print("=" * 70)

    # Sample targets
    new_targets = {
        "bottleneck_threshold_days": 7.0,
        "planning_accuracy_threshold_pct": 70.0,
        # Strategic targets
        "leadtime_target_2026": 35.0,
        "leadtime_target_2027": 25.0,
        "leadtime_target_true_north": 15.0,
        "planning_accuracy_target_2026": 80.0,
        "planning_accuracy_target_2027": 85.0,
        "planning_accuracy_target_true_north": 90.0,
        # Stage overrides can be null
        "threshold_in_backlog": None,
        "threshold_in_analysis": None,
        "threshold_in_planned": None,
        "threshold_in_progress": None,
        "threshold_in_reviewing": None,
        "threshold_ready_for_sit": None,
        "threshold_in_sit": None,
        "threshold_ready_for_uat": None,
        "threshold_in_uat": None,
        "threshold_ready_for_deployment": None,
    }

    print("\n📝 Sending update request with targets:")
    print(f"  Feature Lead-Time 2026: {new_targets['leadtime_target_2026']} days")
    print(f"  Feature Lead-Time 2027: {new_targets['leadtime_target_2027']} days")
    print(
        f"  Feature Lead-Time True North: {new_targets['leadtime_target_true_north']} days"
    )
    print(f"  Planning Accuracy 2026: {new_targets['planning_accuracy_target_2026']}%")
    print(f"  Planning Accuracy 2027: {new_targets['planning_accuracy_target_2027']}%")
    print(
        f"  Planning Accuracy True North: {new_targets['planning_accuracy_target_true_north']}%"
    )

    response = requests.post(
        f"{API_BASE_URL}/api/admin/config/thresholds",
        json=new_targets,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ {result['message']}")
        return True
    else:
        print(f"\n❌ Failed to update targets: {response.status_code}")
        print(response.text)
        return False


def test_insights_with_targets():
    """Test generating insights that use strategic targets"""
    print("\n" + "=" * 70)
    print("TEST 3: Generating Insights with Strategic Targets")
    print("=" * 70)

    # First, ensure targets are set
    test_update_targets()

    # Now request insights
    print("\n🤖 Requesting AI insights...")
    insight_request = {
        "scope": "portfolio",
        "scope_id": None,
        "time_range": "last_pi",
        "metric_focus": None,
    }

    response = requests.post(
        f"{API_BASE_URL}/api/insights",
        json=insight_request,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        insights = response.json()
        print(f"✅ Generated {len(insights)} insights")

        # Look for strategic target insights
        strategic_insights = [
            i
            for i in insights
            if "Strategic Targets" in i.get("title", "")
            or "vs Strategic Targets" in i.get("title", "")
        ]

        if strategic_insights:
            print(f"\n📊 Found {len(strategic_insights)} strategic target insights:")
            for insight in strategic_insights:
                print(f"\n  Title: {insight['title']}")
                print(f"  Severity: {insight['severity']}")
                print(f"  Confidence: {insight['confidence']}%")
                print(f"  Observation: {insight['observation'][:150]}...")
                print(f"  Interpretation: {insight['interpretation'][:150]}...")
        else:
            print("\n⚠️  No strategic target insights found")
            print(
                "This may be because targets were not configured before insight generation"
            )

        return insights
    else:
        print(f"❌ Failed to generate insights: {response.status_code}")
        print(response.text)
        return None


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 STRATEGIC TARGETS INTEGRATION TEST SUITE")
    print("=" * 70)
    print("\nEnsure the backend server is running at http://localhost:8850")
    print("Starting tests...\n")

    try:
        # Test 1: Get current config
        config = test_get_config()
        if not config:
            print("\n❌ Cannot proceed without configuration")
            return

        # Test 2: Update targets
        success = test_update_targets()
        if not success:
            print("\n❌ Failed to update targets")
            return

        # Test 3: Verify config was updated
        print("\n" + "=" * 70)
        print("TEST 2b: Verifying Configuration Update")
        print("=" * 70)
        config = test_get_config()

        # Test 4: Generate insights
        insights = test_insights_with_targets()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Open http://localhost:8800/admin.html")
        print("2. Verify the strategic target fields are visible")
        print("3. Enter target values and save")
        print("4. Navigate to dashboard and check insights for target analysis")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend server")
        print("Please ensure the server is running at http://localhost:8850")
        print("Run: ./start.sh")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
