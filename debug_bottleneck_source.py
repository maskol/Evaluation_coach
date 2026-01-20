import json
import subprocess

result = subprocess.run(
    [
        "curl",
        "-s",
        "http://localhost:8000/api/analysis/summary?arts=C4ART&pis=25Q1,25Q2,25Q3,25Q4",
    ],
    capture_output=True,
    text=True,
)

data = json.loads(result.stdout)
bottleneck = data.get("bottleneck_analysis", {})

# Check bottleneck_stages
stages = bottleneck.get("bottleneck_stages", [])
print(f"🎯 Bottleneck stages count: {len(stages)}")

in_prog_stages = [s for s in stages if s.get("stage") == "in_progress"]
if in_prog_stages:
    s = in_prog_stages[0]
    print(f"\n✅ in_progress bottleneck stage:")
    print(f"   Score: {s.get('bottleneck_score', 0):.1f}%")
    print(f"   Mean time: {s.get('mean_time', 0):.1f} days")
    print(f"   Max time: {s.get('max_time', 0):.1f} days")
    print(f"   Items exceeding: {s.get('items_exceeding_threshold', 0)}")
else:
    print("\n❌ in_progress not found in bottleneck_stages")

# Check stuck_items
stuck_items = bottleneck.get("stuck_items", [])
in_prog_stuck = [s for s in stuck_items if s.get("stage", "").lower() == "in_progress"]
print(f"\n📋 Stuck items in in_progress: {len(in_prog_stuck)}")

if in_prog_stuck:
    sorted_stuck = sorted(
        in_prog_stuck, key=lambda x: x.get("days_in_stage", 0), reverse=True
    )
    print(f"\n🔝 Top 5:")
    for i, item in enumerate(sorted_stuck[:5], 1):
        print(
            f"   {i}. {item.get('issue_key', '?')}: {item.get('days_in_stage', 0):.1f} days"
        )

# The key question: Where does the insight get its max_time from?
print(f"\n💡 Analysis:")
print(f"   The insight observation shows max: 256 days")
print(
    f"   But stuck_items highest is: {sorted_stuck[0].get('days_in_stage', 0):.1f} days"
    if sorted_stuck
    else "   No stuck items!"
)
print(
    f"   bottleneck_stages max_time is: {in_prog_stages[0].get('max_time', 0):.1f} days"
    if in_prog_stages
    else "   No bottleneck_stages!"
)
