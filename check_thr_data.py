#!/usr/bin/env python3
import sys
import json
import requests

response = requests.get(
    "http://localhost:8000/api/leadtime_thr_data?art=FTART&pi=26Q1&limit=10000"
)
data = response.json()

print(f"Total features: {len(data)}")

# Check for lead_time_days
features_with_lt = [f for f in data if f.get("lead_time_days", 0) > 0]
print(f"Features with lead_time_days > 0: {len(features_with_lt)}")

if features_with_lt:
    avg = sum(f["lead_time_days"] for f in features_with_lt) / len(features_with_lt)
    print(f"\nAverage Lead Time: {avg:.1f} days")
    print(f"Min: {min(f['lead_time_days'] for f in features_with_lt):.1f} days")
    print(f"Max: {max(f['lead_time_days'] for f in features_with_lt):.1f} days")

    print(f"\nAll lead times:")
    for f in features_with_lt:
        print(f"  {f['issue_key']}: {f['lead_time_days']:.1f} days")
