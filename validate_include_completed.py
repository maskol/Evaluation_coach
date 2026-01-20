"""
Comprehensive validation that the include_completed feature is working correctly
"""

import httpx

print("=" * 80)
print("COMPREHENSIVE VALIDATION: Include Completed Items Feature")
print("=" * 80)
print()

client = httpx.Client(base_url="http://localhost:8000")

# Test 1: Without include_completed (should exclude completed items)
print("Test 1: Historical PIs WITHOUT include_completed")
print("-" * 80)
response1 = client.get(
    "/api/analysis/summary",
    params={
        "pi": ["25Q1", "25Q2", "25Q3", "25Q4"],
        "art": ["C4ART"],
        "threshold_days": "60",
    },
)
data1 = response1.json()
stuck_items1 = data1.get("bottleneck_analysis", {}).get("stuck_items", [])
max1 = (
    data1.get("bottleneck_analysis", {})
    .get("stage_analysis", {})
    .get("in_progress", {})
    .get("max_time", 0)
)

print(f"Max time in stage_analysis: {max1:.1f} days")
print(f"Stuck items returned: {len(stuck_items1)}")
if stuck_items1:
    top = stuck_items1[0]
    print(
        f"Top stuck item: {top.get('issue_key')}: {top.get('days_in_stage'):.1f} days ({top.get('status')})"
    )
else:
    print("No stuck items (correct for current behavior without parameter)")
print()

# Test 2: With include_completed=true (should include completed items)
print("Test 2: Historical PIs WITH include_completed=true")
print("-" * 80)
response2 = client.get(
    "/api/analysis/summary",
    params={
        "pi": ["25Q1", "25Q2", "25Q3", "25Q4"],
        "art": ["C4ART"],
        "threshold_days": "60",
        "include_completed": "true",
    },
)
data2 = response2.json()
stuck_items2 = data2.get("bottleneck_analysis", {}).get("stuck_items", [])
max2 = (
    data2.get("bottleneck_analysis", {})
    .get("stage_analysis", {})
    .get("in_progress", {})
    .get("max_time", 0)
)

print(f"Max time in stage_analysis: {max2:.1f} days")
print(f"Stuck items returned: {len(stuck_items2)}")
print(f"\nTop 5 stuck items:")
for i, item in enumerate(stuck_items2[:5], 1):
    print(
        f"  {i}. {item.get('issue_key')}: {item.get('days_in_stage'):.1f} days in {item.get('stage')} ({item.get('status')})"
    )

# Check for C4ART-87
c4art87 = next(
    (item for item in stuck_items2 if item.get("issue_key") == "C4ART-87"), None
)
print()
if c4art87:
    print(
        f"✅ C4ART-87 FOUND: {c4art87.get('days_in_stage'):.1f} days in {c4art87.get('stage')}"
    )
else:
    print(f"❌ C4ART-87 NOT FOUND")

print()
print("=" * 80)
print("VALIDATION RESULTS")
print("=" * 80)

checks = []

# Check 1: Parameter controls behavior
check1 = len(stuck_items2) > len(stuck_items1)
checks.append(("include_completed parameter controls stuck_items filtering", check1))

# Check 2: C4ART-87 appears with include_completed=true
check2 = c4art87 is not None
checks.append(("C4ART-87 appears in stuck_items with include_completed=true", check2))

# Check 3: C4ART-87 is the top item
check3 = stuck_items2[0].get("issue_key") == "C4ART-87" if stuck_items2 else False
checks.append(("C4ART-87 is the #1 stuck item (highest days)", check3))

# Check 4: Days match
check4 = abs(c4art87.get("days_in_stage", 0) - 255.9) < 1 if c4art87 else False
checks.append(("C4ART-87 has correct days_in_stage (~255.9)", check4))

# Check 5: Stage is in_progress
check5 = c4art87.get("stage") == "in_progress" if c4art87 else False
checks.append(("C4ART-87 stage is 'in_progress'", check5))

# Check 6: Max time is consistent
check6 = abs(max2 - 255.9) < 10  # Allow some variance
checks.append(("Max time in stage_analysis matches C4ART-87", check6))

print()
for check_name, passed in checks:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {check_name}")

print()
all_passed = all(passed for _, passed in checks)
if all_passed:
    print("=" * 80)
    print("🎉 ALL CHECKS PASSED!")
    print("=" * 80)
    print()
    print("The 'Include Completed Items' feature is FULLY WORKING!")
    print()
    print("Users analyzing historical PIs will now see:")
    print("- C4ART-87: 255.9 days in in_progress (Done)")
    print("- Complete historical context for bottleneck analysis")
    print("- Ability to investigate the actual worst-case items")
    print()
    print("✅ Feature Status: COMPLETE and VALIDATED")
else:
    print("=" * 80)
    print("⚠️  SOME CHECKS FAILED")
    print("=" * 80)
    print("Please review the failed checks above.")
