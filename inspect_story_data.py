"""
Inspect the actual data structure returned by story endpoints
"""

import sys
import os
import json

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

from integrations.leadtime_client import LeadTimeClient


def inspect_story_analysis_summary():
    """Inspect the actual structure of story_analysis_summary"""
    print("\n" + "=" * 80)
    print("INSPECTING: story_analysis_summary DATA")
    print("=" * 80)

    client = LeadTimeClient(base_url="http://localhost:8000")

    data = client.get_story_analysis_summary(
        arts=["UCART"], pis=["26Q1"], team="Loke", threshold_days=30
    )

    print("\n📋 FULL RESPONSE:")
    print(json.dumps(data, indent=2, default=str))

    # Focus on stage_analysis
    print("\n" + "=" * 80)
    print("STAGE ANALYSIS DETAIL")
    print("=" * 80)

    stage_analysis = data.get("bottleneck_analysis", {}).get("stage_analysis", {})

    if not stage_analysis:
        print("⚠️  No stage analysis data")
        return

    for stage_name, stage_data in stage_analysis.items():
        print(f"\n📊 Stage: {stage_name}")
        print(f"   Keys present: {list(stage_data.keys())}")
        for key, value in stage_data.items():
            print(f"   {key}: {value}")


def main():
    try:
        inspect_story_analysis_summary()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
