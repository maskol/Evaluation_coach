#!/usr/bin/env python3
"""
Test script to verify insight export to Excel functionality
"""
import requests
import json

# Read the exported JSON insight
with open(
    "/Users/maskol/Downloads/insight-critical-bottleneck-in-in-uat-stage-2026-01-12.json",
    "r",
) as f:
    insight_data = json.load(f)

# Remove metadata before sending to API
if "metadata" in insight_data:
    del insight_data["metadata"]

# Test the export API
url = "http://localhost:8850/api/v1/insights/export"
params = {"pis": "26Q1", "analysis_level": "feature"}

print(f"🧪 Testing export API endpoint: {url}")
print(f"📋 Insight: {insight_data.get('title', 'Unknown')}")
print(f"🎯 Parameters: {params}")
print()

try:
    response = requests.post(url, params=params, json=insight_data, timeout=30)

    print(f"📡 Response Status: {response.status_code}")
    print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"📦 Content-Length: {len(response.content)} bytes")

    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        if "spreadsheet" in content_type or "excel" in content_type:
            # Save the Excel file
            filename = "/Users/maskol/Downloads/test_insight_export.xlsx"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"✅ Excel file saved: {filename}")
        else:
            print(f"⚠️  Unexpected content type. Response preview:")
            print(response.text[:500])
    else:
        print(f"❌ Error Response:")
        print(response.text)

except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
