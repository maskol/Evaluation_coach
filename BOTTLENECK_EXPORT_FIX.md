# Bottleneck Export Empty Items Fix

## Problem
When exporting a **Critical Bottleneck** insight, the export showed "Total Items: 0" even though there were stuck features/stories detected in the bottleneck stage. The user couldn't see which features were stuck.

### Root Cause
The export logic relied on extracting issue keys (e.g., "UCART-1234") from the insight's evidence using regex pattern matching. However, bottleneck insights sometimes don't include specific issue keys in their evidence - they only show aggregate metrics like:
- "Mean duration: 87.0 days"
- "Maximum observed: 153 days"
- "2 stage occurrences exceeding threshold"

When no issue keys were found in the evidence, the `issue_keys` set was empty, resulting in:
1. No stuck items matched (empty filter)
2. No flow items matched (empty filter)
3. Export showing 0 total items

## Solution
Enhanced the export logic to specifically detect **bottleneck insights** and include ALL stuck items for the identified bottleneck stage, regardless of whether issue keys appear in the evidence. Added multiple fallback strategies to ensure items are found.

### Changes Made

#### 1. Bottleneck Detection
```python
# Detect if this is a bottleneck insight by checking title
insight_title = insight_data.get("title", "").lower()
is_bottleneck_insight = "bottleneck" in insight_title
bottleneck_stage = None

if is_bottleneck_insight:
    # Extract stage name from title like "Critical Bottleneck in In Sit Stage"
    stage_pattern = r"bottleneck in (.+?) stage"
    stage_match = re.search(stage_pattern, insight_title, re.IGNORECASE)
    if stage_match:
        # Convert "In Sit" back to "in_sit"
        bottleneck_stage = stage_match.group(1).lower().replace(" ", "_")
        print(f"🎯 Detected bottleneck insight for stage: {bottleneck_stage}")
```

#### 2. Include All Stuck Items for Bottleneck Stage
```python
# For bottleneck insights, include ALL stuck items for that stage
if is_bottleneck_insight and bottleneck_stage:
    # Try multiple stage name variations (underscore/space/case differences)
    stage_variations = [
        bottleneck_stage,  # e.g., "in_sit"
        bottleneck_stage.replace("_", " "),  # e.g., "in sit"
        bottleneck_stage.replace("_", " ").title(),  # e.g., "In Sit"
    ]
    
    for item in stuck_items:
        item_stage_raw = item.get("stage", "")
        item_stage_lower = item_stage_raw.lower()
        
        # Flexible matching to handle format variations
        stage_matches = any(
            item_stage_lower == var.lower() or 
            item_stage_lower.replace(" ", "_") == var.lower() or
            item_stage_lower.replace("_", " ") == var.lower()
            for var in stage_variations
        )
        
        if stage_matches:
            related_items.append({...})
```

#### 3. Fallback to Flow Data
If no stuck items are found (empty or filtered out), check flow/leadtime data for items that spent time in the bottleneck stage:

```python
if len(related_items) == 0:
    # Check flow data for items with problematic stage in history
    for item in flow_data:
        current_status = item.get("current_status", "").lower()
        stages_duration = item.get("stages_duration", {})
        
        # Check if item passed through bottleneck stage
        if current_status matches bottleneck_stage OR
           bottleneck_stage in stages_duration:
            related_items.append({
                "category": "Flow Item (Bottleneck Stage)",
                "days_in_stage": stages_duration.get(bottleneck_stage, 0),
                ...
            })
```

#### 4. Additional Improvements
- Also extract issue keys from `recommended_actions` (not just evidence and root causes)
- Handle both `team` and `development_team` field names for better compatibility
- Handle both `age` and `age_days` field names for total leadtime

## Testing
Created comprehensive test in `test_bottleneck_export.py` that validates:
1. Bottleneck insight detection from various title patterns
2. Stage name extraction from insight titles
3. Stuck items filtering by stage

## Expected Behavior After Fix

### Before Fix
```
Field Value
Title Critical Bottleneck in In Sit Stage
...
Total Items 0  ❌ Empty export
```

### After Fix
```
Field Value
Title Critical Bottleneck in In Sit Stage
...
Total Items 2  ✅ Shows all stuck items in that stage

Related Features Sheet:
issue_key    category     current_stage  days_in_stage  total_leadtime
UCART-1234   Stuck Item   in_sit        153.0          180.0
UCART-5678   Stuck Item   in_sit        87.0           120.0
```

## Files Modified
- `backend/main.py` - Enhanced export_insight_to_excel endpoint (lines ~1823-1935)

## Files Created
- `test_bottleneck_export.py` - Test suite for the fix

## Impact
- ✅ Users can now see which features are stuck when exporting bottleneck insights
- ✅ Export includes all items in the bottleneck stage, not just those mentioned in evidence
- ✅ Better debugging and root cause analysis for bottleneck issues
- ✅ Maintains backward compatibility with insights that do have issue keys in evidence
