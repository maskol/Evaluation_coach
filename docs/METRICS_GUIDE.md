# Jira Analytics Metric Catalog

**Version**: 1.0  
**Last Updated**: 2026-01-02

This is the single source of truth for what the Evaluation Coach can measure and reason about from Jira Software.

---

## 1. Flow & Delivery Metrics (System-Level)

These metrics measure the flow of work through the system.

| Metric | Definition | Jira Data Used | Why It Matters | Implementation Status |
|--------|------------|----------------|----------------|----------------------|
| **Lead Time** | Time from Created → Done | `issue.created`, status transitions to "Done" | End-to-end delivery speed. Includes all wait time and work time. | ✅ Implemented |
| **Cycle Time** | Time from In Progress → Done | Status transitions from first "In Progress" to "Done" | Team execution efficiency. Pure working time. | ✅ Implemented |
| **Throughput** | Items completed per time period | Issues with `resolved_at` in time window | Delivery capacity and predictability. | ✅ Implemented |
| **WIP** | Items currently in progress | Issues where `status.category = "In Progress"` | Bottleneck indicator. High WIP = context switching. | ✅ Implemented |
| **Flow Efficiency** | Active time / Total time | All status transitions, calculate waiting vs active | Ratio of value-add time to total time. Lean metric. | 🔄 Partially implemented |
| **Blocked Time** | Time in blocked states | Status with "blocked" or custom flag field | Dependency & system friction indicator. | 🔄 Partially implemented |

### Implementation Details

**Lead Time Calculation**
```python
lead_time_hours = (issue.resolved_at - issue.created_at).total_seconds() / 3600
```

**Cycle Time Calculation**
```python
first_in_progress = min(t.transitioned_at for t in transitions if 'progress' in t.to_status.lower())
cycle_time_hours = (issue.resolved_at - first_in_progress).total_seconds() / 3600
```

**WIP Calculation**
```python
# Daily sampling approach
for each_day in time_window:
    wip_count = count(issues where created <= day AND (resolved is null OR resolved > day))
average_wip = mean(daily_wip_counts)
```

**Flow Efficiency Calculation**
```python
active_statuses = ["In Progress", "In Review", "Testing"]
waiting_statuses = ["To Do", "Backlog", "Blocked", "Waiting for Review"]

active_time = sum(time_in_status for status in active_statuses)
total_time = resolved_at - created_at
flow_efficiency = active_time / total_time
```

---

## 2. Predictability & Planning Metrics

These metrics measure how well teams/ARTs deliver what they commit to.

| Metric | Definition | Level | Jira Data Used | Implementation Status |
|--------|------------|-------|----------------|----------------------|
| **Planned vs Done** | Committed vs completed scope | Team / ART | Sprint: issues in sprint at start vs at end. PI: planned features vs delivered. | 🔜 Planned (Phase 2) |
| **Commitment Reliability** | % of committed items completed | Team / Sprint | `sprint.committed_issues` vs `sprint.completed_issues` | 🔜 Planned (Phase 2) |
| **PI Predictability** | % of PI objectives met | ART / PI | PI objectives (custom field) vs actual completion | 🔜 Planned (Phase 2) |
| **Scope Change Rate** | % of scope added/removed mid-execution | Sprint / PI | Issues added after sprint start / Issues removed | 🔜 Planned (Phase 2) |
| **Spillover Rate** | % of incomplete work carried over | Team / Sprint | Issues not completed → moved to next sprint | 🔜 Planned (Phase 2) |
| **Estimation Accuracy** | Planned effort vs actual | Team | `story_points` vs actual completion time or `time_spent` | 🔜 Planned (Phase 2) |

### Formulas

**Commitment Reliability**
```python
commitment_reliability = len(completed_committed) / len(committed_at_start)
# Target: ≥ 80% is healthy
```

**Scope Change Rate**
```python
scope_change_rate = (len(added_after_start) + len(removed)) / len(committed_at_start)
# Target: ≤ 10% is stable
```

**PI Predictability Score** (SAFe metric)
```python
pi_predictability = len(delivered_objectives) / len(planned_objectives)
# Target: ≥ 80% is predictable
```

---

## 3. Quality & Sustainability Metrics

These metrics measure the health and sustainability of delivery.

| Metric | Definition | Jira Data Used | Implementation Status |
|--------|------------|----------------|----------------------|
| **Defect Injection Rate** | Bugs created per features delivered | `issuetype = Bug` created during time window / Features completed | 🔜 Planned (Phase 2) |
| **Escaped Defects** | Bugs found after release | Bugs with `found_in_production` label or similar | 🔜 Planned (Phase 2) |
| **Rework Ratio** | Bugs / total items | Count(Bugs) / Count(All Issues) | 🔜 Planned (Phase 2) |
| **Team Load Index** | Parallel work per team member | WIP / team size | 🔜 Planned (Phase 2) |
| **Team Stability** | % membership change over time | Team roster changes (if tracked) | 🔜 Planned (Phase 2) |

### Formulas

**Defect Injection Rate**
```python
defect_injection_rate = bugs_created_in_period / features_completed_in_period
# Target: < 0.1 (1 bug per 10 features)
```

**Team Load Index**
```python
team_load_index = average_wip / team_size
# Target: ≤ 1.5 (each person working on 1-2 items)
```

---

## 4. Structural & Dependency Metrics

These metrics measure organizational friction and dependencies.

| Metric | Definition | Jira Data Used | Implementation Status |
|--------|------------|----------------|----------------------|
| **Cross-Team Dependencies** | Linked issues across teams | `issuelinks` where teams differ | 🔜 Planned (Phase 3) |
| **Blocker Density** | % of items blocked | Issues with `is_blocked = true` or blocked status | 🔜 Planned (Phase 3) |
| **Handovers** | Status category changes indicating handoffs | Transitions between statuses owned by different roles | 🔜 Planned (Phase 3) |
| **External Wait Time** | Time waiting on other ARTs/vendors | Time in "Waiting" statuses + blocked time | 🔜 Planned (Phase 3) |

### Formulas

**Cross-Team Dependency Count**
```python
cross_team_deps = count(issue.links where linked_issue.team != issue.team)
```

**Blocker Density**
```python
blocker_density = count(blocked_issues) / count(all_issues)
# Target: < 10%
```

---

## 5. Composite Metrics & Scores

These are calculated from multiple base metrics.

### Overall Health Score (0-100)

```python
health_score = weighted_average([
    (predictability_score, 0.30),
    (flow_efficiency, 0.25),
    (quality_score, 0.25),
    (team_stability, 0.20)
])
```

### Performance Category Mapping

| Score Range | Category | Interpretation |
|-------------|----------|----------------|
| 90-100 | Excellent | High-performing, sustainable |
| 75-89 | Good | Healthy with minor improvements needed |
| 60-74 | Average | Significant improvement opportunities |
| 40-59 | Below Average | Multiple systemic issues |
| 0-39 | Poor | Critical intervention needed |

---

## 6. Benchmark Values

Based on industry research and SAFe guidance.

| Metric | Industry Average | High Performer | World Class |
|--------|-----------------|----------------|-------------|
| Lead Time | 30-60 days | 7-14 days | < 7 days |
| Cycle Time | 10-20 days | 3-7 days | < 3 days |
| Flow Efficiency | 15-25% | 40-60% | > 60% |
| Commitment Reliability | 60-70% | 80-90% | > 90% |
| PI Predictability | 60-70% | 80-85% | > 85% |
| Defect Injection Rate | 0.2-0.3 | 0.05-0.1 | < 0.05 |
| WIP per Person | 3-5 | 1.5-2 | ≤ 1.5 |

**Sources**: 
- "Accelerate" (DORA metrics)
- "Actionable Agile Metrics" (Vacanti)
- SAFe 6.0 Big Picture
- Scaled Agile Framework guidance

---

## 7. Metric Implementation Priority

### Phase 1 (Weeks 3-4) ✅ PARTIALLY COMPLETE
- [x] Lead Time
- [x] Cycle Time  
- [x] Throughput
- [x] WIP
- [ ] Flow Efficiency (complete)
- [ ] Blocked Time (complete)

### Phase 2 (Weeks 5-6)
- [ ] Commitment Reliability
- [ ] Scope Change Rate
- [ ] Spillover Rate
- [ ] Velocity Trends
- [ ] Defect Injection Rate
- [ ] Team Load Index

### Phase 3 (Weeks 7-8)
- [ ] Cross-Team Dependencies
- [ ] Blocker Density
- [ ] External Wait Time
- [ ] PI Predictability
- [ ] Estimation Accuracy

---

## 8. Jira Field Mapping Reference

Common Jira fields used across metrics:

| Semantic Field | Standard Field | Custom Field (Example) | Notes |
|----------------|----------------|------------------------|-------|
| Story Points | - | `customfield_10016` | Varies by instance |
| Sprint | - | `customfield_10020` | Board-specific |
| Epic Link | - | `customfield_10014` | Standard for most |
| Team | - | `customfield_10030` | If exists |
| ART | - | `customfield_10031` | If exists |
| PI | - | `customfield_10032` | If exists |
| Created | `created` | - | ISO 8601 datetime |
| Resolved | `resolutiondate` | - | ISO 8601 datetime |
| Status | `status.name` | - | String |
| Status Category | `status.statusCategory.key` | - | `new`, `indeterminate`, `done` |
| Issue Links | `issuelinks` | - | Array of links |
| Blocked Flag | - | `customfield_10037` | Or use status |

**Configuration**: See [backend/config/settings.py](../backend/config/settings.py) for field mapping.

---

## 9. Data Quality Requirements

For reliable metrics, ensure:

| Requirement | Why | How to Check |
|-------------|-----|--------------|
| All issues have created date | Lead time calculation | `created IS NOT EMPTY` |
| Resolved issues have resolution date | Throughput accuracy | `status = Done AND resolutiondate IS NOT EMPTY` |
| Status transitions tracked | Cycle time, flow efficiency | Changelog history enabled |
| Story points on most stories | Velocity calculation | Count stories with `story_points IS NOT EMPTY` |
| Team field populated | Team-level analysis | Check custom field population |
| Sprint assignment | Sprint metrics | Issues assigned to sprints |

**Minimum Data Quality Score**: 0.7 (70% completeness) for reliable analysis

---

## 10. Metric Usage by Scope

### Portfolio Level
Primary: Lead Time, Epic Throughput, Strategic Predictability, Cross-ART Dependencies  
Secondary: Quality trends, Investment distribution

### ART Level  
Primary: PI Predictability, Feature Throughput, Flow Efficiency, Dependency Health  
Secondary: Team load balance, Quality trends

### Team Level
Primary: Sprint Reliability, Cycle Time, WIP, Throughput, Quality  
Secondary: Team stability, Blocked time

---

## References

- **Vacanti, D.** (2015). *Actionable Agile Metrics for Predictability*
- **Forsgren, N., et al.** (2018). *Accelerate: Building and Scaling High Performing Technology Organizations*
- **Scaled Agile, Inc.** (2023). *SAFe 6.0 Framework*
- **Reinertsen, D.** (2009). *The Principles of Product Development Flow*
- **Anderson, D.** (2010). *Kanban: Successful Evolutionary Change*
