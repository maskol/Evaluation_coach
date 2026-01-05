"""
Test insight generation API to see what's being returned
"""

import requests
import json

print("=" * 80)
print("🧪 Testing Insight Generation API")
print("=" * 80)

# Test insight generation endpoint with query parameters (matching frontend)
url = "http://localhost:8850/api/v1/insights/generate"
params = {
    "scope": "art",
    "arts": "SAART",
    "pis": "26Q1",
    "model": "gpt-4o-mini",
    "temperature": 0.3,
}

print(f"\nCalling: {url}")
print(f"Params: {params}")
print("-" * 80)

try:
    response = requests.post(url, params=params, timeout=60)
    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Response Summary:")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Count: {data.get('count', 0)}")

        insights = data.get("insights", [])
        print(f"   Insights: {len(insights)}")

        if len(insights) > 0:
            print(f"\n✅ Successfully generated {len(insights)} insights!")
            print("\nFirst insight:")
            print(f"   Title: {insights[0].get('title', 'N/A')}")
            print(f"   Severity: {insights[0].get('severity', 'N/A')}")
            print(f"   Confidence: {insights[0].get('confidence', 'N/A')}")
        else:
            print("\n⚠️  Empty insights list!")
            print("\nFull response:")
            print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error response ({response.status_code}):")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to backend")
    print(
        "   Make sure backend is running: cd backend && uvicorn main:app --reload --port 8850"
    )
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 80)
