"""
Debug script to test different API parameter formats for DL Webb App bottleneck endpoint
"""

import requests
import json

# Test different parameter combinations to find the issue
test_cases = [
    {
        "name": "Test 1: arts + pis (current approach)",
        "params": {"arts": "SAART", "pis": "26Q1"},
    },
    {
        "name": "Test 2: art (singular) + pi (singular)",
        "params": {"art": "SAART", "pi": "26Q1"},
    },
    {"name": "Test 3: arts only (no PI)", "params": {"arts": "SAART"}},
    {"name": "Test 4: art only (no PI)", "params": {"art": "SAART"}},
    {
        "name": "Test 5: arts + threshold_days",
        "params": {"arts": "SAART", "threshold_days": 7},
    },
]

url = "http://localhost:8000/api/analysis/bottlenecks"

for test_case in test_cases:
    print("\n" + "=" * 80)
    print(f"🧪 {test_case['name']}")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Params: {test_case['params']}")
    print("-" * 80)

    try:
        response = requests.get(url, params=test_case["params"], timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract key info
        print("\n📊 SUMMARY:")

        # Top bottleneck stage
        if "bottleneck_stages" in data and len(data["bottleneck_stages"]) > 0:
            top = data["bottleneck_stages"][0]
            print(f"   Top Bottleneck: {top.get('stage')}")
            print(f"   Items Exceeding: {top.get('items_exceeding_threshold'):,}")

        # WIP in_progress stats
        if "wip_statistics" in data and "in_progress" in data["wip_statistics"]:
            in_prog = data["wip_statistics"]["in_progress"]
            exceeding = in_prog.get("items_exceeding_threshold", 0)
            total = in_prog.get("total_items", 0)
            print(f"   In Progress: {total:,} total, {exceeding:,} exceeding threshold")

        # Stuck items
        if "stuck_items" in data:
            stuck_count = len(data["stuck_items"])
            print(f"   Stuck Items: {stuck_count}")
            if stuck_count > 0:
                first_art = data["stuck_items"][0].get("art", "Unknown")
                print(f"   First item ART: {first_art}")

        # Result check
        print("\n✅ RESULT:")
        if "wip_statistics" in data and "in_progress" in data["wip_statistics"]:
            exceeding = data["wip_statistics"]["in_progress"].get(
                "items_exceeding_threshold", 0
            )
            if exceeding > 10000:
                print(f"   ❌ FAILED - Got {exceeding:,} items (unfiltered data)")
            elif exceeding >= 4000 and exceeding <= 6000:
                print(
                    f"   ✅ SUCCESS - Got {exceeding:,} items (properly filtered for SAART)"
                )
            else:
                print(f"   ⚠️  UNCLEAR - Got {exceeding:,} items")

    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Could not connect to DL Webb App")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 80)
print("🎯 CONCLUSION")
print("=" * 80)
print("Compare the results above to identify which parameter format works correctly.")
print("Expected for SAART: ~5,000-6,000 items exceeding threshold in 'in_progress'")
