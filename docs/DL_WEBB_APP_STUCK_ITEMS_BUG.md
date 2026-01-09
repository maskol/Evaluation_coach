# Bug Report: `/api/analysis/summary` stuck_items Filter Not Working

**Reporter:** Evaluation Coach Team  
**Date:** 8 January 2026  
**Priority:** High  
**Component:** Analysis Summary API

---

## Summary

The `stuck_items` array returned by the `/api/analysis/summary` endpoint only contains features from **ACEART**, regardless of which ARTs are specified in the filter parameters or if no filter is applied.

---

## Steps to Reproduce

### Test 1: Request specific ARTs
```bash
curl "http://localhost:8000/api/analysis/summary?art=ACEART&art=C4ART&art=SAART&pi=25Q4"
```

**Expected:** stuck_items from ACEART, C4ART, and SAART  
**Actual:** stuck_items only from ACEART (20 items)

### Test 2: No ART filter
```bash
curl "http://localhost:8000/api/analysis/summary?pi=25Q4"
```

**Expected:** stuck_items from ALL ARTs  
**Actual:** stuck_items only from ACEART

### Test 3: Verify data exists (flow_leadtime works correctly)
```bash
curl "http://localhost:8000/api/flow_leadtime?limit=100000"
```

**Result:** Returns 58,623 features across 28 ARTs ✅

| ART | Feature Count |
|-----|---------------|
| SAART | 12,825 |
| EEART | 9,156 |
| COART | 6,881 |
| UCART | 5,598 |
| ACEART | 4,231 |
| C4ART | 3,892 |
| ... | ... |

---

## Technical Details

### Python reproduction script
```python
import httpx

# Test with multiple ARTs
response = httpx.get(
    'http://localhost:8000/api/analysis/summary',
    params={'art': ['ACEART', 'C4ART', 'SAART'], 'pi': '25Q4'}
)
data = response.json()

stuck_items = data.get('bottleneck_analysis', {}).get('stuck_items', [])
arts_in_result = set(item.get('art') for item in stuck_items)

print(f"Total stuck items: {len(stuck_items)}")
print(f"ARTs in result: {arts_in_result}")
# Output: ARTs in result: {'ACEART'}  ← BUG!
```

### Request URL shows correct parameters
```
http://localhost:8000/api/analysis/summary?art=ACEART&art=C4ART&art=SAART&pi=25Q4
```
The repeated `art` parameters are correctly formatted.

---

## Impact

- **Excel exports** only include ACEART stuck items, missing data from other ARTs
- **Dashboard analytics** show incomplete bottleneck data
- **Users filtering by multiple ARTs** get misleading stuck item counts
- **Management reports** undercount total stuck features across organization

---

## Workaround Implemented

We implemented a client-side workaround in Evaluation Coach by:
1. Fetching raw data from `/api/flow_leadtime` (which returns all ARTs correctly)
2. Filtering by selected ARTs/PIs
3. Calculating stuck items locally based on `threshold_days`

```python
# Workaround: Calculate stuck items from flow_leadtime
flow_data = client.get_flow_leadtime(limit=50000)
flow_data = [f for f in flow_data if f.get("art") in selected_arts]

stuck_items = []
for feature in flow_data:
    if feature.get("status") == "DONE":
        continue
    # Check if stuck in any stage > threshold_days
    for stage in stage_columns:
        if feature.get(stage, 0) > threshold_days:
            stuck_items.append(feature)
            break
```

This works but is less efficient than having the server calculate it.

---

## Suggested Fix

The stuck_items calculation logic in `/api/analysis/summary` should:

1. **Respect the `art` filter parameter(s)** - Apply ART filter to stuck items query
2. **Include all matching ARTs** - When multiple ARTs requested, include stuck items from all of them
3. **Include ALL ARTs when no filter** - If no `art` parameter provided, return stuck items from entire dataset

### Likely cause
The stuck_items query may have a hardcoded filter or is not applying the `art` parameter correctly. Check the database query or data filtering logic.

---

## Environment

- **DL Webb App:** localhost:8000
- **Evaluation Coach:** localhost:8850
- **Date tested:** 8 January 2026
- **Data period:** PI 25Q4

---

## Acceptance Criteria

- [ ] `/api/analysis/summary?art=ACEART&art=C4ART` returns stuck_items from both ACEART and C4ART
- [ ] `/api/analysis/summary` (no filter) returns stuck_items from ALL ARTs
- [ ] stuck_items count is consistent with calculated count from flow_leadtime data
- [ ] Response time remains acceptable (< 5 seconds)
