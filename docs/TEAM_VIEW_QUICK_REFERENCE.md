# Team View Quick Reference

## How to Use Team View with ART Filtering and Level Selection

### Step-by-Step Guide

1. **Select Team View**
   - Click the **"👥 Team View"** button in the sidebar

2. **Select an ART (Optional but Recommended)**
   - Use the **"Select ART"** dropdown
   - This filters the team list to show only teams in that ART
   - Makes it easier to find your team

3. **Select a Team**
   - Use the **"Select Team"** dropdown
   - Shows teams filtered by the selected ART (or all teams if no ART selected)

4. **Choose Analysis Level**
   - **Feature Level**: Analyzes Features (epic-level work items)
   - **Story Level**: Analyzes User Stories (story-level work items)

5. **View Results**
   - Dashboard shows metrics for the selected team at the chosen level
   - Context banner shows: ART | Team | Level

### When to Use Each Level

#### Use Feature Level When:
- ✅ Analyzing larger work items (Epics/Features)
- ✅ Looking at cross-team coordination
- ✅ Measuring epic-to-production flow
- ✅ Comparing with portfolio-level metrics

#### Use Story Level When:
- ✅ Analyzing team-level work items (User Stories)
- ✅ Looking at sprint-level flow
- ✅ Measuring story-to-production flow
- ✅ Understanding team velocity and efficiency

### Process Stages by Level

#### Feature Level Process
```
Backlog → Planned → Analysis → Development → Review → 
SIT → UAT → Ready for Deployment → Deployed
```

#### Story Level Process
```
Refinement → Ready for Dev → Development → Review → 
Ready for Test → Testing → Ready for Deployment → Deployed
```

### Key Metrics Shown

Both levels show:
- **Flow Efficiency**: Value-add time / Total time
- **Average Lead Time**: Total time from start to completion
- **Throughput**: Number of items completed
- **Planning Accuracy**: Commitment vs. delivery (when available)

### Tips

- 💡 **Tip 1**: Select an ART first to narrow down the team list
- 💡 **Tip 2**: Switch between levels to see different perspectives
- 💡 **Tip 3**: Compare Feature vs Story metrics to understand work breakdown
- 💡 **Tip 4**: Use PI filters to focus on specific time periods

### Example Use Cases

**Use Case 1: Team Flow Efficiency Analysis**
```
1. Select Team View
2. Choose ART: "Enabling Platform ART"
3. Choose Team: "API Developer Journey"
4. Select Level: "Story Level"
5. Review flow efficiency and bottlenecks
```

**Use Case 2: Feature Delivery Analysis**
```
1. Select Team View
2. Choose ART: "Customer Experience ART"
3. Choose Team: "CCS:Comms & Sharing Service"
4. Select Level: "Feature Level"
5. Analyze epic delivery performance
```

**Use Case 3: Multi-ART Team Comparison**
```
1. View different teams across ARTs
2. Compare Story-level metrics
3. Identify best practices
4. Share learnings across teams
```

### Context Display

The context banner shows your current selection:
```
Team | ART: Enabling Platform ART | Team: API Developer Journey | Level: Story
```

### Troubleshooting

**Q: Team dropdown is empty**
- A: Select an ART first, or check if teams data is loaded

**Q: No data showing for selected team**
- A: Team may not have data for selected PIs, try different PI selection

**Q: Which level should I use?**
- A: Use Feature level for strategic view, Story level for operational view

**Q: Can I analyze multiple teams at once?**
- A: Not yet - currently supports single team analysis only

### Related Views

- **Portfolio View**: Analyze all ARTs together
- **ART View**: Analyze a specific ART
- **Metrics Catalog**: Detailed metrics for all items
