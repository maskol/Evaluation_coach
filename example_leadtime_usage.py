#!/usr/bin/env python3
"""
Example script demonstrating how to use the Lead-Time integration.

This shows how to access lead-time data from the external DL Webb App server
through the Evaluation Coach API.
"""

import requests
from typing import Optional


class EvaluationCoachClient:
    """Simple client for Evaluation Coach API"""

    def __init__(self, base_url: str = "http://localhost:8850"):
        self.base_url = base_url.rstrip("/")

    def check_leadtime_status(self):
        """Check if lead-time server is available"""
        response = requests.get(f"{self.base_url}/api/leadtime/status")
        return response.json()

    def get_filters(self):
        """Get available filter options"""
        response = requests.get(f"{self.base_url}/api/leadtime/filters")
        return response.json()

    def get_features_leadtime(
        self, art: Optional[str] = None, pi: Optional[str] = None
    ):
        """Get feature lead-time data"""
        params = {}
        if art:
            params["art"] = art
        if pi:
            params["pi"] = pi

        response = requests.get(f"{self.base_url}/api/leadtime/features", params=params)
        return response.json()

    def get_statistics(self, arts: Optional[list] = None, pis: Optional[list] = None):
        """Get lead-time statistics"""
        params = {}
        if arts:
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)

        response = requests.get(
            f"{self.base_url}/api/leadtime/statistics", params=params
        )
        return response.json()

    def get_bottlenecks(self, arts: Optional[list] = None):
        """Get bottleneck analysis"""
        params = {}
        if arts:
            params["arts"] = ",".join(arts)

        response = requests.get(
            f"{self.base_url}/api/leadtime/bottlenecks", params=params
        )
        return response.json()

    def get_coaching_summary(self, art: Optional[str] = None, pi: Optional[str] = None):
        """Get comprehensive coaching summary"""
        params = {}
        if art:
            params["art"] = art
        if pi:
            params["pi"] = pi

        response = requests.get(f"{self.base_url}/api/leadtime/summary", params=params)
        return response.json()


def main():
    """Example usage"""
    client = EvaluationCoachClient()

    print("=" * 80)
    print("Lead-Time Integration Example")
    print("=" * 80)
    print()

    # 1. Check server status
    print("1. Checking lead-time server status...")
    status = client.check_leadtime_status()
    print(f"   Status: {status}")
    print()

    if not status.get("available"):
        print("❌ Lead-time server is not available. Exiting.")
        return

    # 2. Get available filters
    print("2. Getting available filters...")
    filters = client.get_filters()
    print(f"   Available ARTs: {filters.get('arts', [])[:5]}")
    print(f"   Available PIs: {filters.get('pis', [])[:5]}")
    print(f"   Available Teams: {filters.get('teams', [])[:5]}")
    print()

    # 3. Get feature lead-time for a specific ART
    if filters.get("arts"):
        art = filters["arts"][0]
        print(f"3. Getting feature lead-time for ART: {art}...")
        features = client.get_features_leadtime(art=art)
        print(f"   Found {features.get('count', 0)} features")
        if features.get("features"):
            first_feature = features["features"][0]
            print(
                f"   Example: {first_feature.get('issue_key')} - {first_feature.get('summary')}"
            )
            print(
                f"   Total lead-time: {first_feature.get('total_leadtime', 0):.2f} days"
            )
        print()

    # 4. Get statistics
    print("4. Getting lead-time statistics...")
    stats = client.get_statistics()
    if stats.get("stage_statistics"):
        print("   Stage statistics:")
        for stage, data in list(stats["stage_statistics"].items())[:3]:
            print(f"     {stage}:")
            print(f"       Mean: {data.get('mean', 0):.2f} days")
            print(f"       Median: {data.get('median', 0):.2f} days")
            print(f"       P95: {data.get('p95', 0):.2f} days")
    print()

    # 5. Get bottleneck analysis
    print("5. Getting bottleneck analysis...")
    bottlenecks = client.get_bottlenecks()
    print(f"   Bottlenecks: {bottlenecks}")
    print()

    # 6. Get comprehensive coaching summary
    if filters.get("arts"):
        art = filters["arts"][0]
        print(f"6. Getting coaching summary for ART: {art}...")
        summary = client.get_coaching_summary(art=art)
        print(f"   Available: {summary.get('available')}")
        if summary.get("available"):
            print(f"   Data source: {summary.get('data_source')}")
            if summary.get("leadtime_statistics"):
                stats_count = len(
                    summary["leadtime_statistics"].get("stage_statistics", {})
                )
                print(f"   Stages analyzed: {stats_count}")
        print()

    print("=" * 80)
    print("✅ Example completed!")
    print()
    print("You can now:")
    print("  - View API docs: http://localhost:8850/docs")
    print("  - Use these endpoints in your frontend")
    print("  - Integrate with LLM agents for coaching insights")
    print("=" * 80)


if __name__ == "__main__":
    main()
