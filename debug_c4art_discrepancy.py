"""
Debug script to investigate C4ART 255.9 days discrepancy
"""

import requests
import json

# Query the DL Webb App API for C4ART data
base_url = "http://localhost:8000"

print("🔍 Investigating C4ART discrepancy...")
print("=" * 80)

# Get analysis summary for C4ART
response = requests.get(f"{base_url}/api/analysis/summary", params={"arts": "C4ART"})

if response.status_code != 200:
    print(f"❌ Failed to fetch data: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()

# Check bottleneck analysis
bottleneck = data.get("bottleneck_analysis", {})
stage_analysis = bottleneck.get("stage_analysis", {})
stuck_items = bottleneck.get("stuck_items", [])

print(f"\n📊 Stage Analysis:")
print(f"Total stages: {len(stage_analysis)}")

# Find in_progress stage
in_progress = stage_analysis.get("in_progress", {})
if in_progress:
    print(f"\n🎯 in_progress stage:")
    print(f"   Mean time: {in_progress.get('mean_time', 0):.1f} days")
    print(f"   Max time: {in_progress.get('max_time', 0):.1f} days")
    print(f"   Items exceeding: {in_progress.get('items_exceeding_threshold', 0)}")
    print(f"   Total items: {in_progress.get('total_items', 0)}")

print(f"\n📋 Stuck Items:")
print(f"Total stuck items: {len(stuck_items)}")

# Filter stuck items for in_progress stage
in_progress_stuck = [
    item for item in stuck_items if item.get("stage", "").lower() == "in_progress"
]

print(f"Stuck items in in_progress: {len(in_progress_stuck)}")

# Sort by days_in_stage
in_progress_stuck_sorted = sorted(
    in_progress_stuck, key=lambda x: x.get("days_in_stage", 0), reverse=True
)

print(f"\n🔝 Top 10 stuck items in in_progress:")
for i, item in enumerate(in_progress_stuck_sorted[:10], 1):
    issue_key = item.get("issue_key", "Unknown")
    days = item.get("days_in_stage", 0)
    art = item.get("art", "Unknown")
    print(f"   {i}. {issue_key}: {days:.1f} days (ART: {art})")

# Look for items with ~255-256 days
print(f"\n🔍 Looking for items with 250-260 days:")
high_items = [
    item for item in in_progress_stuck if 250 <= item.get("days_in_stage", 0) <= 260
]

if high_items:
    print(f"Found {len(high_items)} items:")
    for item in high_items:
        print(
            f"   - {item.get('issue_key', 'Unknown')}: {item.get('days_in_stage', 0):.1f} days"
        )
        print(f"     ART: {item.get('art', 'Unknown')}")
        print(f"     Team: {item.get('development_team', 'Unknown')}")
        print(f"     PI: {item.get('pi', 'Unknown')}")
else:
    print("   ❌ No items found in this range!")

# Check if max_time matches highest stuck item
if in_progress_stuck_sorted:
    highest_stuck_days = in_progress_stuck_sorted[0].get("days_in_stage", 0)
    max_time_from_stage = in_progress.get("max_time", 0)

    print(f"\n⚠️  Discrepancy Check:")
    print(f"   Max time from stage_analysis: {max_time_from_stage:.1f} days")
    print(f"   Highest stuck item: {highest_stuck_days:.1f} days")

    if abs(max_time_from_stage - highest_stuck_days) > 1:
        print(
            f"   ❌ MISMATCH! Difference: {abs(max_time_from_stage - highest_stuck_days):.1f} days"
        )
        print(
            f"\n💡 This suggests the feature with {max_time_from_stage:.1f} days is not in stuck_items!"
        )
    else:
        print(f"   ✅ Match - data is consistent")

print("\n" + "=" * 80)
