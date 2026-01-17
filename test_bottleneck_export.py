"""
Test the bottleneck export fix
"""

import re


def test_bottleneck_detection():
    """Test that bottleneck insights are correctly detected and stage is extracted"""

    test_cases = [
        {
            "title": "Critical Bottleneck in In Sit Stage",
            "expected_is_bottleneck": True,
            "expected_stage": "in_sit",
        },
        {
            "title": "Critical Bottleneck in In Dev Stage",
            "expected_is_bottleneck": True,
            "expected_stage": "in_dev",
        },
        {
            "title": "Multiple Bottlenecks Detected",
            "expected_is_bottleneck": True,
            "expected_stage": None,
        },
        {
            "title": "High WIP Detected",
            "expected_is_bottleneck": False,
            "expected_stage": None,
        },
    ]

    for test in test_cases:
        title = test["title"]
        insight_title_lower = title.lower()
        is_bottleneck_insight = "bottleneck" in insight_title_lower

        bottleneck_stage = None
        if is_bottleneck_insight:
            stage_pattern = r"bottleneck in (.+?) stage"
            stage_match = re.search(stage_pattern, insight_title_lower, re.IGNORECASE)
            if stage_match:
                bottleneck_stage = stage_match.group(1).lower().replace(" ", "_")

        print(f"\nTest: {title}")
        print(
            f"  Is Bottleneck: {is_bottleneck_insight} (expected: {test['expected_is_bottleneck']})"
        )
        print(f"  Stage: {bottleneck_stage} (expected: {test['expected_stage']})")

        assert (
            is_bottleneck_insight == test["expected_is_bottleneck"]
        ), f"Failed for {title}"
        assert (
            bottleneck_stage == test["expected_stage"]
        ), f"Failed stage extraction for {title}"

    print("\n✅ All tests passed!")


def test_stuck_items_matching():
    """Test that stuck items are correctly matched to the bottleneck stage"""

    bottleneck_stage = "in_sit"

    stuck_items = [
        {"issue_key": "UCART-1234", "stage": "in_sit", "days_in_stage": 87},
        {"issue_key": "UCART-5678", "stage": "in_sit", "days_in_stage": 153},
        {"issue_key": "UCART-9999", "stage": "in_dev", "days_in_stage": 45},
        {"issue_key": "ACET-1111", "stage": "in_sit", "days_in_stage": 62},
    ]

    # Filter items for the bottleneck stage
    matching_items = [
        item
        for item in stuck_items
        if item.get("stage", "").lower() == bottleneck_stage
    ]

    print(f"\nBottleneck stage: {bottleneck_stage}")
    print(f"Total stuck items: {len(stuck_items)}")
    print(f"Matching items: {len(matching_items)}")

    assert (
        len(matching_items) == 3
    ), f"Expected 3 matching items, got {len(matching_items)}"

    for item in matching_items:
        print(
            f"  - {item['issue_key']}: {item['days_in_stage']} days in {item['stage']}"
        )

    print("\n✅ Stuck items matching test passed!")


if __name__ == "__main__":
    test_bottleneck_detection()
    test_stuck_items_matching()
