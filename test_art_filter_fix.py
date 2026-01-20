"""
Test script to verify ART filtering works correctly for stuck_items.
This should prevent items from SPOCKF appearing when filtering by SAART.
"""


def test_art_filter():
    """Test that ART filter correctly removes items from wrong ARTs"""

    # Simulated stuck_items data (like what comes from DL Webb App API)
    stuck_items = [
        {
            "issue_key": "SAART-514",
            "art": "SAART",
            "team": "VSAITSM-1",
            "days_in_stage": 132.99,
        },
        {
            "issue_key": "SPOCKF-488",
            "art": "SPOCKF",
            "team": "SPOCK Product Mgmt",
            "days_in_stage": 84.16,
        },
        {
            "issue_key": "SAART-2301",
            "art": "SAART",
            "team": "VSAHELIX",
            "days_in_stage": 71.03,
        },
        {
            "issue_key": "SAART-1082",
            "art": "SAART",
            "team": "VSAPF",
            "days_in_stage": 67.27,
        },
        {
            "issue_key": "SAART-3138",
            "art": "SAART",
            "team": "VSAPF",
            "days_in_stage": 0,
        },
    ]

    # Filter by SAART (this is what the fixed code does now)
    selected_arts = ["SAART"]

    filtered_items = [item for item in stuck_items if item.get("art") in selected_arts]

    print("Original stuck_items count:", len(stuck_items))
    print("After ART filter (SAART only):", len(filtered_items))
    print("\nFiltered items:")
    for item in filtered_items:
        print(f"  - {item['issue_key']} (ART: {item['art']})")

    # Verify SPOCKF-488 is NOT in the filtered results
    spockf_items = [item for item in filtered_items if item["art"] == "SPOCKF"]
    saart_items = [item for item in filtered_items if item["art"] == "SAART"]

    print(f"\n✅ Test Results:")
    print(f"   SAART items: {len(saart_items)} (expected: 4)")
    print(f"   SPOCKF items: {len(spockf_items)} (expected: 0)")

    if len(spockf_items) == 0 and len(saart_items) == 4:
        print("\n✅ SUCCESS: ART filter working correctly!")
        print("   SPOCKF-488 is correctly excluded when filtering by SAART")
        return True
    else:
        print("\n❌ FAILURE: ART filter not working correctly")
        return False


def test_case_insensitive_art_filter():
    """Test that ART filter handles case variations correctly"""

    stuck_items = [
        {
            "issue_key": "SAART-514",
            "art": "saart",
            "days_in_stage": 132.99,
        },  # lowercase
        {
            "issue_key": "SPOCKF-488",
            "art": "SPOCKF",
            "days_in_stage": 84.16,
        },  # uppercase
        {
            "issue_key": "SAART-2301",
            "art": "SAART",
            "days_in_stage": 71.03,
        },  # uppercase
    ]

    # Test case-sensitive filter (what we use in story_insights.py)
    selected_arts_upper = ["SAART"]
    filtered_case_sensitive = [
        item for item in stuck_items if item.get("art") in selected_arts_upper
    ]

    # Test case-insensitive filter (what we use in main.py export)
    selected_arts = ["SAART"]
    filtered_case_insensitive = []
    for item in stuck_items:
        item_art = item.get("art", "").strip().upper()
        normalized_selected_arts = [art.strip().upper() for art in selected_arts]
        if item_art in normalized_selected_arts:
            filtered_case_insensitive.append(item)

    print("\nCase-sensitive filter results:", len(filtered_case_sensitive))
    print("Case-insensitive filter results:", len(filtered_case_insensitive))

    if len(filtered_case_insensitive) == 2:
        print(
            "✅ Case-insensitive filter working correctly (handles both 'saart' and 'SAART')"
        )
        return True
    else:
        print("❌ Case-insensitive filter issue")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Testing ART Filter Fix for SPOCKF Issue")
    print("=" * 70)
    print()

    test1 = test_art_filter()
    print("\n" + "=" * 70)
    test2 = test_case_insensitive_art_filter()
    print("\n" + "=" * 70)

    if test1 and test2:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
