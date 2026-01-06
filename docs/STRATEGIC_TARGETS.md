# Strategic Targets Feature

## Overview

The Strategic Targets feature allows you to define organizational goals for **Feature Lead-Time** and **Planning Accuracy** across multiple time horizons (2026, 2027, and True North). The AI Insights engine automatically analyzes current performance against these targets and provides actionable coaching recommendations.

## What Are Strategic Targets?

Strategic targets are quantifiable goals that help organizations:

- **Track progress** toward continuous improvement objectives
- **Align teams** around common improvement goals
- **Identify gaps** between current and desired performance
- **Prioritize improvements** based on strategic impact

### Target Time Horizons

1. **2026 Target**: Near-term goal (1-2 years out)
2. **2027 Target**: Medium-term goal (2-3 years out)
3. **True North**: Long-term aspirational goal representing world-class performance

## Feature Lead-Time Targets

**What is Feature Lead-Time?**
- Time from feature creation to deployment/completion
- Measured in days
- Key flow efficiency metric

**Example Targets:**
- Current: 47 days
- 2026 Target: 35 days
- 2027 Target: 25 days
- True North: 15 days

**Why It Matters:**
Shorter lead-times mean:
- Faster value delivery to customers
- Quicker feedback loops
- Better market responsiveness
- Reduced risk and cost

## Planning Accuracy Targets

**What is Planning Accuracy?**
- Percentage of planned work completed within a PI/Sprint
- Measured as %
- Key predictability metric

**Example Targets:**
- Current: 72%
- 2026 Target: 80%
- 2027 Target: 85%
- True North: 90%

**Why It Matters:**
Higher planning accuracy means:
- Better resource planning
- More reliable commitments
- Improved stakeholder trust
- Enhanced team morale

## How to Configure Strategic Targets

### Step 1: Access Admin Configuration

1. Navigate to the Admin page: `http://localhost:8800/admin.html`
2. Scroll to the **📊 Strategic Targets** section

### Step 2: Enter Target Values

**Feature Lead-Time Targets (in days):**
- Enter desired lead-time for 2026 (e.g., 35)
- Enter desired lead-time for 2027 (e.g., 25)
- Enter True North aspiration (e.g., 15)

**Planning Accuracy Targets (in %):**
- Enter desired accuracy for 2026 (e.g., 80)
- Enter desired accuracy for 2027 (e.g., 85)
- Enter True North aspiration (e.g., 90)

### Step 3: Save Configuration

Click **💾 Save Configuration** button

The targets are saved to runtime configuration and will be used immediately for AI Insights generation.

## How AI Insights Use Strategic Targets

When strategic targets are configured, the AI Insights engine automatically:

### 1. **Gap Analysis**
Compares current metrics against each target:
- Calculates the gap (e.g., "12 days above 2026 target")
- Determines gap percentage (e.g., "25% reduction needed")
- Assesses severity (critical/warning/info/success)

### 2. **Target-Specific Insights**
Generates dedicated insights for each metric:
- "Feature Lead-Time vs Strategic Targets"
- "Planning Accuracy vs Strategic Targets"

### 3. **Actionable Recommendations**
Provides coaching actions tailored to closing the gaps:
- Short-term actions (immediate fixes)
- Medium-term actions (structural improvements)
- Success signals for tracking progress

### 4. **Expected Outcomes**
Defines what to watch:
- Leading indicators (early signals)
- Lagging indicators (final results)
- Timeline expectations
- Risk factors

## Example Insight Output

```
Title: Feature Lead-Time vs Strategic Targets
Severity: Warning
Confidence: 95%

Observation:
Current Feature lead-time is 47.0 days. 2026 target: 35.0 days (gap: +12.0 days). 
2027 target: 25.0 days (gap: +22.0 days). True North: 15.0 days (gap: +32.0 days).

Interpretation:
Need to reduce lead-time by 12.0 days (25.5%) to meet 2026 target. 
2027 target requires additional 22.0 days reduction. 
True North vision requires 68.1% total reduction.

Recommended Actions:
- SHORT-TERM: Analyze bottlenecks in current flow to identify improvement opportunities
- MEDIUM-TERM: Implement incremental improvements targeting 2026 goals

Expected Outcomes:
- Watch: Feature lead-time, Flow efficiency, Cycle time
- Leading Indicators: Bottleneck reduction, WIP limits adherence
- Timeline: 12-24 months for 2026 target
```

## Integration Points

### Backend Components

1. **Settings** (`backend/config/settings.py`)
   - Stores target values as configuration parameters
   - Loads from environment variables or defaults

2. **API Models** (`backend/api_models.py`)
   - `ThresholdConfig`: Defines target fields with validation
   - `AdminConfigResponse`: Returns targets to frontend

3. **Insights Service** (`backend/services/insights_service.py`)
   - `_generate_strategic_target_insights()`: Analyzes metrics vs targets
   - Automatically runs when targets are configured

4. **Main API** (`backend/main.py`)
   - `/api/admin/config`: GET configuration including targets
   - `/api/admin/config/thresholds`: POST to update targets
   - `/api/insights`: Generates insights using targets

### Frontend Components

1. **Admin Page** (`frontend/admin.html`)
   - Form fields for all 6 target values
   - Visual styling to highlight strategic targets section
   - Load/save functionality

## Testing the Feature

### Automated Test

Run the test suite:

```bash
python test_strategic_targets.py
```

This tests:
- Configuration loading
- Target updates via API
- Insight generation with targets

### Manual Test

1. **Start the application:**
   ```bash
   ./start.sh
   ```

2. **Open Admin page:**
   Navigate to `http://localhost:8800/admin.html`

3. **Configure targets:**
   - Feature Lead-Time 2026: 35 days
   - Feature Lead-Time 2027: 25 days
   - Feature Lead-Time True North: 15 days
   - Planning Accuracy 2026: 80%
   - Planning Accuracy 2027: 85%
   - Planning Accuracy True North: 90%

4. **Save configuration**

5. **View insights:**
   - Return to dashboard (`http://localhost:8800`)
   - Navigate to Insights section
   - Look for "vs Strategic Targets" insights

## Best Practices

### Setting Realistic Targets

1. **Start with current baseline**: Understand current performance
2. **Research industry benchmarks**: Compare with similar organizations
3. **Set incremental goals**: 2026 → 2027 → True North progression
4. **Align with capacity**: Ensure targets are achievable with available resources

### Target Ranges

**Feature Lead-Time:**
- World-class: 7-15 days
- Good: 15-30 days
- Needs improvement: 30-60 days
- Critical: 60+ days

**Planning Accuracy:**
- World-class: 85-95%
- Good: 75-85%
- Needs improvement: 60-75%
- Critical: <60%

### Review Cadence

- **Quarterly**: Review progress toward 2026 targets
- **Annually**: Adjust targets based on actual improvement velocity
- **PI Planning**: Use targets to inform improvement initiatives

## Persistence Note

⚠️ **Important**: Target values are stored in runtime configuration only. For persistence across server restarts:

1. Add to `.env` file:
   ```
   LEADTIME_TARGET_2026=35.0
   LEADTIME_TARGET_2027=25.0
   LEADTIME_TARGET_TRUE_NORTH=15.0
   PLANNING_ACCURACY_TARGET_2026=80.0
   PLANNING_ACCURACY_TARGET_2027=85.0
   PLANNING_ACCURACY_TARGET_TRUE_NORTH=90.0
   ```

2. Or configure as environment variables in your deployment

## Future Enhancements

Potential improvements:

- [ ] Database persistence for targets
- [ ] Historical tracking of target changes
- [ ] Progress visualization against targets
- [ ] Target achievement notifications
- [ ] Multi-ART/team-specific targets
- [ ] Custom time horizons beyond 2026/2027
- [ ] Target recommendations based on benchmarks

## Troubleshooting

**Issue**: Targets not appearing in insights
- **Solution**: Ensure targets are saved via admin panel
- **Check**: GET `/api/admin/config` to verify targets are set

**Issue**: Insights not updating after target change
- **Solution**: Insights are generated on-demand; refresh dashboard or regenerate insights

**Issue**: Cannot save targets
- **Solution**: Check browser console for errors; verify backend is running

## Related Documentation

- [METRICS_GUIDE.md](METRICS_GUIDE.md) - Understanding flow metrics
- [EXPLAINABLE_INSIGHTS.md](EXPLAINABLE_INSIGHTS.md) - How insights are generated
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) - Future features

---

**Version**: 1.0
**Last Updated**: January 2026
