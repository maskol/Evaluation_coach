# Strategic Targets - Admin UI Preview

## Visual Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚙️ Admin Configuration                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🎯 Bottleneck Analysis Thresholds                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ℹ️ About Thresholds                                        │ │
│  │ Thresholds determine when a feature is considered to be    │ │
│  │ "exceeding the acceptable time" in a workflow stage.       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Global Threshold (Days) *                                       │
│  ┌──────────────┐                                               │
│  │     7.0      │ days                                          │
│  └──────────────┘                                               │
│  Default threshold applied to all stages (unless overridden)    │
│                                                                  │
│  Planning Accuracy Threshold (%) *                              │
│  ┌──────────────┐                                               │
│  │     70       │ %                                             │
│  └──────────────┘                                               │
│  Minimum acceptable planning accuracy percentage                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 📊 Strategic Targets                              ⭐ NEW!  │ │
│  │────────────────────────────────────────────────────────────│ │
│  │ Define strategic targets for Feature Lead-Time and         │ │
│  │ Planning Accuracy. AI Insights will analyze current        │ │
│  │ performance against these targets.                         │ │
│  │                                                            │ │
│  │ 🎯 Feature Lead-Time Target 2026 (days)                   │ │
│  │ ┌──────────────┐                                          │ │
│  │ │     35       │ days                                     │ │
│  │ └──────────────┘                                          │ │
│  │ Target lead-time for 2026                                │ │
│  │                                                            │ │
│  │ 🎯 Feature Lead-Time Target 2027 (days)                   │ │
│  │ ┌──────────────┐                                          │ │
│  │ │     25       │ days                                     │ │
│  │ └──────────────┘                                          │ │
│  │ Target lead-time for 2027                                │ │
│  │                                                            │ │
│  │ ⭐ Feature Lead-Time True North (days)                    │ │
│  │ ┌──────────────┐                                          │ │
│  │ │     15       │ days                                     │ │
│  │ └──────────────┘                                          │ │
│  │ Long-term vision for lead-time                           │ │
│  │                                                            │ │
│  │ 🎯 Planning Accuracy Target 2026 (%)                      │ │
│  │ ┌──────────────┐                                          │ │
│  │ │     80       │ %                                        │ │
│  │ └──────────────┘                                          │ │
│  │ Target accuracy for 2026                                 │ │
│  │                                                            │ │
│  │ 🎯 Planning Accuracy Target 2027 (%)                      │ │
│  │ ┌──────────────┐                                          │ │
│  │ │     85       │ %                                        │ │
│  │ └──────────────┘                                          │ │
│  │ Target accuracy for 2027                                 │ │
│  │                                                            │ │
│  │ ⭐ Planning Accuracy True North (%)                       │ │
│  │ ┌──────────────┐                                          │ │
│  │ │     90       │ %                                        │ │
│  │ └──────────────┘                                          │ │
│  │ Long-term vision for accuracy                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Stage-Specific Overrides (Optional)                            │
│  Leave blank to use the global threshold for that stage         │
│                                                                  │
│  [Stage override fields...]                                     │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ 💾 Save Config   │  │ 🔄 Reset         │                   │
│  └──────────────────┘  └──────────────────┘                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Color Scheme

**Strategic Targets Section:**
- Background: Light gray (#f8f9fa)
- Border: 2px solid #e0e0e0
- Border-radius: 8px
- Padding: 20px

**Icons:**
- 🎯 = Near/Medium-term targets (2026, 2027)
- ⭐ = True North (long-term aspirational goal)
- 📊 = Strategic/Data-focused

## Grid Layout

The 6 target fields are displayed in a responsive grid:
- **Desktop:** 3 columns (3 fields per row)
- **Tablet:** 2 columns (2 fields per row)
- **Mobile:** 1 column (1 field per row)

## User Experience

### Input Fields
- **Type:** Number input with spinner controls
- **Validation:** Real-time (min/max/step enforcement)
- **Placeholders:** Empty (not required fields)
- **Help Text:** Descriptive label below each field

### Save Behavior
- **Action:** POST to `/api/admin/config/thresholds`
- **Feedback:** Success alert appears at top
- **Auto-hide:** Alert disappears after 5 seconds
- **No Reload:** Page stays in place (AJAX save)

### Visual Hierarchy
1. **Most Important:** Global thresholds (required, marked with *)
2. **Strategic:** Strategic targets (highlighted box, optional)
3. **Detailed:** Stage-specific overrides (optional, collapsed feel)

## Example with Values

```
Feature Lead-Time Targets:
┌─────────┬─────────┬──────────────┐
│ 2026    │ 2027    │ True North   │
├─────────┼─────────┼──────────────┤
│ 35 days │ 25 days │ 15 days      │
└─────────┴─────────┴──────────────┘

Planning Accuracy Targets:
┌─────────┬─────────┬──────────────┐
│ 2026    │ 2027    │ True North   │
├─────────┼─────────┼──────────────┤
│ 80%     │ 85%     │ 90%          │
└─────────┴─────────┴──────────────┘
```

## Insights Display (Dashboard)

After saving targets, insights will appear on the dashboard:

```
┌──────────────────────────────────────────────────────────────────┐
│ ⚠️  Feature Lead-Time vs Strategic Targets                      │
├──────────────────────────────────────────────────────────────────┤
│ Severity: Warning | Confidence: 95%                              │
│                                                                  │
│ 📊 Observation                                                   │
│ Current Feature lead-time is 47.0 days.                         │
│ • 2026 target: 35.0 days (gap: +12.0 days)                      │
│ • 2027 target: 25.0 days (gap: +22.0 days)                      │
│ • True North: 15.0 days (gap: +32.0 days)                       │
│                                                                  │
│ 💡 Interpretation                                                │
│ Need to reduce lead-time by 12.0 days (25.5%) to meet 2026      │
│ target. 2027 target requires additional reduction. True North   │
│ vision requires 68.1% total reduction.                          │
│                                                                  │
│ 🎯 Recommended Actions                                           │
│ • SHORT-TERM: Analyze bottlenecks in current flow              │
│ • MEDIUM-TERM: Implement incremental improvements              │
│                                                                  │
│ [View Details] [Dismiss] [Provide Feedback]                    │
└──────────────────────────────────────────────────────────────────┘
```

## Accessibility

- ✅ **Labels:** All fields have clear, descriptive labels
- ✅ **Required Fields:** Marked with asterisk (*)
- ✅ **Help Text:** Small gray text below each field
- ✅ **Keyboard Navigation:** Tab order follows visual layout
- ✅ **Error States:** Red border + error message on validation failure
- ✅ **Screen Reader:** Semantic HTML with proper ARIA labels

## Responsive Behavior

### Desktop (>1024px)
```
┌───────────┬───────────┬───────────┐
│ LT 2026   │ LT 2027   │ LT North  │
├───────────┼───────────┼───────────┤
│ PA 2026   │ PA 2027   │ PA North  │
└───────────┴───────────┴───────────┘
```

### Tablet (768-1024px)
```
┌───────────┬───────────┐
│ LT 2026   │ LT 2027   │
├───────────┼───────────┤
│ LT North  │ PA 2026   │
├───────────┼───────────┤
│ PA 2027   │ PA North  │
└───────────┴───────────┘
```

### Mobile (<768px)
```
┌─────────────┐
│ LT 2026     │
├─────────────┤
│ LT 2027     │
├─────────────┤
│ LT North    │
├─────────────┤
│ PA 2026     │
├─────────────┤
│ PA 2027     │
├─────────────┤
│ PA North    │
└─────────────┘
```

Legend:
- LT = Lead-Time
- PA = Planning Accuracy
- North = True North
