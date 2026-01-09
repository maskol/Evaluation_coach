# Display Excluded Statuses Feature

## Overview

This feature ensures that both **AI Insights** and **PI Reports** display which feature statuses are excluded from analysis, providing transparency about what data is being filtered.

## What Was Changed

### Backend Changes

#### 1. PI Report Generation (`backend/main.py`)

**Location**: `/api/v1/insights/pi-report` endpoint (lines ~540-550, ~632)

Added excluded statuses information to the data context sent to the LLM:

**Multi-PI Reports:**
```python
excluded_status_note = f"\n**Note:** Features with the following statuses are excluded from analysis: {', '.join(excluded_statuses)}" if excluded_statuses else ""
data_context = f"""
**Analysis Period:** {pi_list} ({len(pis)} Program Increments)
**Report Type:** Multi-PI Performance Analysis{excluded_status_note}
```

**Single PI Reports:**
```python
excluded_status_note = f"\n**Note:** Features with the following statuses are excluded from analysis: {', '.join(excluded_statuses)}" if excluded_statuses else ""
data_context = f"""
**PI Being Analyzed:** {pi}{excluded_status_note}

**Current PI Performance:**
```

#### 2. AI Insights Generation (`backend/main.py`)

**Location**: `/api/v1/insights/generate` endpoint (lines ~815-820, ~885-895)

- Retrieves excluded statuses from database at the start of insights generation
- Includes excluded statuses in the API response with filter information:

```python
return {
    "status": "success",
    "insights": [insight.dict() for insight in insights],
    "count": len(insights),
    "excluded_statuses": excluded_statuses,
    "filter_info": {
        "excluded_statuses": excluded_statuses,
        "selected_pis": selected_pis,
        "selected_arts": selected_arts,
    },
}
```

### Frontend Changes

#### 1. Display Excluded Statuses in AI Insights Tab (`frontend/app.js`)

**Location**: Lines ~1218-1225, ~1305-1320

**Changes:**
1. Updated `generateInsights()` to extract `excluded_statuses` and `filter_info` from API response
2. Modified `displayGeneratedInsights()` function signature to accept these parameters
3. Added excluded statuses to the filter display bar:

```javascript
// Add excluded statuses info
if (excludedStatuses && excludedStatuses.length > 0) {
    filterParts.push(`Excluded: ${excludedStatuses.join(', ')}`);
}
```

**Visual Result:**

```
📊 Active Filters
Portfolio | PI: 24Q4, 24Q3 | All ARTs | Excluded: Cancelled, On Hold
```

## How It Works

### Configuration

Excluded statuses are configured in the **Admin Panel**:

1. Go to http://localhost:8800/admin.html
2. Find the "Exclude Feature Statuses from Analysis" section
3. Enter comma-separated statuses (e.g., `Cancelled, On Hold`)
4. Click "Save Display Options"

### When Generating AI Insights

1. User clicks "💡 Generate Insights" button
2. Backend retrieves excluded statuses from database using `get_excluded_feature_statuses(db)`
3. Features with these statuses are filtered out before analysis
4. API returns insights along with `excluded_statuses` array
5. Frontend displays excluded statuses in the filter info bar

### When Generating PI Reports

1. User clicks "📊 Generate PI Report"
2. Backend retrieves excluded statuses from database
3. Adds a note to the report context: `**Note:** Features with the following statuses are excluded from analysis: ...`
4. LLM includes this information in the generated report narrative
5. Report displays the excluded statuses as part of the analysis context

## Example Output

### AI Insights Tab

**Filter Bar:**
```
📊 Active Filters
Portfolio | PI: 24Q4, 24Q3 | ARTs: ACEART, CAF, CITPF | Excluded: Cancelled, On Hold
```

### PI Report

**Report Header:**
```
**PI Being Analyzed:** 24Q4
**Note:** Features with the following statuses are excluded from analysis: Cancelled, On Hold

**Current PI Performance:**
- Flow Efficiency: 45.2%
- Average Lead-Time: 42.3 days
- Planning Accuracy: 78.5%
- Features Delivered: 127
```

## Benefits

1. **Transparency**: Users can see exactly what data is being analyzed
2. **Clarity**: Eliminates confusion about why certain features don't appear in metrics
3. **Auditability**: Clear documentation of what was excluded in historical reports
4. **Context**: Helps users interpret results correctly based on filtered data

## Files Modified

- `backend/main.py` - Added excluded statuses to PI reports and insights responses
- `frontend/app.js` - Updated to display excluded statuses in AI Insights tab

## Testing

### Test 1: Configure Excluded Statuses

```bash
# Set excluded statuses
curl -X POST http://localhost:8850/api/admin/config/display \
  -H "Content-Type: application/json" \
  -d '{"excluded_feature_statuses": ["Cancelled", "On Hold"]}'
```

### Test 2: Generate AI Insights

1. Go to http://localhost:8800
2. Click "💡 Insights" tab
3. Click "Generate Insights"
4. Verify filter bar shows: `Excluded: Cancelled, On Hold`

### Test 3: Generate PI Report

1. Click "📊 Generate PI Report"
2. Select PI (e.g., 24Q4)
3. Verify report includes note about excluded statuses

### Test 4: API Response

```bash
curl -X POST "http://localhost:8850/api/v1/insights/generate?scope=portfolio" | python3 -m json.tool

# Response should include:
{
  "status": "success",
  "insights": [...],
  "count": 5,
  "excluded_statuses": ["Cancelled", "On Hold"],
  "filter_info": {
    "excluded_statuses": ["Cancelled", "On Hold"],
    "selected_pis": [],
    "selected_arts": []
  }
}
```

## Related Features

- **Inactive ARTs Filter** - Similar transparency for filtered ARTs
- **Admin Configuration** - Where excluded statuses are managed
- **Feature Status Filtering** - The underlying filtering mechanism

## Future Enhancements

- [ ] Add excluded statuses count to the display (e.g., "Excluded: 2 statuses")
- [ ] Allow clicking on excluded statuses to see which features were filtered
- [ ] Add excluded statuses to Excel export file metadata
- [ ] Show excluded statuses in Dashboard metrics cards
- [ ] Add API endpoint to get list of excluded features for auditing
