# Historical Analysis: Include Completed Items Feature

## Overview

The `include_completed` parameter enables accurate historical analysis by including completed/done items in bottleneck stuck_items data when analyzing past Program Increments (PIs).

## Problem Statement

### The Issue

When analyzing historical PIs (e.g., 25Q1-25Q4 in early 2026), users expect to see **all items** that were stuck during those periods, including ones that have since been completed. However, by default, the DL Webb API excludes completed items from the `stuck_items` array, showing only currently active stuck items.

This creates a discrepancy:
- **Statistics show**: "max: 256 days" (calculated from all data including completed items)
- **Stuck items list shows**: Only 3 active items with max ~127 days
- **User expectation**: "Show me the 256-day item that created that maximum!"

### Why This Matters

**For Current/Active PI Analysis:**
- Users want to see items that are **currently stuck** and need immediate attention
- Completed items are not actionable and add noise
- ✅ Exclude completed items

**For Historical PI Analysis:**
- Users want to understand what **actually happened** in the past
- Completed items are crucial historical data points
- Maximum stuck time of 256 days is meaningless if you can't see which item it was
- Historical insights require complete data for accuracy
- ✅ Include completed items

## Solution Architecture

### Automatic Detection

The Evaluation Coach backend automatically detects whether analysis is historical or current:

```python
# Check if selected PI dates include today's date
today = datetime.now().date()
pi_config = {"pi": "26Q1", "start_date": "2025-12-28", "end_date": "2026-03-27"}

start_date = datetime.strptime(pi_config["start_date"], "%Y-%m-%d").date()
end_date = datetime.strptime(pi_config["end_date"], "%Y-%m-%d").date()

if start_date <= today <= end_date:
    is_current = True  # Don't include completed
else:
    is_historical = True  # Include completed
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ User Selects PIs: 25Q1, 25Q2, 25Q3, 25Q4                       │
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
│ DL Webb API (backend)                                            │
│                                                                  │
│ Query database:                                                  │
│ - If include_completed = true: Include all items in stuck_items │
│ - If include_completed = false: Filter out DONE/CLOSED items    │
│                                                                  │
│ Return stuck_items with historical context                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Insight Generation                                               │
│                                                                  │
│ Display: "max: 256 days" with corresponding item C4ART-XX       │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Evaluation Coach Backend Changes

**File: `backend/main.py`**

Added automatic PI date detection and parameter passing:

```python
# Determine if this is historical analysis (for DL Webb API)
if selected_pis:
    today = datetime.now().date()
    config_entry = db.query(RuntimeConfiguration).filter(
        RuntimeConfiguration.config_key == "pi_configurations"
    ).first()
    
    if config_entry and config_entry.config_value:
        pi_configurations = json.loads(config_entry.config_value)
        
        is_current = False
        for selected_pi in selected_pis:
            for pi_config in pi_configurations:
                if pi_config.get("pi") == selected_pi:
                    start_date = datetime.strptime(pi_config["start_date"], "%Y-%m-%d").date()
                    end_date = datetime.strptime(pi_config["end_date"], "%Y-%m-%d").date()
                    
                    if start_date <= today <= end_date:
                        is_current = True
                        break
        
        # For historical analysis, tell DL Webb API to include completed items
        if not is_current:
            params["include_completed"] = True
            print("📅 Historical analysis detected - requesting completed items")
```

**File: `backend/integrations/leadtime_client.py`**

Added parameter to API client methods:

```python
def get_analysis_summary(
    self,
    arts: Optional[List[str]] = None,
    pis: Optional[List[str]] = None,
    team: Optional[str] = None,
    threshold_days: Optional[float] = None,
    include_completed: Optional[bool] = None,  # NEW
) -> Dict[str, Any]:
    """
    Args:
        include_completed: Include completed/done items in stuck_items 
                          (for historical analysis)
    """
    params = {}
    # ... other params ...
    if include_completed is not None:
        params["include_completed"] = "true" if include_completed else "false"
    
    return self._get("/api/analysis/summary", params=params)
```

### DL Webb API Backend Changes (Required)

**File: `backend/routes/analysis.py` (or equivalent)**

The DL Webb API needs to support the `include_completed` parameter:

```python
@app.get("/api/analysis/summary")
async def get_analysis_summary(
    pi: Optional[List[str]] = Query(None),
    art: Optional[List[str]] = Query(None),
    include_completed: bool = Query(False),  # NEW parameter
):
    # Build query
    query = db.query(FeatureFlowLeadtime)
    
    # Apply filters
    if pi:
        query = query.filter(FeatureFlowLeadtime.pi.in_(pi))
    if art:
        query = query.filter(FeatureFlowLeadtime.art.in_(art))
    
    # Get all data for statistics
    all_items = query.all()
    
    # Calculate statistics from ALL items (including completed)
    max_days = max(item.days_in_stage for item in all_items)  # e.g., 256
    
    # Build stuck_items array
    if include_completed:
        # Historical analysis - include all items
        stuck_items = [
            format_stuck_item(item) 
            for item in all_items 
            if item.days_in_stage > threshold
        ]
    else:
        # Current analysis - exclude completed items
        stuck_items = [
            format_stuck_item(item)
            for item in all_items
            if item.days_in_stage > threshold
            and item.status not in ['DONE', 'CLOSED', 'RESOLVED', 'CANCELLED']
        ]
    
    return {
        "bottleneck_analysis": {
            "stage_analysis": {
                "in_progress": {
                    "max_time": max_days,  # 256 days
                    # ... other stats ...
                }
            },
            "stuck_items": stuck_items  # Now includes 256-day item for historical
        }
    }
```

## Usage Examples

### Example 1: Current PI Analysis (26Q1)

**PI Configuration:**
```json
{
  "pi": "26Q1",
  "start_date": "2025-12-28",
  "end_date": "2026-03-27"
}
```

**Today's Date:** 2026-01-20 (within PI range)

**Request:**
```
GET /api/analysis/summary?pi=26Q1&art=C4ART
```

**Result:** `include_completed` is NOT added (defaults to false)

**Stuck Items Returned:**
- C4ART-129: 126.8 days (Status: In Progress) ✅
- C4ART-26: 24.1 days (Status: In Progress) ✅
- C4ART-XX: 256 days (Status: Done) ❌ Excluded

### Example 2: Historical PI Analysis (25Q1-25Q4)

**PI Configuration:**
```json
[
  {"pi": "25Q1", "start_date": "2024-12-16", "end_date": "2025-03-16"},
  {"pi": "25Q2", "start_date": "2025-03-17", "end_date": "2025-06-15"},
  {"pi": "25Q3", "start_date": "2025-06-16", "end_date": "2025-09-14"},
  {"pi": "25Q4", "start_date": "2025-09-15", "end_date": "2025-12-14"}
]
```

**Today's Date:** 2026-01-20 (all PIs are in the past)

**Request:**
```
GET /api/analysis/summary?pi=25Q1,25Q2,25Q3,25Q4&art=C4ART&include_completed=true
```

**Result:** `include_completed=true` is added

**Stuck Items Returned:**
- C4ART-129: 126.8 days (Status: Done) ✅
- C4ART-26: 24.1 days (Status: Done) ✅
- C4ART-XX: 256 days (Status: Done) ✅ **Included for historical accuracy**

## Benefits

### For Users

1. **Historical Accuracy**: See complete picture of what happened in past PIs
2. **No Manual Configuration**: Automatic detection based on PI dates
3. **Consistent Behavior**: Statistics and stuck_items list match
4. **Better Root Cause Analysis**: Can investigate the actual worst-case items

### For System

1. **Single Source of Truth**: PI configuration dates drive the behavior
2. **No UI Changes**: Works automatically without new controls
3. **Backward Compatible**: Defaults to current behavior if parameter not provided
4. **Clear Separation**: Current vs historical analysis handled differently

## Logging

When running with historical PIs, you'll see:

```
📅 Historical analysis detected - requesting completed items from DL Webb API
📅 PI 25Q1 is historical (2024-12-16 to 2025-03-16, today: 2026-01-20)
📅 PI 25Q2 is historical (2025-03-17 to 2025-06-15, today: 2026-01-20)
📅 PI 25Q3 is historical (2025-06-16 to 2025-09-14, today: 2026-01-20)
📅 PI 25Q4 is historical (2025-09-15 to 2025-12-14, today: 2026-01-20)
📊 Stuck items filtering: Selected PIs=['25Q1', '25Q2', '25Q3', '25Q4'], Today=2026-01-20, Is Historical=True
📋 Historical analysis: Keeping all 45 stuck_items (including completed)
```

## Testing

### Test Case 1: Current PI
- Select PI: 26Q1
- Expected: No `include_completed` parameter
- Stuck items should exclude completed items

### Test Case 2: Historical PI
- Select PI: 25Q1
- Expected: `include_completed=true` parameter
- Stuck items should include completed items

### Test Case 3: Mixed PIs (Current + Historical)
- Select PIs: 25Q4, 26Q1
- Expected: No `include_completed` parameter (at least one is current)
- Behavior: Current analysis mode

### Test Case 4: No PI Configuration
- Select PI: 27Q1 (not configured in database)
- Expected: Default to historical mode (include completed)
- Fallback: Safe to show all data

## Related Files

- `backend/main.py` - PI date detection and parameter passing
- `backend/integrations/leadtime_client.py` - API client with include_completed support
- `backend/database.py` - RuntimeConfiguration model for PI configs
- **DL Webb API** - Needs implementation to support this parameter

## Future Enhancements

1. **Cache PI configurations** to avoid repeated database queries
2. **Add UI indicator** showing "Historical Mode" vs "Current Mode"
3. **Support date range overrides** for custom historical analysis
4. **Export metadata** including whether analysis was historical or current

## Status

✅ **Evaluation Coach Backend**: Implemented  
⏳ **DL Webb API Backend**: Requires implementation  
📅 **Date**: 2026-01-20
