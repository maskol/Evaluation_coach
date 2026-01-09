"""
Verify the fix - test Evaluation Coach API after fixing parameter names
"""

import requests
import json

print("=" * 80)
print("🧪 Testing Evaluation Coach after fix")
print("=" * 80)

# Test via Evaluation Coach API (which should now call DL Webb App correctly)
url = "http://localhost:8850/api/leadtime/bottlenecks"
params = {"arts": "SAART", "pis": "26Q1"}

print(f"\nCalling Evaluation Coach API:")
print(f"URL: {url}")
print(f"Params: {params}")
print("-" * 80)

try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    print("\n📊 RESULTS:")

    # Check in_progress stage
    if "wip_statistics" in data and "in_progress" in data["wip_statistics"]:
        in_prog = data["wip_statistics"]["in_progress"]
        exceeding = in_prog.get("items_exceeding_threshold", 0)
        total = in_prog.get("total_items", 0)
        print(f"   In Progress: {total:,} total items")
        print(f"   Items Exceeding Threshold: {exceeding:,}")

        if exceeding >= 4000 and exceeding <= 6000:
            print(f"\n✅ SUCCESS! Now returning correct filtered data for SAART")
            print(f"   Expected: ~5,000 items")
            print(f"   Got: {exceeding:,} items")
        elif exceeding > 10000:
            print(f"\n❌ STILL BROKEN - Getting unfiltered data")
            print(f"   Expected: ~5,000 items for SAART")
            print(f"   Got: {exceeding:,} items (all ARTs)")
        else:
            print(f"\n⚠️  UNCLEAR - Got {exceeding:,} items")

    # Check stuck items ART
    if "stuck_items" in data and len(data["stuck_items"]) > 0:
        first_art = data["stuck_items"][0].get("art", "Unknown")
        print(f"\n   First stuck item ART: {first_art}")
        if first_art == "SAART":
            print("   ✅ Stuck items correctly filtered to SAART")
        else:
            print(f"   ❌ Stuck items showing {first_art} instead of SAART")

except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to Evaluation Coach")
    print(
        "   Make sure backend is running: cd backend && uvicorn main:app --reload --port 8850"
    )
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "=" * 80)
