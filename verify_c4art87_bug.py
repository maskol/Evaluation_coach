"""
Verify C4ART-87 stuck_items bug in DL Webb APP
"""

import httpx
import json

# Get the raw flow_leadtime data for C4ART-87
response = httpx.get("http://localhost:8000/api/flow_leadtime?limit=100000")
data = response.json()
c4art87 = next((item for item in data if item.get("issue_key") == "C4ART-87"), None)

print("C4ART-87 RAW DATA:")
print("=" * 80)
print(f'Issue Key: {c4art87.get("issue_key")}')
print(f'Status: {c4art87.get("status")}')
print(f'ART: {c4art87.get("art")}')
print(f'PI: {c4art87.get("pi")}')
print(f'in_progress: {c4art87.get("in_progress")} days  ⬅️ THIS IS 255.9 DAYS!')
print(f'total_leadtime: {c4art87.get("total_leadtime")} days')
print()

# Check stuck_items from analysis API
response2 = httpx.get(
    "http://localhost:8000/api/analysis/summary",
    params={
        "pi": ["25Q1", "25Q2", "25Q3", "25Q4"],
        "art": ["C4ART"],
        "threshold_days": "60",
        "include_completed": "true",
    },
)
data2 = response2.json()
stuck_items = data2.get("bottleneck_analysis", {}).get("stuck_items", [])

print("STUCK_ITEMS FROM API:")
print("=" * 80)
print(f"Total stuck items: {len(stuck_items)}")

# Check if C4ART-87 is in stuck_items
c4art87_stuck = [item for item in stuck_items if item.get("issue_key") == "C4ART-87"]
if c4art87_stuck:
    print(f"✅ C4ART-87 FOUND in stuck_items:")
    for item in c4art87_stuck:
        print(f'   Stage: {item.get("stage")}, Days: {item.get("days_in_stage")}')
else:
    print(f"❌ C4ART-87 NOT FOUND in stuck_items!")
    print(
        f"   This is a BUG - it should be there with in_progress: 255.9 days > threshold 60 days"
    )

print()
print("Top 5 stuck items (for comparison):")
sorted_items = sorted(
    stuck_items, key=lambda x: x.get("days_in_stage", 0), reverse=True
)
for i, item in enumerate(sorted_items[:5], 1):
    print(
        f'{i}. {item.get("issue_key")}: {item.get("days_in_stage"):.1f} days in {item.get("stage")} ({item.get("status")})'
    )

print()
print("=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("C4ART-87 has 255.9 days in in_progress stage (> 60 day threshold)")
print("C4ART-87 has status Done (should be included with include_completed=true)")
print("BUT C4ART-87 is MISSING from stuck_items array")
print()
print("This is a BUG in DL Webb APP stuck_items calculation logic.")
