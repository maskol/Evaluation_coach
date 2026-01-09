#!/usr/bin/env python3
"""
Test script to verify get_analysis_summary() returns correct filtered data
"""
import sys

sys.path.append("backend")

from integrations.leadtime_client import LeadTimeClient

print("=" * 80)
print("🧪 Testing get_analysis_summary() with SAART PI 26Q1")
print("=" * 80)

client = LeadTimeClient(base_url="http://localhost:8000")

# Test with SAART and PI 26Q1
print("\nCalling: get_analysis_summary(arts=['SAART'], pis=['26Q1'])")
print("-" * 80)

summary = client.get_analysis_summary(arts=["SAART"], pis=["26Q1"])

# Extract bottleneck data
bottleneck = summary.get("bottleneck_analysis", {})
bottleneck_stages = bottleneck.get("bottleneck_stages", [])

if bottleneck_stages:
    top_stage = bottleneck_stages[0]
    print(f"\n✅ Top bottleneck stage: {top_stage['stage']}")
    print(
        f"   Stage occurrences exceeding threshold: {top_stage['items_exceeding_threshold']}"
    )
    print(f"   Bottleneck score: {top_stage['bottleneck_score']:.1f}")

    if top_stage["items_exceeding_threshold"] == 5026:
        print(
            f"\n🎯 SUCCESS! Correct filtered data: {top_stage['items_exceeding_threshold']} stage occurrences"
        )
        print("   (Not the incorrect 27,751 unfiltered count)")
    else:
        print(
            f"\n❌ UNEXPECTED: Got {top_stage['items_exceeding_threshold']} instead of expected 5,026"
        )
else:
    print("\n❌ ERROR: No bottleneck stages found in response")

print("\n" + "=" * 80)
