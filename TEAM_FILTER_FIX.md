# Team Filtering Fix - Data Accuracy Issue

## Problem

**Critical bug reported**: AI insights were showing incorrect team data when filtering by team. 

**Example**:
- Filter: `ART: UCART | Team: Loke`
- Insight showed: `UCART-2228` with `team THOR` (not Loke), `in_sit: 153 days`
- Excel export showed: `UCART-2228` belongs to `team THOR`, `in_sit: 0 days`

## Root Cause

The bottleneck analysis functions were filtering stuck items by ART and stage, but **NOT by team** (`development_team` field). This caused insights to include items from all teams in the ART when a specific team was selected.

## Solution

Added team filtering to all stuck_items analysis locations:

### Files Modified

#### 1. `/backend/agents/nodes/advanced_insights.py`
- **Line 206-218**: Added team filter in `_analyze_bottlenecks()`
- **Line 415-428**: Added team filter in `_analyze_stuck_item_patterns()`
- **Line 1871-1878**: Added team filter in `_generate_executive_summary()`

#### 2. `/backend/agents/nodes/story_insights.py`
- **Line 170-177**: Added team filter in `_analyze_story_bottlenecks()`
- **Line 264-270**: Added team filter in `_analyze_story_stuck_items()`

### Code Pattern Applied

```python
# Filter by team if specified (critical for team view accuracy)
if selected_team:
    stuck_items = [
        item for item in stuck_items if item.get("development_team") == selected_team
    ]
```

This filter is applied **immediately after** retrieving `stuck_items` from `bottleneck_data`, ensuring that all subsequent analysis operates only on items belonging to the selected team.

## Impact

- **Before**: Team-filtered views showed items from other teams in the same ART
- **After**: Team-filtered views show only items belonging to the selected team
- **Data Accuracy**: Metrics (days in stage, stuck items, etc.) now accurately reflect the selected team's performance

## Testing

To verify the fix:
1. Navigate to Team View
2. Select ART: `UCART`
3. Select Team: `Loke`
4. Generate insights
5. Verify that only features with `development_team: "Loke"` appear in bottleneck analysis
6. Example: `UCART-2228` (team THOR) should **not** appear when filtering for team Loke

## Related Issues

- ART-team filtering fix (art_key vs art_name mismatch)
- Alphabetical sorting of ARTs

## Technical Notes

The `stuck_items` array contains feature/story objects with these key fields:
- `issue_key`: Feature ID (e.g., "UCART-2228")
- `art`: ART key (e.g., "UCART")
- `development_team`: Team name (e.g., "Loke", "THOR")
- `stage`: Current stage (e.g., "in_sit", "in_progress")
- `days_in_stage`: Time stuck in current stage

All insight generation functions must filter by **all three dimensions** (ART, team, PI) when analyzing bottlenecks to ensure data accuracy.
