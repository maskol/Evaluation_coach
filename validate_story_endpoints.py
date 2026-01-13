"""
Validate DL Webb App Story-Level API Endpoints
This script validates that the story-level endpoints are returning proper data
"""

import sys
import os
import json

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

from integrations.leadtime_client import LeadTimeClient


def validate_story_analysis_summary(data):
    """Validate story_analysis_summary endpoint response"""
    print("\n" + "=" * 80)
    print("VALIDATING: /api/story_analysis_summary")
    print("=" * 80)

    issues = []

    # Check structure
    if not isinstance(data, dict):
        issues.append("❌ Response is not a dictionary")
        return issues

    required_keys = [
        "bottleneck_analysis",
        "story_stages",
        "threshold_days",
        "analysis_date",
    ]
    for key in required_keys:
        if key not in data:
            issues.append(f"❌ Missing required key: {key}")

    # Check bottleneck_analysis
    bottleneck = data.get("bottleneck_analysis", {})
    if not bottleneck:
        issues.append("❌ bottleneck_analysis is empty")
    else:
        print(f"✅ Has bottleneck_analysis")

        # Check stage_analysis
        stage_analysis = bottleneck.get("stage_analysis", {})
        if not stage_analysis:
            issues.append("⚠️  stage_analysis is empty (no stage data)")
        else:
            print(f"✅ stage_analysis has {len(stage_analysis)} stages:")
            for stage_name, stage_data in stage_analysis.items():
                print(f"   - {stage_name}")
                required_metrics = ["mean_time", "median_time", "total_items"]
                missing = [m for m in required_metrics if m not in stage_data]
                if missing:
                    issues.append(f"   ❌ Stage '{stage_name}' missing: {missing}")

        # Check stuck_items
        stuck_items = bottleneck.get("stuck_items", [])
        print(f"✅ stuck_items: {len(stuck_items)} items")
        if len(stuck_items) > 0:
            first_item = stuck_items[0]
            required_fields = ["issue_key", "stage", "days_in_stage"]
            missing = [f for f in required_fields if f not in first_item]
            if missing:
                issues.append(f"   ❌ Stuck item missing fields: {missing}")

        # Check wip_statistics
        wip_stats = bottleneck.get("wip_statistics", {})
        if not wip_stats:
            issues.append("⚠️  wip_statistics is empty")
        else:
            print(f"✅ Has wip_statistics")
            if "total_wip" in wip_stats:
                print(f"   Total WIP: {wip_stats['total_wip']}")

    # Check story_stages
    story_stages = data.get("story_stages", [])
    print(f"✅ story_stages: {len(story_stages)} stages defined")

    return issues


def validate_story_pip_data(data):
    """Validate story_pip_data endpoint response"""
    print("\n" + "=" * 80)
    print("VALIDATING: /api/story_pip_data")
    print("=" * 80)

    issues = []

    # Check structure
    if not isinstance(data, list):
        issues.append("❌ Response is not a list")
        return issues

    if len(data) == 0:
        issues.append("⚠️  No planning data returned")
        return issues

    print(f"✅ Returned {len(data)} record(s)")

    # Check first record
    record = data[0]
    print(f"\n📋 Record structure:")
    print(json.dumps(record, indent=2))

    required_keys = ["pi", "story_metrics"]
    for key in required_keys:
        if key not in record:
            issues.append(f"❌ Missing required key: {key}")

    # Check story_metrics
    if "story_metrics" in record:
        metrics = record["story_metrics"]
        print(f"\n✅ Has story_metrics:")

        expected_metrics = [
            "total_planned",
            "total_delivered",
            "completion_rate",
            "average_lead_time",
        ]

        for metric in expected_metrics:
            if metric in metrics:
                print(f"   ✅ {metric}: {metrics[metric]}")
            else:
                print(f"   ⚠️  {metric}: missing")

    return issues


def validate_story_waste_analysis(data):
    """Validate story_waste_analysis endpoint response"""
    print("\n" + "=" * 80)
    print("VALIDATING: /api/story_waste_analysis")
    print("=" * 80)

    issues = []

    # Check structure
    if not isinstance(data, dict):
        issues.append("❌ Response is not a dictionary")
        return issues

    if "waste_metrics" not in data:
        issues.append("❌ Missing 'waste_metrics' key")
        return issues

    waste_metrics = data["waste_metrics"]
    print(f"✅ Has waste_metrics")

    # Check for expected waste metric keys
    expected_keys = [
        "waiting_time_waste",
        "blocked_stories",
        "stories_exceeding_threshold",
    ]

    for key in expected_keys:
        if key in waste_metrics:
            value = waste_metrics[key]
            if isinstance(value, dict):
                print(f"   ✅ {key}: {len(value)} entries")
            elif isinstance(value, list):
                print(f"   ✅ {key}: {len(value)} items")
            else:
                print(f"   ✅ {key}: {value}")
        else:
            issues.append(f"⚠️  Missing expected key: {key}")

    return issues


def main():
    """Run validation tests"""
    print("\n" + "=" * 80)
    print("DL WEBB APP STORY-LEVEL ENDPOINTS VALIDATION")
    print("=" * 80)
    print("\nChecking if endpoints return complete and valid data...")

    # Initialize client
    client = LeadTimeClient(base_url="http://localhost:8000")

    # Test parameters
    test_params = {
        "arts": ["UCART"],
        "pis": ["26Q1"],
        "team": "Loke",
        "threshold_days": 30,
    }

    all_issues = []

    try:
        # Test 1: Story Analysis Summary
        print("\n📊 Fetching story_analysis_summary...")
        data = client.get_story_analysis_summary(**test_params)
        issues = validate_story_analysis_summary(data)
        all_issues.extend(issues)

    except Exception as e:
        print(f"❌ FAILED to fetch: {e}")
        all_issues.append(f"❌ story_analysis_summary endpoint failed: {e}")

    try:
        # Test 2: Story PIP Data
        print("\n📊 Fetching story_pip_data...")
        data = client.get_story_pip_data(pi="26Q1", art="UCART", team="Loke")
        issues = validate_story_pip_data(data)
        all_issues.extend(issues)

    except Exception as e:
        print(f"❌ FAILED to fetch: {e}")
        all_issues.append(f"❌ story_pip_data endpoint failed: {e}")

    try:
        # Test 3: Story Waste Analysis
        print("\n📊 Fetching story_waste_analysis...")
        data = client.get_story_waste_analysis(
            arts=["UCART"], pis=["26Q1"], team="Loke"
        )
        issues = validate_story_waste_analysis(data)
        all_issues.extend(issues)

    except Exception as e:
        print(f"❌ FAILED to fetch: {e}")
        all_issues.append(f"❌ story_waste_analysis endpoint failed: {e}")

    # Print summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    if not all_issues:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("\nThe DL Webb App story-level endpoints are working correctly!")
        print("All required data structures are present.")
        return 0
    else:
        print(f"\n⚠️  FOUND {len(all_issues)} ISSUE(S):\n")
        for issue in all_issues:
            print(f"  {issue}")

        # Count critical vs warnings
        critical = sum(1 for i in all_issues if i.startswith("❌"))
        warnings = sum(1 for i in all_issues if i.startswith("⚠️"))

        print(f"\n  Critical: {critical}")
        print(f"  Warnings: {warnings}")

        if critical == 0:
            print("\n✅ No critical issues - endpoints are functional")
            print("⚠️  Some optional data may be missing")
            return 0
        else:
            print("\n❌ Critical issues found - endpoints need fixes")
            return 1

    print("=" * 80)


if __name__ == "__main__":
    sys.exit(main())
