# Visual Guide: Finding Strategic Target Insights in the UI

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🎯 Evaluation Coach                                                 │
│ AI-powered Agile & SAFe Analytics Platform                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐                                               │
│  │  📊 Dashboard   │  💬 Chat   💡 Insights   ⚙️ Admin            │
│  └─────────────────┘                 ▲                              │
│                                      │                              │
│                            CLICK HERE TO VIEW INSIGHTS              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Step 1: Click the "💡 Insights" Tab

```
┌─────────────────────────────────────────────────────────────────────┐
│  📊 Dashboard    💬 Chat    [💡 Insights] ✓   ⚙️ Admin            │
└─────────────────────────────────────────────────────────────────────┘
```

## Step 2: Click "🚀 Generate AI Insights" Button

```
┌─────────────────────────────────────────────────────────────────────┐
│ 💡 Insights Tab                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Insight Filters                                                    │
│  Severity: All | Confidence: High | Scope: Portfolio               │
│                                                                     │
│  ┌───────────────────────────────────────────────┐                │
│  │  🚀 Generate AI Insights                      │  ← CLICK THIS  │
│  └───────────────────────────────────────────────┘                │
│                                                                     │
│  ⚠️ This may take a while as the AI analyzes your data            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Step 3: Wait for AI Analysis

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    🤔 AI Coach analyzing your data...               │
│                                                                     │
│                           [  Loading...  ]                          │
│                                                                     │
│               🧠 Expert analysis in progress with                   │
│                      claude-3-5-sonnet-20241022                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Step 4: Strategic Target Insights Appear!

```
┌─────────────────────────────────────────────────────────────────────┐
│ 💡 Actionable Insights                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 📊 Feature Lead-Time vs Strategic Targets          ⚠️ Warning   │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ Confidence: 95%                                                 │ │
│ │                                                                 │ │
│ │ 📊 Observation                                                  │ │
│ │ Current Feature lead-time is 47.0 days.                        │ │
│ │ • 2026 target: 35.0 days (gap: +12.0 days) ← YOUR TARGETS     │ │
│ │ • 2027 target: 25.0 days (gap: +22.0 days)                     │ │
│ │ • True North: 15.0 days (gap: +32.0 days)                      │ │
│ │                                                                 │ │
│ │ 💡 Interpretation                                               │ │
│ │ Need to reduce lead-time by 12.0 days (25.5%) to meet 2026    │ │
│ │ target. 2027 target requires additional reduction...           │ │
│ │                                                                 │ │
│ │ [Show Details ▼]  [Dismiss]  [Provide Feedback]               │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 📊 Planning Accuracy vs Strategic Targets          ℹ️ Info      │ │
│ ├─────────────────────────────────────────────────────────────────┤ │
│ │ Confidence: 95%                                                 │ │
│ │                                                                 │ │
│ │ 📊 Observation                                                  │ │
│ │ Current Planning Accuracy is 72.0%.                            │ │
│ │ • 2026 target: 80.0% (gap: +8.0%) ← YOUR TARGETS              │ │
│ │ • 2027 target: 85.0% (gap: +13.0%)                            │ │
│ │ • True North: 90.0% (gap: +18.0%)                             │ │
│ │                                                                 │ │
│ │ 💡 Interpretation                                               │ │
│ │ Need to improve accuracy by 8.0 percentage points to meet      │ │
│ │ 2026 target...                                                 │ │
│ │                                                                 │ │
│ │ [Show Details ▼]  [Dismiss]  [Provide Feedback]               │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ... (other operational insights may appear below) ...              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Insight Card Details

When you click **[Show Details ▼]**, you'll see:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📊 Feature Lead-Time vs Strategic Targets          ⚠️ Warning       │
├─────────────────────────────────────────────────────────────────────┤
│ Confidence: 95%                                                     │
│                                                                     │
│ 📊 Observation                                                      │
│ Current Feature lead-time is 47.0 days.                            │
│ • 2026 target: 35.0 days (gap: +12.0 days)                         │
│ • 2027 target: 25.0 days (gap: +22.0 days)                         │
│ • True North: 15.0 days (gap: +32.0 days)                          │
│                                                                     │
│ 💡 Interpretation                                                   │
│ Need to reduce lead-time by 12.0 days (25.5%) to meet 2026 target. │
│ 2027 target requires additional 22.0 days reduction. True North    │
│ vision requires 68.1% total reduction.                             │
│                                                                     │
│ 🔍 Root Causes                                                      │
│ • Baseline measurement for strategic goal tracking                 │
│   Confidence: 95% | Evidence: current_metrics                      │
│                                                                     │
│ 🎯 Recommended Actions                                              │
│ SHORT-TERM:                                                         │
│ • Analyze bottlenecks in current flow to identify improvement      │
│   opportunities                                                     │
│   Owner: Process Improvement Team | Effort: Medium                 │
│   Success Signal: Identified top 3 bottlenecks affecting lead-time │
│                                                                     │
│ MEDIUM-TERM:                                                        │
│ • Implement incremental improvements targeting 2026 goals          │
│   Owner: ART Leadership | Effort: High                             │
│   Success Signal: Lead-time reduced to 35.0 days by end of 2026   │
│                                                                     │
│ 📈 Expected Outcomes                                                │
│ Metrics to Watch: Feature lead-time, Flow efficiency, Cycle time   │
│ Leading Indicators: Bottleneck reduction, WIP limits adherence     │
│ Lagging Indicators: Average lead-time trend                        │
│ Timeline: 12-24 months for 2026 target                            │
│ Risks: Organizational resistance, Resource constraints             │
│                                                                     │
│ [Show Less ▲]  [Dismiss]  [Provide Feedback]                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Severity Indicators

Strategic target insights use color-coded severity:

```
🔴 CRITICAL (Red border)
   Gap > 15 days or 15% from 2026 target
   Example: Current 50 days, Target 35 days (gap: 15+ days)

🟡 WARNING (Orange border)
   Gap 5-15 days or 5-15% from 2026 target
   Example: Current 42 days, Target 35 days (gap: 7 days)

🔵 INFO (Blue border)
   Gap 0-5 days or 0-5% from 2026 target
   Example: Current 37 days, Target 35 days (gap: 2 days)

🟢 SUCCESS (Green border)
   At or ahead of 2026 target
   Example: Current 33 days, Target 35 days (ahead by 2 days)
```

## Navigation Map

Here's the complete navigation path:

```
1. Start at Dashboard
   http://localhost:8800
   
2. Click "💡 Insights" tab (top navigation)
   ↓
   
3. View Insights page
   Shows: Insight filters + Generate button
   ↓
   
4. Click "🚀 Generate AI Insights"
   ↓
   
5. Wait for analysis (10-30 seconds)
   Shows: Loading overlay with progress messages
   ↓
   
6. View Generated Insights
   Shows: Strategic target insights + operational insights
   ↓
   
7. Click "Show Details" on any insight
   Shows: Full insight with all 5 components
```

## What If I Don't See Strategic Insights?

### Checklist

```
☐ Have you configured targets in Admin panel?
  └─ Go to: http://localhost:8800/admin.html
     Scroll to: 📊 Strategic Targets section
     Set: At least one 2026 target value
     Click: 💾 Save Configuration

☐ Have you generated insights?
  └─ Go to: http://localhost:8800
     Click: 💡 Insights tab
     Click: 🚀 Generate AI Insights button

☐ Is the backend running?
  └─ Check: Backend should be at http://localhost:8850
     Verify: http://localhost:8850/docs should load
     Restart: Run ./start.sh if needed

☐ Did you wait for generation to complete?
  └─ Wait: 10-30 seconds for AI analysis
     Check: Loading overlay should disappear
     Look: Insights should appear in the list
```

## Mobile/Responsive View

On smaller screens, the layout adapts:

```
┌────────────────────────┐
│ 🎯 Evaluation Coach    │
├────────────────────────┤
│ [≡ Menu]               │
├────────────────────────┤
│ 💡 Insights            │
├────────────────────────┤
│ [🚀 Generate Insights] │
├────────────────────────┤
│ ┌────────────────────┐ │
│ │ 📊 Feature Lead-   │ │
│ │ Time vs Targets    │ │
│ │                    │ │
│ │ ⚠️ Warning         │ │
│ │                    │ │
│ │ Current: 47 days   │ │
│ │ 2026: 35d (+12d)   │ │
│ │ 2027: 25d (+22d)   │ │
│ │ North: 15d (+32d)  │ │
│ │                    │ │
│ │ [Show Details]     │ │
│ └────────────────────┘ │
└────────────────────────┘
```

## Quick Reference

| Element | Location | What to Look For |
|---------|----------|------------------|
| Admin Panel | `admin.html` | 📊 Strategic Targets section with 6 input fields |
| Insights Tab | Top navigation | 💡 Insights button |
| Generate Button | Insights page | 🚀 Generate AI Insights (center of page) |
| Strategic Insights | Insights list | Title contains "vs Strategic Targets" |
| Target Values | Insight observation | Lines showing 2026, 2027, True North with gaps |
| Gap Analysis | Insight interpretation | % reduction needed statements |

---

**Pro Tip**: Bookmark the Insights page for quick access:
- Insights: `http://localhost:8800#insights`
- Admin: `http://localhost:8800/admin.html`

**Need Help?** Check [WHERE_ARE_STRATEGIC_INSIGHTS.md](WHERE_ARE_STRATEGIC_INSIGHTS.md) for troubleshooting.
