# PI Report Feature - Implementation Guide

## Overview

The PI Report feature generates comprehensive Program Increment management reports for senior leadership. These reports analyze PI performance against strategic targets, compare with previous PIs, and provide actionable proposals to achieve targets.

## Features

### 1. Comprehensive Analysis
- **Performance vs Targets**: Compare current metrics against 2026, 2027, and True North targets
- **Previous PI Comparison**: Analyze improvements and declines from previous PI
- **Root Cause Analysis**: Identify systemic issues and underlying problems
- **Actionable Proposals**: Specific, prioritized recommendations with owners and success criteria

### 2. Metrics Analyzed
- **Flow Efficiency**: Value-add time vs total lead-time
- **Average Lead-Time**: Time from backlog to done
- **Planning Accuracy**: Committed features actually delivered
- **Throughput**: Total features delivered in the PI

### 3. Report Sections
1. **Executive Summary**: High-level assessment for leadership
2. **Performance vs Targets**: Gap analysis against strategic goals
3. **Improvements from Previous PI**: Trend analysis and lessons learned
4. **Detailed Analysis**: Deep-dive into each metric
5. **Root Causes & Systemic Issues**: Underlying problems
6. **Actionable Proposals**: Short/medium/long-term recommendations
7. **Path to Target Achievement**: Roadmap to reach goals

## Usage

### From the UI

1. **Access the Feature**:
   - Click "📊 Generate PI Report" button in Quick Actions sidebar
   - Or open from any screen using the quick action button

2. **Configure Report**:
   - Select PI to analyze (e.g., "25Q4")
   - Choose whether to compare with previous PI (recommended)
   - Click "Generate Report"

3. **View Report**:
   - Report displays in a modal with:
     - Visual metrics summary card
     - Full formatted report content
     - Print functionality

4. **Print/Export**:
   - Click "🖨️ Print Report" to create PDF
   - Professional formatting for executive presentation

### From the API

**Endpoint**: `POST /api/v1/insights/pi-report`

**Request Body**:
```json
{
  "pi": "25Q4",
  "compare_with_previous": true,
  "model": "gpt-4o",
  "temperature": 0.7
}
```

**Response**:
```json
{
  "pi": "25Q4",
  "report_content": "# Executive Summary\n\n...",
  "current_metrics": {
    "flow_efficiency": 42.1,
    "avg_leadtime": 131.3,
    "planning_accuracy": 73.8,
    "throughput": 2796
  },
  "previous_metrics": {
    "pi_name": "25Q3",
    "flow_efficiency": 38.5,
    "avg_leadtime": 145.2,
    "planning_accuracy": 71.2,
    "throughput": 2654
  },
  "generated_at": "2026-01-07T10:30:00"
}
```

## Implementation Details

### Backend

**New Files**:
- `backend/services/pi_report_service.py`: PI report generation service
  - Metric calculation
  - Previous PI identification
  - Report prompt generation

**Modified Files**:
- `backend/main.py`: Added `/api/v1/insights/pi-report` endpoint
  - Fetches metrics from leadtime service
  - Compares with previous PI
  - Integrates with RAG for context
  - Generates report using LLM

### Frontend

**Modified Files**:
- `frontend/index.html`:
  - Added "Generate PI Report" button to Quick Actions
  - Added PI Report dialog modal
  - Added PI Report display modal

- `frontend/app.js`:
  - `openPIReportDialog()`: Opens PI selection dialog
  - `generatePIReport()`: Calls API and generates report
  - `displayPIReport()`: Renders report with metrics visualization
  - `printPIReport()`: Print/PDF functionality
  - `getChangeIndicator()`: Visual change indicators (arrows, colors)

### Data Flow

1. **User Action**: Clicks "Generate PI Report"
2. **Load PIs**: Fetch available PIs from dashboard API
3. **User Selection**: Select PI and comparison options
4. **API Call**: POST to `/api/v1/insights/pi-report`
5. **Backend Processing**:
   - Fetch current PI metrics from leadtime service
   - Calculate previous PI and fetch its metrics
   - Retrieve strategic targets from database
   - Query RAG for relevant context
   - Generate comprehensive report with LLM
6. **Display**: Show formatted report with metrics card
7. **Actions**: Print, export, or close

## Report Content Examples

### Executive Summary
```
The Q4 2025 Program Increment shows mixed performance with notable 
improvements in flow efficiency (+3.6%) but continued challenges in 
lead-time management. While we delivered 142 more features than Q3, 
our average lead-time remains 2.2x our 2026 target...
```

### Performance vs Targets
```
**Flow Efficiency**: 42.1% (Target: 55%)
- Gap: -12.9 percentage points
- Status: Behind target, but improving trend
- Projection: At current rate, will reach target by Q2 2026

**Average Lead-Time**: 131.3 days (Target: 60 days)
- Gap: +71.3 days (118% over target)
- Status: Critical - Major improvement needed
- Projection: Requires 15-day reduction per PI to reach target
```

### Actionable Proposals
```
**Short-term (Next Sprint)**
1. Implement WIP limits per team (Owner: RTEs, Effort: Low)
   - Success: WIP reduced by 30%
   
2. Daily dependency stand-ups (Owner: SM, Effort: Low)
   - Success: Blocked time < 20%

**Medium-term (Next PI)**
1. Architecture runway investment (Owner: Architects, Effort: High)
   - Success: Technical debt reduced 25%
   
2. Cross-team pairing program (Owner: Leads, Effort: Medium)
   - Success: Knowledge silos reduced
```

## Integration with Existing Features

### Strategic Targets
- Pulls targets from `strategic_targets` database table
- Compares current metrics against 2026, 2027, True North
- Calculates gap analysis automatically

### RAG Knowledge Base
- Queries knowledge base for relevant coaching content
- Includes best practices in report recommendations
- Enhances proposals with proven methodologies

### LLM Service
- Uses configured LLM model (default: gpt-4o)
- Respects temperature settings
- Generates natural language analysis

### Lead-Time Service
- Fetches flow efficiency, lead-time, planning accuracy
- Gets throughput data per PI
- Enables historical comparison

## Best Practices

### For Coaches/Admins
1. **Timing**: Generate reports at PI end for retrospectives
2. **Comparison**: Always compare with previous PI for trends
3. **Targets**: Keep strategic targets updated
4. **Context**: Add relevant documents to RAG for better insights

### For Leadership
1. **Focus**: Start with Executive Summary
2. **Trends**: Review "Improvements from Previous PI" section
3. **Action**: Prioritize short-term proposals first
4. **Follow-up**: Track success criteria from previous PI reports

### For Teams
1. **Transparency**: Share reports for team awareness
2. **Ownership**: Identify specific actions for your team
3. **Metrics**: Understand how your work impacts PI metrics
4. **Improvement**: Use proposals for sprint planning

## Future Enhancements

### Planned
- [ ] Multi-PI trend charts (3-4 PIs)
- [ ] ART-specific PI reports
- [ ] Automated email distribution
- [ ] Report scheduling (auto-generate at PI end)
- [ ] Custom report templates
- [ ] Executive dashboard integration

### Possible
- [ ] Predictive analytics (forecasting next PI)
- [ ] Benchmark comparison (industry standards)
- [ ] What-if scenario modeling
- [ ] Integration with strategic planning tools
- [ ] Video summary generation
- [ ] Natural language Q&A about reports

## Troubleshooting

### Report Generation Fails
- **Check**: Backend logs for detailed error
- **Verify**: LLM service is configured and API key is valid
- **Confirm**: Lead-time service is available (port 8000)
- **Review**: Selected PI has data in database

### Metrics Show N/A
- **Cause**: No data for selected PI
- **Solution**: Verify PI naming matches data (e.g., "25Q4")
- **Check**: Lead-time service has synchronized data

### Previous PI Comparison Missing
- **Cause**: Previous PI has no data
- **Solution**: Uncheck "Compare with previous PI"
- **Note**: Reports are still valuable without comparison

### Slow Generation
- **Expected**: LLM calls take 10-30 seconds
- **Optimize**: Use gpt-4o-mini for faster results
- **Monitor**: Check backend logs for bottlenecks

## Technical Notes

### Performance
- Report generation: ~15-30 seconds (LLM dependent)
- Data fetching: ~2-5 seconds (from lead-time service)
- Typical report size: 3000-6000 tokens

### Dependencies
- LLM Service (OpenAI API)
- Lead-Time Service (DL Webb App on port 8000)
- Strategic Targets database
- RAG Service (optional, enhances quality)

### Security
- Reports contain sensitive business metrics
- Access controlled by authentication (when implemented)
- Recommend confidential marking on printed reports

## Support

For issues or questions:
1. Check backend logs: `backend.log`
2. Review browser console for frontend errors
3. Verify all services are running
4. Consult `DEVELOPMENT_ROADMAP.md` for known issues

---

**Version**: 1.0  
**Last Updated**: January 7, 2026  
**Author**: Evaluation Coach Development Team
