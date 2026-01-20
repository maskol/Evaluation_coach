# DL Webb APP Bug Report: C4ART-87 Missing from stuck_items

**Date**: 20 January 2026  
**Reporter**: Evaluation Coach Team  
**Priority**: HIGH  
**Component**: `/api/analysis/summary` - stuck_items calculation

---

## Summary

**C4ART-87 is missing from the `stuck_items` array** even though it has **255.9 days in `in_progress`** stage (well above the 60-day threshold) and `include_completed=true` is set.

This causes users analyzing historical PIs to see incorrect examples in their bottleneck insights - they see the maximum time is 256 days but can't see which item caused it.

---

## Evidence

### Raw Data (from `/api/flow_leadtime`)
```
Issue Key: C4ART-87
Status: Done
ART: C4ART
PI: 25Q2
in_progress: 255.858129305556 days  ⬅️ THIS SHOULD BE IN STUCK_ITEMS!
total_leadtime: 265.878735 days
```

### API Request
```
GET /api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART&threshold_days=60&include_completed=true
```

### Expected Result
C4ART-87 should appear in `stuck_items` array:
```json
{
  "issue_key": "C4ART-87",
  "stage": "in_progress",
  "days_in_stage": 255.858,
  "art": "C4ART",
  "team": "GSOC Engineering",
  "status": "Done"
}
```

### Actual Result
C4ART-87 is **NOT in the stuck_items array**. Top 5 stuck items are:
```
1. C4ART-40: 157.1 days in in_planned (Done)
2. C4ART-129: 126.8 days in in_progress (Done)
3. C4ART-129: 125.8 days in in_planned (Done)
4. C4ART-10: 110.2 days in in_analysis (Done)
5. C4ART-19: 104.1 days in in_analysis (Done)
```

**Max in list**: 157.1 days (C4ART-40)  
**Missing**: 255.9 days (C4ART-87) ❌

---

## Impact

### For Users
- ❌ Insights show "max: 256 days" but can't see the actual 256-day item
- ❌ Can't investigate C4ART-87 to understand what caused the delay
- ❌ Historical analysis is incomplete and misleading
- ❌ Root cause analysis is impossible without the actual worst-case example

### Example Insight (Current - Incorrect)
```
Critical Bottleneck in In Progress Stage
...
🔍 Root Causes:
Severe flow blockage with items stuck in stage
C4ART-129: 126.8 days in in_progress
C4ART-26: 24.1 days in in_progress
Note: Historical maximum was 256 days. Currently stuck items shown above 
are still active; historical max may be from a completed/cancelled item.
```

**User Question**: "Show me the 256-day item!" ⬅️ Can't do it - it's missing!

### Example Insight (Expected - Correct)
```
Critical Bottleneck in In Progress Stage
...
🔍 Root Causes:
Severe flow blockage with items stuck in stage
C4ART-87: 255.9 days in in_progress (Done)  ⬅️ NOW VISIBLE!
C4ART-129: 126.8 days in in_progress (Done)
C4ART-26: 24.1 days in in_progress (Done)
```

---

## Root Cause Hypothesis

The stuck_items calculation logic in DL Webb APP is likely:

1. **Not properly reading stage times from database**
   - Perhaps it's looking at a summary table instead of the detail `flow_leadtime` table
   - Or it's only considering current_stage/days_in_current_stage

2. **Not properly applying include_completed filter**
   - It IS returning completed items (good!)
   - But it's missing C4ART-87 specifically

3. **Data transformation issue**
   - The `flow_leadtime` endpoint correctly has C4ART-87 with 255.9 days
   - But the `analysis/summary` endpoint's stuck_items doesn't include it
   - Likely a bug in the analysis engine logic

---

## Steps to Reproduce

1. Query raw data:
   ```bash
   curl "http://localhost:8000/api/flow_leadtime?limit=100000" | grep -A 10 "C4ART-87"
   ```
   Result: Shows C4ART-87 with `in_progress: 255.858` days ✅

2. Query stuck_items:
   ```bash
   curl "http://localhost:8000/api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART&threshold_days=60&include_completed=true"
   ```
   Result: C4ART-87 NOT in stuck_items array ❌

3. Run verification script:
   ```bash
   python verify_c4art87_bug.py
   ```

---

## Suggested Fix

Check the stuck_items calculation logic in DL Webb APP backend:

**File**: Likely in `backend/analysis_engine.py` or `backend/main_sqlmodel.py`

**Look for**:
- How stuck_items are calculated from `flow_leadtime` records
- Whether it's using the correct stage time fields (`in_progress`, `in_analysis`, etc.)
- Whether there's a limit on stuck_items that's excluding C4ART-87
- Whether completed items are properly included when `include_completed=true`

**Expected Logic**:
```python
for record in flow_leadtime_records:
    # Check EACH stage time field
    for stage in ['in_progress', 'in_analysis', 'in_planned', ...]:
        stage_time = getattr(record, stage)
        if stage_time > threshold_days:
            # Include if include_completed or not completed
            if include_completed or record.status not in COMPLETED_STATUSES:
                stuck_items.append({
                    'issue_key': record.issue_key,
                    'stage': stage,
                    'days_in_stage': stage_time,
                    'status': record.status,
                    # ... other fields
                })
```

---

## Acceptance Criteria

- [ ] C4ART-87 appears in stuck_items with `stage: 'in_progress'` and `days_in_stage: 255.9`
- [ ] All items with any stage > threshold_days appear in stuck_items
- [ ] Completed items are included when `include_completed=true`
- [ ] stuck_items are sorted by `days_in_stage` descending
- [ ] Response time remains acceptable (< 5 seconds)

---

## Testing

After fix, verify with:

```bash
# Test 1: Check C4ART-87 is in stuck_items
curl "http://localhost:8000/api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART&threshold_days=60&include_completed=true" \
  | jq '.bottleneck_analysis.stuck_items[] | select(.issue_key == "C4ART-87")'

# Expected: Should return C4ART-87 with in_progress: 255.9 days

# Test 2: Verify sorting
curl "http://localhost:8000/api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART&threshold_days=60&include_completed=true" \
  | jq '.bottleneck_analysis.stuck_items[0]'

# Expected: Should be C4ART-87 (highest days_in_stage)
```

---

## Related

- **Include Completed Items Feature**: HISTORICAL_ANALYSIS_INCLUDE_COMPLETED.md
- **Implementation Guide**: DL_WEBB_APP_INCLUDE_COMPLETED_IMPLEMENTATION.md
- **Verification Script**: verify_c4art87_bug.py

---

## Status

🔴 **OPEN** - Awaiting DL Webb APP fix

Once fixed, users will be able to see C4ART-87 as the example in their bottleneck insights for historical analysis! 🎉
