#!/usr/bin/env python3
"""
Test Little's Law Analysis with RAG Enhancement

This script tests the complete Little's Law workflow:
1. Fetches flow data and planning data
2. Runs Little's Law analyzer with RAG enhancement
3. Displays the generated insights
4. Validates quality against benchmark criteria
"""

import requests
import json
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8850"


def test_littles_law_analysis():
    """Test Little's Law analysis generation."""

    print("=" * 80)
    print("🔬 TESTING LITTLE'S LAW ANALYSIS WITH RAG ENHANCEMENT")
    print("=" * 80)
    print()

    # Use a known PI from the system
    pi = "24Q4"  # Common test PI

    print(f"📊 Testing with PI: {pi}")
    print()

    # Step 1: Generate Little's Law insights
    print("🚀 Step 1: Generating Little's Law insights with RAG...")

    request_payload = {
        "scope_type": "pi",
        "scope_id": pi,
        "use_agent_graph": True,
        "enhance_with_llm": True,
        "model": "gpt-4o-mini",  # Use mini for faster testing
        "temperature": 0.7,
    }

    print(f"   RAG Enhancement: ENABLED")
    print(f"   Model: gpt-4o-mini")
    print()

    try:
        # Send as query parameters (endpoint uses form params, not JSON body)
        params = {
            "scope": "pi",
            "pis": pi,
            "enhance_with_llm": "true",
            "use_agent_graph": "true",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/insights/generate", params=params
        )
        response.raise_for_status()
        result = response.json()

        print(f"✅ Request successful!")
        print()

    except Exception as e:
        print(f"❌ Failed to generate insights: {e}")
        if hasattr(e, "response") and e.response:
            print(f"   Response: {e.response.text}")
        return False

    # Step 2: Extract Little's Law insights
    print("🔍 Step 2: Analyzing Little's Law insights...")

    insights = result.get("insights", [])
    littles_law_insights = [
        i
        for i in insights
        if "little" in i.get("category", "").lower()
        or "flow" in i.get("title", "").lower()
        and "little" in str(i).lower()
    ]

    print(f"   Total insights: {len(insights)}")
    print(f"   Little's Law insights: {len(littles_law_insights)}")
    print()

    if not littles_law_insights:
        print("⚠️  No Little's Law insights found in response")
        print("   This may indicate the analyzer didn't run or scope was incorrect")
        print()
        print("📋 All insight categories:")
        for insight in insights[:5]:
            print(
                f"   - {insight.get('category', 'unknown')}: {insight.get('title', 'no title')}"
            )
        return False

    # Step 3: Validate quality
    print("✅ Step 3: Validating insight quality...")
    print()

    quality_score = 0
    max_score = 0

    for idx, insight in enumerate(littles_law_insights, 1):
        print(f"📊 Insight {idx}: {insight.get('title', 'Untitled')}")
        print(f"   Category: {insight.get('category', 'unknown')}")
        print(f"   Severity: {insight.get('severity', 'unknown')}")
        print()

        # Get the interpretation (where RAG enhancement appears)
        interpretation = insight.get("interpretation", "")

        # Quality checks
        checks = {
            "Has RAG enhancement (Expert Analysis section)": "**Expert Analysis:**"
            in interpretation,
            "Length > 500 chars (detailed)": len(interpretation) > 500,
            "Mentions Little's Law formula": any(
                x in interpretation.lower() for x in ["l = λ", "wip =", "throughput ×"]
            ),
            "Contains specific numbers": any(char.isdigit() for char in interpretation),
            "Has scenario modeling": any(
                x in interpretation.lower() for x in ["scenario", "what if", "impact"]
            ),
            "Mentions stage/WIP limits": any(
                x in interpretation.lower() for x in ["stage", "wip limit", "≤"]
            ),
        }

        print("   Quality Checks:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
            max_score += 1
            if passed:
                quality_score += 1

        print()
        print("   📝 Interpretation Preview (first 500 chars):")
        print("   " + "-" * 70)
        preview = interpretation[:500].replace("\n", "\n   ")
        print(f"   {preview}...")
        print("   " + "-" * 70)
        print()

    # Step 4: Final scoring
    print("=" * 80)
    print("📊 QUALITY ASSESSMENT")
    print("=" * 80)

    percentage = (quality_score / max_score * 100) if max_score > 0 else 0

    print(f"Quality Score: {quality_score}/{max_score} ({percentage:.1f}%)")
    print()

    if percentage >= 80:
        print("🎉 EXCELLENT - Analysis meets benchmark quality!")
    elif percentage >= 60:
        print("✅ GOOD - Analysis is solid, minor improvements possible")
    elif percentage >= 40:
        print("⚠️  FAIR - Analysis needs improvement")
    else:
        print("❌ POOR - Analysis quality below expectations")

    print()
    print("=" * 80)

    return percentage >= 60


def main():
    """Main test execution."""
    try:
        success = test_littles_law_analysis()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
