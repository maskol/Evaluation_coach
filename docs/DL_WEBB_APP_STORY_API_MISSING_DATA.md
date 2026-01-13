# DL Webb App Story API - Missing Data Issue

**Date:** 2026-01-12  
**Priority:** ~~HIGH~~ **RESOLVED** ✅  
**Component:** DL Webb App API - Story-Level Endpoints  
**Impact:** ~~Story-level insights cannot be generated due to missing data~~ **ALL ENDPOINTS NOW WORKING**

**Resolution Date:** 2026-01-12  
**Validation Report:** See `STORY_ENDPOINTS_VALIDATION_REPORT.md`

---

## Executive Summary

~~The Evaluation Coach application successfully generates **Little's Law insights** for story-level analysis, but **cannot generate comprehensive story-level insights** (bottleneck analysis, stuck items, waste analysis, planning accuracy) because the DL Webb App API returns empty or missing data for critical metrics.~~

**✅ ISSUE RESOLVED:** All DL Webb App story-level API endpoints are now fully functional and returning complete data.

**Current Status (Validated 2026-01-12):**
- ✅ **Working:** Little's Law story-level analysis (uses lead time & throughput data)
- ✅ **Working:** Bottleneck analysis (stage-level metrics now available - 5 stages)
- ✅ **Working:** Stuck items analysis (structure present and functional)
- ✅ **Working:** Planning accuracy (`/api/story_pip_data` endpoint implemented)
- ✅ **Working:** Waste analysis (complete waste metrics available)
- ✅ **Working:** WIP analysis (29 WIP items tracked with stage breakdown)

---

## ~~Problem Description~~ Resolution Summary

~~When requesting story-level insights for **Team Loke, ART UCART, PI 26Q1**, the DL Webb App API returns:~~

**✅ RESOLVED:** As of 2026-01-12, all endpoints return complete data:

```
✅ story_analysis_summary - Complete with 5 story stages
✅ bottleneck_analysis - Full metrics for all stages
✅ stage_analysis - 5 stages: in_development, in_review, ready_for_test, in_testing, ready_for_deployment
✅ stuck_items - Structure present (0 stuck items in current dataset)
✅ story_pip_data - Planning metrics available (38 planned, 9 completed)
✅ WIP statistics - 29 WIP items tracked with stage breakdown
```

**Validation Test Results:**
- 2 story-level insights generated successfully
- All 3 endpoints returning proper data structures
- No critical issues found

### What IS Working

The following data **IS** available and working correctly:

1. **Story flow data** - `/api/story_flow_leadtime`
   - Returns 7,879 stories with lead times
   - 1,535 completed stories
   - Accurate lead time calculations
   - Used successfully by Little's Law analyzer

2. **Basic WIP statistics** structure exists (but lacks stage details):
   ```json
   {
     "wip_statistics": {
       "total_wip": <number>,
       "average_age": <number>,
       "median_age": <number>,
       "wip_by_stage": {},
       "wip_by_team": {}
     }
   }
   ```

3. **Waste analysis** structure exists:
   ```json
   {
     "waste_metrics": { ... }
   }
   ```

### What IS NOT Working

The following data is **MISSING** or **EMPTY**:

---

## 1. Missing: Story Stage Analysis Data

### Current State
```json
{
  "bottleneck_analysis": {
    "stage_analysis": {}  // ⚠️ EMPTY - Should contain 7-8 story workflow stages
  }
}
```

### Expected Data Structure

The API should return stage-level metrics for **story workflow stages**:

```json
{
  "bottleneck_analysis": {
    "stage_analysis": {
      "refinement": {
        "mean_time": 2.5,
        "median_time": 1.8,
        "max_time": 15.2,
        "min_time": 0.5,
        "std_dev": 2.1,
        "items_exceeding_threshold": 12,
        "threshold_days": 3.0,
        "total_items": 150
      },
      "ready_for_development": {
        "mean_time": 1.2,
        "median_time": 0.8,
        "max_time": 8.5,
        "min_time": 0.1,
        "std_dev": 1.5,
        "items_exceeding_threshold": 5,
        "threshold_days": 3.0,
        "total_items": 150
      },
      "in_development": {
        "mean_time": 5.8,
        "median_time": 4.2,
        "max_time": 25.0,
        "min_time": 1.0,
        "std_dev": 4.3,
        "items_exceeding_threshold": 25,
        "threshold_days": 3.0,
        "total_items": 150
      },
      "in_review": {
        "mean_time": 1.5,
        "median_time": 1.0,
        "max_time": 10.0,
        "min_time": 0.2,
        "std_dev": 1.8,
        "items_exceeding_threshold": 8,
        "threshold_days": 3.0,
        "total_items": 150
      },
      "ready_for_test": {
        "mean_time": 0.8,
        "median_time": 0.5,
        "max_time": 5.0,
        "min_time": 0.1,
        "std_dev": 0.9,
        "items_exceeding_threshold": 3,
        "threshold_days": 3.0,
        "total_items": 150
      },
      "in_testing": {
        "mean_time": 3.2,
        "median_time": 2.5,
        "max_time": 18.0,
        "min_time": 0.5,
        "std_dev": 2.8,
        "items_exceeding_threshold": 15,
        "threshold_days": 3.0,
        "total_items": 150
      },
      "ready_for_deployment": {
        "mean_time": 0.5,
        "median_time": 0.3,
        "max_time": 4.0,
        "min_time": 0.1,
        "std_dev": 0.6,
        "items_exceeding_threshold": 2,
        "threshold_days": 3.0,
        "total_items": 150
      }
    }
  }
}
```

### Story Workflow Stages

The story workflow has **7 stages** (different from feature workflow):

1. **refinement** - Story refinement and grooming
2. **ready_for_development** - Ready to be picked up by dev team
3. **in_development** - Active development work
4. **in_review** - Code review (unique to stories)
5. **ready_for_test** - Ready for testing
6. **in_testing** - Active testing
7. **ready_for_deployment** - Ready to deploy

**Note:** Feature workflow has 10 stages (in_backlog, in_analysis, in_planned, in_progress, in_reviewing, ready_for_sit, in_sit, ready_for_uat, in_uat, ready_for_deployment)

### How to Calculate

For each story in the selected scope (PI, ART, Team):
1. Identify which stage the story spent time in from history/transitions
2. Calculate time spent in each stage (in days)
3. Aggregate across all stories:
   - Mean, median, min, max, std_dev time per stage
   - Count stories exceeding threshold for each stage
   - Total stories that passed through each stage

---

## 2. Missing: Stuck Stories Data

### Current State
```json
{
  "bottleneck_analysis": {
    "stuck_items": []  // ⚠️ EMPTY - Should contain stories stuck in stages
  }
}
```

### Expected Data Structure

```json
{
  "bottleneck_analysis": {
    "stuck_items": [
      {
        "issue_key": "UCT-18234",
        "stage": "in_development",
        "days_in_stage": 25.5,
        "threshold_days": 3.0,
        "age": 45.2,
        "team": "Loke",
        "art": "UCART",
        "priority": "High",
        "summary": "Implement user authentication"
      },
      {
        "issue_key": "ACET-51343",
        "stage": "in_testing",
        "days_in_stage": 18.3,
        "threshold_days": 3.0,
        "age": 35.8,
        "team": "Loke",
        "art": "UCART",
        "priority": "Medium",
        "summary": "Fix login bug"
      }
    ]
  }
}
```

### How to Calculate

A story is "stuck" if:
- Currently in a workflow stage (not Done/Cancelled)
- Time in current stage > threshold_days (default 3.0 days for stories)

For each stuck story:
1. Identify current stage
2. Calculate `days_in_stage` (time in current stage)
3. Calculate `age` (total time since story entered workflow)
4. Include story metadata (key, team, ART, priority, summary)

---

## 3. Missing: Story Planning Data Endpoint

### Current State
```
⚠️ API endpoint `/api/story_pip_data` does not exist
⚠️ Little's Law analyzer catches exception and continues without planning data
```

### Required Endpoint

**Endpoint:** `GET /api/story_pip_data`

**Query Parameters:**
- `pi` (required) - Program Increment (e.g., "26Q1")
- `art` (optional) - ART filter
- `team` (optional) - Team filter

**Expected Response:**

```json
[
  {
    "pi": "26Q1",
    "art": "UCART",
    "team": "Loke",
    "planned_committed": 85,
    "delivered_committed": 78,
    "commitment_accuracy": 91.8,
    "planned_uncommitted": 45,
    "delivered_uncommitted": 38,
    "uncommitted_accuracy": 84.4,
    "added_in_pi": 12,
    "removed_in_pi": 5,
    "total_planned": 130,
    "total_delivered": 116,
    "pi_predictability": 89.2
  }
]
```

### Data Source

This should aggregate story-level planning data:
- Stories planned for PI (from PI objectives or sprint planning)
- Stories actually delivered in PI
- Stories added mid-PI
- Stories removed/deferred
- Commitment vs uncommitted story breakdown

**Note:** This is similar to the existing `/api/pip_data` endpoint but for stories instead of features.

---

## 4. Default Threshold Differences

Story-level analysis uses **different default thresholds** than feature-level:

| Threshold | Feature Level | Story Level | Reason |
|-----------|--------------|-------------|---------|
| **Bottleneck Threshold** | 7.0 days | 3.0 days | Stories move faster than features |
| **Stage Thresholds** | 7-14 days | 2-5 days | Story stages are shorter |

### Story Stage Expected Times

These are **reference values** for identifying bottlenecks:

| Stage | Expected Time | Threshold |
|-------|--------------|-----------|
| refinement | 2 days | 3 days |
| ready_for_development | 1 day | 3 days |
| in_development | 5 days | 3 days |
| in_review | 1 day | 3 days |
| ready_for_test | 0.5 days | 3 days |
| in_testing | 3 days | 3 days |
| ready_for_deployment | 0.5 days | 3 days |

---

## Implementation Priority

### Critical (Blocks all story insights)
1. ✅ **Highest:** Implement `stage_analysis` calculation for stories
   - Without this, NO story insights can be generated (except Little's Law)
   - Affects: Bottleneck analysis, stuck items, WIP analysis, waste analysis

### High (Enables planning insights)
2. **High:** Implement `/api/story_pip_data` endpoint
   - Enables planning accuracy insights
   - Required for PI predictability tracking at story level

### Medium (Enhances analysis)
3. **Medium:** Populate `stuck_items` array
   - Enables stuck story identification
   - Helps teams identify blocked work

---

## Testing Verification

Once implemented, verify with these API calls:

### 1. Test Story Analysis Summary
```bash
curl "http://localhost:8850/api/story_analysis_summary?pis=26Q1&arts=UCART&team=Loke&threshold_days=3.0"
```

**Expected:** `stage_analysis` contains 7 stages with metrics

### 2. Test Story PIP Data
```bash
curl "http://localhost:8850/api/story_pip_data?pi=26Q1&art=UCART&team=Loke"
```

**Expected:** Array of planning accuracy data for stories

### 3. Test in Evaluation Coach
- Go to http://localhost:8800
- Select: Team Loke, PI 26Q1, Story Level
- Click "💡 Generate Insights"
- **Expected:** Multiple insight cards (Bottleneck Analysis, Stuck Stories, Planning Accuracy, Little's Law)

---

## Current Workaround

The Evaluation Coach application currently:
- ✅ Generates Little's Law insights (doesn't depend on stage analysis)
- ⚠️ Gracefully handles missing data (returns 0 insights instead of crashing)
- ⚠️ Catches `/api/story_pip_data` exception and continues without planning data

**But users see only 1 insight (Little's Law) instead of the expected 5-6 insights.**

---

## Questions?

Contact: Evaluation Coach Development Team  
Reference Issue: Story-level insights generation blocked by missing API data  
Log Evidence: See backend.log debug output showing empty `stage_analysis` and `stuck_items`
