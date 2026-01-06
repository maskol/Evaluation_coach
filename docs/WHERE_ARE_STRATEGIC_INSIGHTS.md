# Where to Find Strategic Target Insights

## Quick Answer

Strategic target insights appear in the **💡 Insights** tab of the main dashboard when:

1. ✅ **Targets are configured** in the Admin panel
2. ✅ **Insights are generated** by clicking "Generate AI Insights"

## Step-by-Step Guide

### Step 1: Configure Strategic Targets

1. Navigate to **Admin Configuration**: `http://localhost:8800/admin.html`
2. Scroll to the **📊 Strategic Targets** section
3. Enter your targets:
   - Feature Lead-Time Target 2026: e.g., `35` days
   - Feature Lead-Time Target 2027: e.g., `25` days
   - Feature Lead-Time True North: e.g., `15` days
   - Planning Accuracy Target 2026: e.g., `80` %
   - Planning Accuracy Target 2027: e.g., `85` %
   - Planning Accuracy True North: e.g., `90` %
4. Click **💾 Save Configuration**

### Step 2: Generate Insights

1. Return to **Dashboard**: `http://localhost:8800`
2. Click on the **💡 Insights** tab (top navigation)
3. Click the **🚀 Generate AI Insights** button
4. Wait for AI analysis to complete (this may take 10-30 seconds)

### Step 3: View Strategic Target Insights

The strategic target insights will appear with titles like:

- **📊 Feature Lead-Time vs Strategic Targets**
- **📊 Planning Accuracy vs Strategic Targets**

Each insight shows:
- 📊 **Observation**: Current value and all target comparisons
  - Current: X days/percent
  - 2026 target: Y (gap: ±Z)
  - 2027 target: Y (gap: ±Z)
  - True North: Y (gap: ±Z)
- 💡 **Interpretation**: What the gaps mean and % reduction needed
- 🔍 **Root Causes**: Why the gap exists
- 🎯 **Recommended Actions**: What to do (short/medium/long-term)
- 📈 **Expected Outcomes**: Metrics to watch and timeline

## What You Should See

### Example: Feature Lead-Time Insight

```
┌────────────────────────────────────────────────────────────┐
│ 📊 Feature Lead-Time vs Strategic Targets                  │
├────────────────────────────────────────────────────────────┤
│ Severity: ⚠️ Warning | Confidence: 95%                    │
│                                                            │
│ 📊 Observation                                             │
│ Current Feature lead-time is 47.0 days.                   │
│ • 2026 target: 35.0 days (gap: +12.0 days)                │
│ • 2027 target: 25.0 days (gap: +22.0 days)                │
│ • True North: 15.0 days (gap: +32.0 days)                 │
│                                                            │
│ 💡 Interpretation                                          │
│ Need to reduce lead-time by 12.0 days (25.5%) to meet     │
│ 2026 target. 2027 target requires additional 22.0 days    │
│ reduction. True North vision requires 68.1% total          │
│ reduction.                                                 │
│                                                            │
│ [Show Details] [Dismiss] [Feedback]                       │
└────────────────────────────────────────────────────────────┘
```

### Example: Planning Accuracy Insight

```
┌────────────────────────────────────────────────────────────┐
│ 📊 Planning Accuracy vs Strategic Targets                  │
├────────────────────────────────────────────────────────────┤
│ Severity: ℹ️ Info | Confidence: 95%                       │
│                                                            │
│ 📊 Observation                                             │
│ Current Planning Accuracy is 72.0%.                        │
│ • 2026 target: 80.0% (gap: +8.0%)                         │
│ • 2027 target: 85.0% (gap: +13.0%)                        │
│ • True North: 90.0% (gap: +18.0%)                         │
│                                                            │
│ 💡 Interpretation                                          │
│ Need to improve accuracy by 8.0 percentage points to      │
│ meet 2026 target.                                         │
│                                                            │
│ [Show Details] [Dismiss] [Feedback]                       │
└────────────────────────────────────────────────────────────┘
```

## How It Works Behind the Scenes

### Data Flow

```
1. User sets targets in Admin panel
   ↓
2. Targets saved to Settings (runtime config)
   ↓
3. User clicks "Generate AI Insights"
   ↓
4. Frontend calls: POST /api/v1/insights/generate
   ↓
5. Backend fetches real metrics from LeadTime service
   ↓
6. Backend calls InsightsService.generate_insights()
   ↓
7. InsightsService checks if targets are configured
   ↓
8. If targets exist, generates strategic target insights
   ↓
9. Compares current metrics vs targets (2026, 2027, True North)
   ↓
10. Calculates gaps and severity
   ↓
11. Returns insights to frontend
   ↓
12. Frontend displays in Insights tab
```

### Integration Points

**Backend Components:**

1. **Settings** (`backend/config/settings.py`)
   - Stores target values

2. **Insights Service** (`backend/services/insights_service.py`)
   - `_generate_strategic_target_insights()`: Creates target insights
   - Accepts `current_leadtime` and `current_planning_accuracy` parameters
   - Uses real metrics when available, fallback to examples if not

3. **Main API** (`backend/main.py`)
   - `/api/v1/insights/generate` endpoint
   - Fetches real metrics from LeadTime service
   - Passes current metrics to InsightsService
   - Merges strategic insights with operational insights

**Frontend Components:**

1. **Dashboard** (`frontend/index.html`)
   - Insights tab displays all insights
   - "Generate AI Insights" button triggers generation

2. **App Logic** (`frontend/app.js`)
   - `generateInsights()` function calls the API
   - Displays returned insights in the UI

## Troubleshooting

### ❌ Problem: Strategic target insights don't appear

**Possible Causes:**

1. **Targets not configured**
   - Solution: Go to Admin panel and set at least one 2026 target

2. **Insights not generated yet**
   - Solution: Click "Generate AI Insights" button in Insights tab

3. **Backend not running**
   - Solution: Run `./start.sh` to start the backend

4. **Old insights cached**
   - Solution: Click "Generate AI Insights" again to refresh

### ❌ Problem: Insight shows "47 days" (example data)

**Cause:** LeadTime service is not available or returning data

**Solution:**
- Check if LeadTime service is running at `http://localhost:3005`
- Verify connection in Admin panel under "Lead-Time Data Server"
- If service is unavailable, insights use example values (47 days, 72%)

### ❌ Problem: Only operational insights appear, no strategic ones

**Cause:** Strategic targets are not configured

**Solution:**
1. Open Admin page: `http://localhost:8800/admin.html`
2. Set at least one target value (2026 targets recommended)
3. Save configuration
4. Regenerate insights

## Testing

### Quick Test

Run this script to verify everything works:

```bash
python test_strategic_targets.py
```

Expected output:
```
✅ Configuration fetched successfully
✅ Thresholds updated successfully
✅ Generated X insights
📊 Found 2 strategic target insights:
  - Feature Lead-Time vs Strategic Targets
  - Planning Accuracy vs Strategic Targets
```

### Manual Test Checklist

- [ ] Admin page loads successfully
- [ ] Strategic Targets section is visible
- [ ] Can enter and save target values
- [ ] Success message appears after save
- [ ] Dashboard Insights tab is accessible
- [ ] "Generate AI Insights" button works
- [ ] Strategic target insights appear in results
- [ ] Insights show correct gap calculations
- [ ] All three targets (2026, 2027, True North) are displayed

## Current Metric Sources

### Feature Lead-Time
- **Source**: LeadTime service `/api/statistics` endpoint
- **Field**: `average_leadtime_days`
- **Fallback**: 47.0 days (example value)

### Planning Accuracy
- **Source**: LeadTime service `/api/planning-accuracy` endpoint
- **Field**: `predictability_score`
- **Fallback**: 72.0% (example value)

## What's Next?

Once you see the strategic target insights:

1. **Review the gaps** - Understand where you are vs targets
2. **Prioritize actions** - Focus on short-term wins first
3. **Track progress** - Regenerate insights monthly/quarterly
4. **Adjust targets** - Update based on actual improvement velocity
5. **Share insights** - Discuss with leadership and teams

## Related Documentation

- [STRATEGIC_TARGETS.md](STRATEGIC_TARGETS.md) - Complete feature documentation
- [STRATEGIC_TARGETS_IMPLEMENTATION.md](STRATEGIC_TARGETS_IMPLEMENTATION.md) - Technical details
- [STRATEGIC_TARGETS_UI_PREVIEW.md](STRATEGIC_TARGETS_UI_PREVIEW.md) - UI layout guide

---

**Last Updated**: January 2026
**Version**: 1.1 (with real metrics integration)
