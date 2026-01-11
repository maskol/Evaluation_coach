# Story-Level Insights - Quick Reference

**Last Updated**: January 11, 2026

---

## Quick Start

### Enable Story-Level Insights

1. Open Evaluation Coach dashboard
2. Select **Analysis Level**: "Story"
3. Select **Scope**: "Team"
4. Choose team, PI, and ART
5. View insights in AI Insights panel

### API Usage

```http
GET /api/coaching/insights?analysis_level=story&scope=team&team=Loke&pis=26Q1
```

---

## Story Workflow Stages (8 stages)

```
refinement → ready_for_development → in_development → in_review 
  → ready_for_test → in_testing → ready_for_deployment → deployed
```

**Key Stage**: `in_review` is unique to stories (code review)

---

## Insight Types Generated

### 1. 🚫 Bottleneck Detection
- Identifies slow stages
- Expected times: Development (5d), Testing (3d), Review (1d)
- Triggers: Mean time > 2x expected

### 2. ⏱️ Code Review Analysis (Story-Specific)
- Target: <1 day for reviews
- Monitors: PR wait times
- Recommends: Review rotation, size limits

### 3. 📊 WIP Management
- Healthy range: 5-12 stories
- Per stage: Dev(5), Review(3), Test(4)
- Focus: "Stop starting, start finishing"

### 4. 🚧 Stuck Stories
- Threshold: >10 days average
- Actions: Daily review, swarming
- Escalate: >3 days to management

### 5. ❌ Blocked Stories
- Threshold: >5 days average
- Track: Dependencies and blockers
- Implement: Dependency mapping

### 6. 📅 Planning Accuracy
- Target: 80-90% completion
- Metrics: Planned vs completed
- Focus: Right-sizing estimates

---

## Expected Timeframes

| Stage | Expected | Warning | Critical |
|-------|----------|---------|----------|
| Refinement | 2 days | >4 days | >6 days |
| Development | 5 days | >10 days | >15 days |
| Code Review | 1 day | >2 days | >3 days |
| Testing | 3 days | >6 days | >9 days |
| Overall | 15 days | >30 days | >45 days |

---

## Recommended WIP Limits

**For 5-8 person team**:
- Total: 5-12 stories
- Development: 5 max
- Review: 3 max
- Testing: 4 max

**Kanban principle**: Pull new work only when capacity available

---

## Key Metrics to Watch

### Leading Indicators
- Review turnaround time
- WIP count by stage
- Daily throughput
- Blocker resolution time

### Lagging Indicators
- Story lead time
- Sprint completion rate
- Velocity trend
- Defect escape rate

---

## Common Recommendations

### For High WIP
1. Implement WIP limits
2. Focus on finishing vs starting
3. Use pull system

### For Slow Reviews
1. 4-hour review SLA
2. Review rotation schedule
3. Limit PR size (<400 lines)
4. Use pair programming

### For Blocked Stories
1. Daily blocker review
2. Assign blocker owners
3. Escalate after 3 days
4. Dependency mapping in refinement

### For Stuck Stories
1. Swarming on stuck items
2. Root cause analysis
3. Daily standup focus
4. Visible blocker board

---

## Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| 🔴 Critical | Immediate action needed | Within 1 day |
| 🟡 Warning | Monitor and plan | Within 1 week |
| 🔵 Info | Awareness only | Note for planning |
| 🟢 Success | Positive trend | Continue practice |

---

## Best Practices

### Sprint Planning
- Use last 3 sprints velocity
- Plan to 80% capacity
- Right-size stories (3-5 days each)

### Daily Standup
- Focus on blockers first
- Review stuck stories daily
- Update WIP limits

### Refinement
- Clear acceptance criteria
- Identify dependencies
- Estimate collaboratively

### Code Review
- Review within 4 hours
- Limit PR size
- Use automation for standards

---

## Troubleshooting

### No Insights Shown
- **Check**: Story data exists in selected PI/Team
- **Verify**: DL Webb App is running
- **Confirm**: Analysis level = "Story"

### Wrong Insights (Feature-level)
- **Check**: Analysis Level dropdown
- **Ensure**: "Story" is selected
- **Refresh**: Page after changing

### Low Confidence Insights
- **Cause**: Limited data
- **Solution**: Expand PI range or include more teams

---

## Comparison with Features

| Aspect | Stories | Features |
|--------|---------|----------|
| Scope | Team/Sprint | Portfolio/ART |
| Duration | Days | Weeks-Months |
| Planning | Sprint | PI (12 weeks) |
| WIP Target | 5-12 | 10-20 |
| Threshold | 30 days | 60 days |
| Code Review | Yes | No |

---

## Testing

```bash
# Quick test
cd /Users/maskol/Local-Development/evaluation_coach/Evaluation_coach
source venv/bin/activate
python test_story_insights.py
```

---

## Need Help?

1. Check implementation docs: `docs/STORY_INSIGHTS_IMPLEMENTATION.md`
2. View API docs: `http://localhost:8001/docs`
3. Check logs for errors
4. Verify DL Webb App connectivity

---

**Quick Tip**: Start with team-level, single PI analysis for most actionable insights.
