# Waste Analysis & Throughput Integration

## Overview
This document describes the integration of waste analysis and throughput trends from the DL Webb App into the Evaluation Coach metrics catalog.

## Implementation Date
2025-01-XX

## Changes Made

### Backend Updates

#### 1. Metrics Catalog Endpoint (`/api/metrics/catalog`)
**File:** `backend/main.py` (lines ~1970-2100)

Added two new metric types to the Flow Metrics section:

##### Waste Metric
```python
"waste": {
    "name": "Process Waste",
    "description": "Days wasted in waiting states and removed work",
    "formula": "sum(waiting_time) + removed_work_count",
    "current_value": 511.4,  # Total waste days
    "unit": "days",
    "status": "high",  # From DL Webb App waste categories
    "breakdown": {
        "waiting_time": {
            "ready_for_sit": 210.0,
            "ready_for_deployment": 301.4
        },
        "removed_work": {
            "duplicates": 184,
            "planned_removed": 0,
            "added_removed": 0
        }
    }
}
```

**Data Source:** `leadtime_client.get_waste_analysis()`
- Fetches waiting time waste by stage
- Fetches removed work counts (duplicates, planned, added)
- Calculates total waste days

##### Throughput Metric
```python
"throughput": {
    "name": "Throughput",
    "description": "Features completed per PI/Sprint",
    "formula": "count(status = 'Done') / time_period",
    "current_value": 27,  # Total features completed
    "unit": "features",
    "average_per_pi": 27.0,
    "trend_by_pi": {
        "26Q1": {
            "throughput": 27,
            "avg_leadtime": 125.6
        },
        "25Q4": {
            "throughput": 42,
            "avg_leadtime": 98.3
        }
        // ... last 6 PIs
    }
}
```

**Data Source:** `leadtime_client.get_throughput_analysis()`
- Fetches throughput by PI with average lead time
- Shows trend over last 6 Program Increments
- Displays per-PI completion rates

### Frontend Updates

#### 2. Metric Card Rendering (`frontend/app.js`)
**Function:** `createMetricCard()` (lines ~1460-1540)

Added two new expandable sections:

##### Waste Breakdown Section
```javascript
${metric.breakdown ? `
    <details>
        <summary>View Waste Breakdown</summary>
        <div>
            ⏱️ Waiting Time Waste
            - ready_for_sit: 210.0 days
            - ready_for_deployment: 301.4 days
            
            🗑️ Removed Work
            - Duplicates: 184 items
            - Planned Removed: 0 items
            - Added Removed: 0 items
        </div>
    </details>
` : ''}
```

##### Throughput Trend Section
```javascript
${metric.trend_by_pi ? `
    <details>
        <summary>View Throughput by PI</summary>
        <div>
            26Q1: 27 features (125.6 days avg)
            25Q4: 42 features (98.3 days avg)
            // ... last 6 PIs
        </div>
    </details>
` : ''}
```

#### 3. Flow Metrics Display
**Function:** `renderMetricsCatalog()` (lines ~1530-1550)

Updated to include waste metric:
```javascript
flowMetricsDiv.innerHTML = `
    ${createMetricCard(flowMetrics.lead_time)}
    ${createMetricCard(flowMetrics.cycle_time)}
    ${createMetricCard(flowMetrics.wip)}
    ${createMetricCard(flowMetrics.throughput)}
    ${flowMetrics.waste ? createMetricCard(flowMetrics.waste) : ''}
`;
```

### Frontend Cleanup

#### 4. Removed Fake/Static Data
**File:** `frontend/index.html` (lines ~395-480)

Removed hardcoded metric values:
- ❌ "67% flow efficiency" card
- ❌ "1.3x WIP" card
- ❌ Static "Industry Average: 45 days"
- ❌ Static "High Performer: 21 days"
- ✅ Replaced with loading placeholders

All metrics now load dynamically from real data.

## API Endpoints Used

### DL Webb App (Port 8000)
1. **`/api/analysis/waste`**
   - Returns waiting time waste by stage
   - Returns removed work counts
   - Categories: High/Medium/Low waste

2. **`/api/analysis/throughput`**
   - Returns overall throughput statistics
   - Returns by-PI throughput with average lead time
   - Supports filtering by ART and PI

### Evaluation Coach (Port 8850)
1. **`GET /api/metrics/catalog`**
   - Query params: `arts`, `pis`
   - Returns comprehensive metrics including waste and throughput
   - Example: `http://localhost:8850/api/metrics/catalog?arts=SAART&pis=26Q1`

## Example Output

### Waste Metric (SAART PI 26Q1)
```
Process Waste
511.4 days total
Status: HIGH

Breakdown:
⏱️ Waiting Time Waste
  - ready_for_sit: 210.0 days
  - ready_for_deployment: 301.4 days

🗑️ Removed Work
  - Duplicates: 184 items
  - Planned Removed: 0 items
  - Added Removed: 0 items
```

### Throughput Metric (SAART PI 26Q1)
```
Throughput
27 features completed
Average: 27.0 per PI
Status: GOOD

Trend by PI:
  26Q1: 27 features (125.6 days avg)
```

## Benefits

1. **Real Data Integration**: All metrics now use live data from DL Webb App
2. **Waste Visibility**: Teams can identify bottleneck stages with highest waste
3. **Throughput Trends**: Historical view of delivery rates and lead times
4. **Actionable Insights**: Expandable sections provide detailed breakdowns
5. **No Fake Data**: Eliminated all hardcoded/demo values

## Testing

### Backend Test
```bash
curl "http://localhost:8850/api/metrics/catalog?arts=SAART&pis=26Q1"
```

Expected response includes:
- `flow_metrics.waste` with breakdown
- `flow_metrics.throughput` with trend_by_pi

### Frontend Test
1. Open `http://localhost:8800`
2. Navigate to "Metrics" tab
3. Select SAART + 26Q1
4. Verify waste and throughput cards appear
5. Expand "View Waste Breakdown" and "View Throughput by PI"

## Future Enhancements

### Phase 2 (Pending)
1. **WIP Trends Timeline**
   - Endpoint: `/api/analysis/trends`
   - Weekly WIP chart with status breakdown
   - Estimated: 1-2 hours

2. **Story Comprehensive Metrics**
   - Endpoint: `/api/analysis/story-comprehensive`
   - P50/P75/P90 percentiles
   - Lead time distribution histogram
   - Estimated: 1-2 hours

## Related Documents
- [METRICS_GUIDE.md](./METRICS_GUIDE.md) - Comprehensive metrics definitions
- [LEADTIME_INTEGRATION.md](./LEADTIME_INTEGRATION.md) - DL Webb App integration details
- [DATA_SOURCES.md](./DATA_SOURCES.md) - Data source documentation

## Implementation Notes

### API Parameter Convention
DL Webb App expects **singular** parameter names:
- ✅ `art=SAART` (singular)
- ❌ `arts=SAART` (plural)

This was corrected across all 7 methods in `leadtime_client.py`.

### Status Color Mapping
Frontend uses consistent status colors:
- 🟢 Green (`#34C759`): good/low
- 🟡 Yellow (`#FF9500`): warning/medium
- 🔴 Red (`#FF3B30`): critical/high

### Waste Status Handling
Waste metric status comes from DL Webb App waste categories:
```python
status = waste_categories.get("waiting_waste", "unknown").lower()
```

Values: `"high"`, `"medium"`, `"low"`, `"unknown"`
