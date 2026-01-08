# Excel Export Feature for Executive Summary

## Overview
Added functionality to export all example features mentioned in the AI Insights Executive Summary report to an Excel file with multiple sheets for detailed analysis.

## What's Included in the Export

### Sheet 1: Stuck Items
- **ALL stuck items** (not just top 3 shown in UI)
- Sorted by `days_in_stage` (worst first)
- Columns:
  - `issue_key` - Jira issue identifier
  - `art` - Agile Release Train
  - `current_stage` - Current workflow stage
  - `days_in_stage` - Days stuck in current stage
  - `summary` - Issue description
  - `status` - Current status
  - `pi` - Program Increment

### Sheet 2: Bottleneck Analysis
- **ALL workflow stages** with bottleneck scores
- Sorted by `Bottleneck Score` (highest first)
- Columns:
  - `Stage` - Workflow stage name
  - `Bottleneck Score` - Calculated score (mean_time/10 + exceeding%)
  - `Mean Time (days)` - Average time in stage
  - `Total Items` - Total items in stage
  - `Items Exceeding Threshold` - Count exceeding threshold
  - `Exceeding %` - Percentage exceeding threshold

### Sheet 3: WIP Statistics
- **ALL stages** with Work In Progress data
- Sorted by `Total Items (WIP)` (highest first)
- Columns:
  - `Stage` - Workflow stage name
  - `Total Items (WIP)` - Current WIP count
  - `Mean Time (days)` - Average time in stage
  - `Items Exceeding Threshold` - Count exceeding threshold
  - `Exceeding %` - Percentage exceeding threshold

### Sheet 4: Summary
- High-level statistics:
  - Total Stuck Items
  - Total Workflow Stages
  - Stages with High WIP (>1000)
  - Highest Bottleneck Score
  - Analysis Scope (ARTs and PIs applied)

## How to Use

### From the Insights Tab:
1. Navigate to **Dashboard** → **Insights** tab
2. Select your filters (PIs, ARTs)
3. Click **"Generate AI Insights"** button
4. Once insights are generated, click the new **"📊 Export to Excel"** button
5. Excel file will automatically download with all data

### File Naming Convention:
```
executive_summary_<ART>_<PI>_<timestamp>.xlsx
```

Examples:
- `executive_summary_ACEART_25Q4_20260108_143022.xlsx` (single ART, single PI)
- `executive_summary_MultiART_MultiPI_20260108_143022.xlsx` (multiple ARTs/PIs)

## Why This Is Better Than UI Display

1. **Complete Data**: Export includes ALL stuck items and stages, not just top 3-4 shown in UI
2. **Sortable**: Excel allows you to sort and filter by any column
3. **Analysis**: Can perform additional analysis, create pivot tables, charts
4. **Sharing**: Easy to share with stakeholders or include in reports
5. **Historical**: Save exports over time to track improvements

## Backend Implementation

**New Endpoint:** `GET /api/v1/insights/export-summary`

**Query Parameters:**
- `pis` - Comma-separated list of Program Increments (optional)
- `arts` - Comma-separated list of ARTs (optional)

**Technology:**
- Uses `pandas` with `openpyxl` engine to create Excel files
- Creates multi-sheet workbook with proper formatting
- Streams file directly to browser for download

## Example Use Cases

### 1. Deep Dive on ACEART
The UI only shows top 3 stuck items, but ACEART might have 20+ stuck items. Export to Excel to see all of them sorted by days in stage.

### 2. Identify Patterns
Export data for multiple PIs, compare in Excel to identify recurring bottlenecks or stuck item patterns across quarters.

### 3. Executive Reporting
Include Excel export in monthly/quarterly reports to provide detailed backup data for high-level insights presented in meetings.

### 4. Team Retrospectives
Use the exported data in team retrospectives to discuss specific stuck items and bottleneck stages with detailed metrics.

## Technical Notes

### Frontend Changes:
- Added "Export to Excel" button in Insights tab ([frontend/app.js](frontend/app.js:1269-1290))
- Added `exportExecutiveSummary()` function ([frontend/app.js](frontend/app.js:3292-3350))
- Respects current filter state (PIs, ARTs)
- Shows loading overlay during export
- Automatically triggers download when complete

### Backend Changes:
- New endpoint `/api/v1/insights/export-summary` ([backend/main.py](backend/main.py:852-1037))
- Fetches same data as executive summary insight
- Creates Excel workbook with 4 sheets
- Uses pandas DataFrame for Excel generation
- Returns StreamingResponse with proper MIME type and filename

## Testing

To test the feature:
1. Start the application: `./start.sh`
2. Go to Insights tab
3. Select filters: PIs = `25Q4, 25Q3, 25Q2, 25Q1`
4. Click "Generate AI Insights"
5. Click "📊 Export to Excel"
6. Open downloaded Excel file and verify all 4 sheets contain data

## Future Enhancements

Potential improvements:
1. Add conditional formatting in Excel (color-code high bottleneck scores)
2. Include charts/graphs in Excel workbook
3. Export individual insights as separate sheets
4. Add filtering options directly in export dialog
5. Schedule automated exports (email daily/weekly reports)
