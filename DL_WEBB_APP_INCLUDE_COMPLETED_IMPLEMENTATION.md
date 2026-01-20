# Include Completed Items Feature - DL Webb APP Implementation Guide

## 📋 Overview

This guide provides step-by-step instructions for implementing the "Include Completed Items" feature in the **DL Webb APP** backend. This feature is already implemented in the Evaluation Coach backend and is now waiting for DL Webb APP support.

**Status**: 
- ✅ Evaluation Coach: **Fully Implemented** (backend/main.py, leadtime_client.py)
- ⏳ DL Webb APP: **Requires Implementation** (this guide)

**Date**: 20 January 2026

---

## 🎯 Feature Purpose

### Problem
When analyzing **historical PIs** (e.g., 25Q1-25Q4 analyzed in 2026), users expect to see **all items** that were stuck during those periods, including items that have since been completed. However, the DL Webb API currently excludes completed items from `stuck_items`, showing only currently active stuck items.

This creates a data mismatch:
- **Statistics show**: "max: 256 days" (calculated from ALL data including completed items)
- **Stuck items list shows**: Only 3 active items with max ~127 days
- **User expectation**: "Show me the 256-day item that caused that maximum!"

### Solution
Add an **`include_completed`** query parameter to the `/api/analysis/summary` endpoint that:
- **When `true`**: Include all stuck items (including DONE/CLOSED) for historical analysis
- **When `false` (default)**: Exclude completed items for current/active analysis
- **Automatic**: The Evaluation Coach automatically sets this parameter based on PI dates

---

## 🏗️ Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Selects Historical PIs in Evaluation Coach UI              │
│ Example: 25Q1, 25Q2, 25Q3, 25Q4 (all in the past)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Evaluation Coach Backend (main.py)                              │
│                                                                  │
│ 1. Query PI configurations from database                        │
│ 2. Check if any selected PI includes today's date               │
│ 3. If all PIs are in the past → is_historical = True           │
│ 4. Add parameter: include_completed = True                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LeadTime Client (leadtime_client.py)                            │
│                                                                  │
│ Pass include_completed parameter to DL Webb API:                │
│ GET /api/analysis/summary?pi=25Q1&art=C4ART&include_completed=true
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ DL Webb API (backend) ⬅️ YOU ARE HERE                          │
│                                                                  │
│ Query database:                                                  │
│ - If include_completed = true: Include all items in stuck_items │
│ - If include_completed = false: Filter out DONE/CLOSED items    │
│                                                                  │
│ Return stuck_items with historical context                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 💻 Implementation Steps

### Step 1: Locate the Analysis Summary Endpoint

Find the endpoint that handles `/api/analysis/summary` in your DL Webb APP codebase. This is typically in:
- `backend/routes/analysis.py`
- `backend/main_sqlmodel.py`
- `backend/api/analysis.py`
- Or similar routing file

### Step 2: Add the `include_completed` Parameter

Update the endpoint signature to accept the new parameter:

```python
from typing import Optional, List
from fastapi import Query

@app.get("/api/analysis/summary")
async def get_analysis_summary(
    pi: Optional[List[str]] = Query(None),
    art: Optional[List[str]] = Query(None),
    development_team: Optional[str] = Query(None),
    threshold_days: Optional[float] = Query(None),
    include_completed: bool = Query(False),  # ⬅️ NEW PARAMETER
):
    """
    Get comprehensive analysis summary.
    
    Args:
        pi: List of Program Increments to analyze
        art: List of ARTs to analyze
        development_team: Team name to filter by
        threshold_days: Threshold for identifying stuck items
        include_completed: Include completed/done items in stuck_items 
                          (for historical analysis)
    """
    # Implementation below...
```

### Step 3: Define Completed Statuses

Add a constant for completed statuses (adjust based on your status values):

```python
# At the top of your file or in a constants module
COMPLETED_STATUSES = {
    "DONE",
    "CLOSED",
    "RESOLVED",
    "CANCELLED",
    "CANCELED",
    "DEPLOYED",  # If your system uses this
    "COMPLETED",  # If your system uses this
}
```

### Step 4: Build the Database Query

Build your query as usual, applying PI, ART, and team filters:

```python
# Build base query
query = db.query(FeatureFlowLeadtime)

# Apply filters
if pi:
    query = query.filter(FeatureFlowLeadtime.pi.in_(pi))
if art:
    query = query.filter(FeatureFlowLeadtime.art.in_(art))
if development_team:
    query = query.filter(FeatureFlowLeadtime.development_team == development_team)

# Get all data
all_items = query.all()
```

### Step 5: Calculate Statistics (Include ALL Items)

Calculate statistics from **ALL items** (including completed), regardless of the `include_completed` parameter:

```python
# Calculate statistics from ALL items (including completed)
# This ensures statistics like max_days reflect the true maximum
stage_times = {}
for item in all_items:
    stage = item.current_stage
    if stage not in stage_times:
        stage_times[stage] = []
    stage_times[stage].append(item.days_in_stage)

# Calculate stage statistics
stage_analysis = {}
for stage, times in stage_times.items():
    stage_analysis[stage] = {
        "mean_time": sum(times) / len(times),
        "max_time": max(times),  # ⬅️ This includes completed items
        "min_time": min(times),
        "median_time": sorted(times)[len(times) // 2],
        "items_exceeding_threshold": len([t for t in times if t > threshold_days]),
        # ... other stats ...
    }
```

### Step 6: Build Stuck Items List (Respect `include_completed`)

Build the `stuck_items` array, filtering based on the `include_completed` parameter:

```python
# Determine threshold
if threshold_days is None:
    threshold_days = 60  # Default threshold

# Build stuck_items list
stuck_items = []

for item in all_items:
    # Only include items exceeding threshold
    if item.days_in_stage > threshold_days:
        # Check if we should filter out completed items
        if not include_completed:
            # Current/active analysis - exclude completed items
            if item.status.upper() in COMPLETED_STATUSES:
                continue  # Skip this item
        
        # Item passes filters - include it
        stuck_items.append({
            "feature_key": item.feature_key,
            "art": item.art,
            "current_stage": item.current_stage,
            "days_in_stage": item.days_in_stage,
            "status": item.status,
            "priority": item.priority,
            "development_team": item.development_team,
            # ... other fields ...
        })

# Sort by days_in_stage descending
stuck_items.sort(key=lambda x: x["days_in_stage"], reverse=True)
```

### Step 7: Build and Return Response

Return the complete response structure:

```python
return {
    "bottleneck_analysis": {
        "stage_analysis": stage_analysis,
        "stuck_items": stuck_items,  # ⬅️ Now includes completed items for historical analysis
        "wip_statistics": {
            # ... WIP stats ...
        }
    },
    "leadtime_statistics": {
        # ... lead time stats ...
    },
    "waste_analysis": {
        # ... waste stats ...
    },
    "throughput": {
        # ... throughput stats ...
    }
}
```

---

## 📝 Complete Example Implementation

Here's a complete example showing the key parts:

```python
from typing import Optional, List
from fastapi import Query, APIRouter

router = APIRouter()

# Completed status definitions
COMPLETED_STATUSES = {
    "DONE",
    "CLOSED",
    "RESOLVED",
    "CANCELLED",
    "CANCELED",
}

@router.get("/api/analysis/summary")
async def get_analysis_summary(
    pi: Optional[List[str]] = Query(None),
    art: Optional[List[str]] = Query(None),
    development_team: Optional[str] = Query(None),
    threshold_days: Optional[float] = Query(60),
    include_completed: bool = Query(False),  # NEW PARAMETER
):
    """
    Get comprehensive analysis summary.
    
    For historical PI analysis, set include_completed=true to include
    completed/done items in the stuck_items array.
    """
    
    # Build query with filters
    query = db.query(FeatureFlowLeadtime)
    
    if pi:
        query = query.filter(FeatureFlowLeadtime.pi.in_(pi))
    if art:
        query = query.filter(FeatureFlowLeadtime.art.in_(art))
    if development_team:
        query = query.filter(FeatureFlowLeadtime.development_team == development_team)
    
    all_items = query.all()
    
    # Calculate statistics from ALL items (including completed)
    max_days = max(item.days_in_stage for item in all_items) if all_items else 0
    
    # Build stuck_items with optional filtering
    stuck_items = []
    for item in all_items:
        if item.days_in_stage > threshold_days:
            # Apply completed item filter if needed
            if not include_completed and item.status.upper() in COMPLETED_STATUSES:
                continue  # Skip completed items for current analysis
            
            stuck_items.append({
                "feature_key": item.feature_key,
                "art": item.art,
                "current_stage": item.current_stage,
                "days_in_stage": item.days_in_stage,
                "status": item.status,
            })
    
    # Sort by days descending
    stuck_items.sort(key=lambda x: x["days_in_stage"], reverse=True)
    
    return {
        "bottleneck_analysis": {
            "stage_analysis": {
                "in_progress": {
                    "max_time": max_days,  # 256 days (from ALL items)
                    # ... other stats ...
                }
            },
            "stuck_items": stuck_items  # Now includes 256-day item for historical
        }
    }
```

---

## 🧪 Testing

### Test Case 1: Current PI (Default Behavior)
```bash
# Test without parameter (should exclude completed items)
curl "http://localhost:8000/api/analysis/summary?pi=26Q1&art=C4ART"

# Expected: Only active/in-progress stuck items
# Completed items should NOT appear in stuck_items
```

### Test Case 2: Historical PI with Parameter
```bash
# Test with include_completed=true
curl "http://localhost:8000/api/analysis/summary?pi=25Q1&art=C4ART&include_completed=true"

# Expected: ALL stuck items including completed ones
# Should see items with status DONE, CLOSED, etc.
```

### Test Case 3: Verify Statistics Match
```bash
# Query the data
curl "http://localhost:8000/api/analysis/summary?pi=25Q1&art=C4ART&include_completed=true" | jq

# Check:
# 1. max_time in stage_analysis (e.g., 256 days)
# 2. stuck_items array should contain item with 256 days
# 3. Both should reference the same maximum value
```

### Test Case 4: Explicit False
```bash
# Test with include_completed=false (explicit)
curl "http://localhost:8000/api/analysis/summary?pi=25Q1&art=C4ART&include_completed=false"

# Expected: Same as omitting parameter - only active items
```

---

## ✅ Validation Checklist

Before considering this feature complete, verify:

- [ ] Endpoint accepts `include_completed` parameter (boolean, defaults to `false`)
- [ ] When `include_completed=false` (or omitted):
  - [ ] Stuck items exclude DONE/CLOSED/RESOLVED/CANCELLED statuses
  - [ ] Only active/in-progress items appear in stuck_items
- [ ] When `include_completed=true`:
  - [ ] Stuck items include ALL items exceeding threshold
  - [ ] Completed items (DONE/CLOSED etc.) appear in stuck_items
- [ ] Statistics (max_time, mean_time, etc.) calculated from ALL items regardless of parameter
- [ ] Response structure unchanged (backward compatible)
- [ ] API documentation updated with new parameter
- [ ] Tested with real data for both current and historical PIs

---

## 📊 Usage Examples

### Example 1: Current Analysis (Exclude Completed)
**Scenario**: Analyzing current PI 26Q1 (today is 2026-01-20, within PI range)

**Request**:
```bash
GET /api/analysis/summary?pi=26Q1&art=C4ART
```

**Parameter**: `include_completed` not provided (defaults to `false`)

**Result**:
```json
{
  "bottleneck_analysis": {
    "stage_analysis": {
      "in_progress": {
        "max_time": 256.0
      }
    },
    "stuck_items": [
      {"feature_key": "C4ART-129", "days_in_stage": 126.8, "status": "In Progress"},
      {"feature_key": "C4ART-26", "days_in_stage": 24.1, "status": "In Progress"}
      // C4ART-XX with 256 days (status: DONE) is EXCLUDED ✅
    ]
  }
}
```

**Notes**:
- Max time shows 256 days (calculated from all data)
- But stuck_items only shows active items
- This is correct for current/active analysis

### Example 2: Historical Analysis (Include Completed)
**Scenario**: Analyzing past PIs 25Q1-25Q4 (today is 2026-01-20, all PIs are historical)

**Request**:
```bash
GET /api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART&include_completed=true
```

**Parameter**: `include_completed=true` (set by Evaluation Coach automatically)

**Result**:
```json
{
  "bottleneck_analysis": {
    "stage_analysis": {
      "in_progress": {
        "max_time": 256.0
      }
    },
    "stuck_items": [
      {"feature_key": "C4ART-XX", "days_in_stage": 256.0, "status": "DONE"},
      {"feature_key": "C4ART-129", "days_in_stage": 126.8, "status": "DONE"},
      {"feature_key": "C4ART-26", "days_in_stage": 24.1, "status": "DONE"}
      // ALL items including completed ones are INCLUDED ✅
    ]
  }
}
```

**Notes**:
- Max time shows 256 days
- stuck_items includes the 256-day item (even though it's DONE)
- This provides complete historical context

---

## 🔄 Integration with Evaluation Coach

The Evaluation Coach backend automatically determines when to use this parameter:

```python
# From backend/main.py (already implemented)

# Check if analysis is historical
today = datetime.now().date()
is_current = False

for selected_pi in selected_pis:
    pi_config = get_pi_config(selected_pi)
    start_date = parse_date(pi_config["start_date"])
    end_date = parse_date(pi_config["end_date"])
    
    if start_date <= today <= end_date:
        is_current = True
        break

# Set parameter based on analysis type
if not is_current:
    params["include_completed"] = True
    print("📅 Historical analysis - requesting completed items")
else:
    print("📅 Current analysis - excluding completed items")
```

**No UI changes needed** - this works automatically based on which PIs the user selects!

---

## 🎯 Benefits

### For Users
1. **Historical Accuracy**: See complete picture of what happened in past PIs
2. **Consistent Data**: Statistics and stuck_items list now match
3. **Better Root Cause Analysis**: Can investigate the actual worst-case items
4. **No Manual Configuration**: Works automatically based on PI dates

### For Developers
1. **Backward Compatible**: Defaults to current behavior (exclude completed)
2. **Simple Implementation**: One boolean parameter, clear filtering logic
3. **No Schema Changes**: Uses existing data, no database migrations
4. **Clear Separation**: Current vs historical analysis handled cleanly

---

## 📚 Related Documentation

- [HISTORICAL_ANALYSIS_INCLUDE_COMPLETED.md](docs/HISTORICAL_ANALYSIS_INCLUDE_COMPLETED.md) - Full feature specification
- Evaluation Coach implementation:
  - [backend/main.py](backend/main.py) - Lines 1160-1203 (PI date detection)
  - [backend/integrations/leadtime_client.py](backend/integrations/leadtime_client.py) - Lines 390-416 (API client)

---

## 📞 Support

If you have questions about implementing this feature:

1. Review the [HISTORICAL_ANALYSIS_INCLUDE_COMPLETED.md](docs/HISTORICAL_ANALYSIS_INCLUDE_COMPLETED.md) documentation
2. Check the Evaluation Coach implementation in `backend/main.py` and `backend/integrations/leadtime_client.py`
3. Test with the provided curl commands
4. Verify data matches expected behavior for both current and historical PIs

---

## 🏁 Summary

This feature enables accurate historical analysis by allowing the API to return completed items in the stuck_items array when requested. The implementation is:

- **Simple**: One boolean parameter
- **Backward compatible**: Defaults to current behavior
- **Automatic**: Evaluation Coach sets it based on PI dates
- **Clear**: Separates current from historical analysis

**Next Steps**:
1. Locate your `/api/analysis/summary` endpoint in DL Webb APP
2. Add the `include_completed` parameter (Step 2)
3. Implement filtering logic (Steps 5-6)
4. Test with provided curl commands (Testing section)
5. Deploy to production

**Status**: Ready for implementation in DL Webb APP backend! 🚀
