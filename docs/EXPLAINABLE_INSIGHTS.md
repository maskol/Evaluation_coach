# Explainable Insight Template System

**Purpose**: Ensure every coaching output is transparent, evidence-based, and actionable.

**Core Principle**: The user must understand:
1. **What** was observed (data)
2. **Why** it matters (interpretation)
3. **What** to do about it (action)
4. **How** to know it's working (metrics)

This is the differentiator of the Evaluation Coach.

---

## 1. Insight Template Structure

Every insight MUST follow this five-part structure:

```
1. Metric Observation
2. Interpretation
3. Likely Root Causes
4. Recommended Actions
5. Expected Outcome
```

---

## 2. Detailed Template

### 2.1 Full Template

```markdown
## Insight: [Clear, Non-Blame Title]

### 1. Metric Observation
**What was measured**: [Specific metric name]
**Value**: [Actual value with units]
**Comparison**: [Benchmark/previous period/target]
**Time Period**: [Date range]
**Data Source**: [Jira JQL or specific issues]
**Confidence**: [High/Medium/Low - based on data quality]

**Raw Data**:
- [Specific data points]
- [Issue keys if relevant]
- [Trend visualization reference]

---

### 2. Interpretation
**What this indicates**: [Systemic issue, not blame]
**Why this matters**: [Business/team impact]
**Contextual factors**: [What else might be contributing]

**Impact Assessment**:
- **Severity**: [Low/Medium/High/Critical]
- **Urgency**: [How quickly must this be addressed]
- **Scope**: [Team/ART/Portfolio]

---

### 3. Likely Root Causes
**Based on**: [Pattern analysis + RAG knowledge]

1. **[Root Cause 1]**
   - Evidence: [Specific data supporting this]
   - Confidence: [High/Medium/Low]
   - References: [Knowledge base documents]

2. **[Root Cause 2]**
   - Evidence: [...]
   - Confidence: [...]

**Assumptions**:
- [Explicit assumptions made]
- [What we don't know but inferred]

---

### 4. Recommended Actions

#### Short-Term (Next Sprint/Iteration)
**Goal**: [Quick wins, immediate relief]

1. **[Action 1]**
   - **What**: [Specific action]
   - **Who**: [Role/team responsible]
   - **Effort**: [Hours/days]
   - **Dependencies**: [What's needed]
   - **Success Signal**: [How you'll know it worked]

2. **[Action 2]**
   - ...

#### Medium-Term (Next PI/Quarter)
**Goal**: [Structural improvements]

1. **[Action 1]**
   - **What**: [...]
   - **Who**: [...]
   - **Effort**: [Weeks]
   - **Dependencies**: [...]
   - **Success Signal**: [...]

#### Long-Term (Systemic)
**Goal**: [Organizational/cultural change]

1. **[Action 1]**
   - **What**: [...]
   - **Governance**: [How to sustain]

---

### 5. Expected Outcome

**Metrics to Watch**:
- [Metric 1]: Expected to [increase/decrease] by [amount] within [timeframe]
- [Metric 2]: Expected to [...]

**Leading Indicators** (Early signals):
- [What you'll see first]

**Lagging Indicators** (Confirming success):
- [What confirms sustained improvement]

**Timeline**: [Realistic timeframe for improvement]

**Risks**:
- [What could prevent improvement]
- [Mitigation strategies]

---

### Supporting Evidence
- [Link to Jira query]
- [Link to knowledge base article]
- [Reference to case study]
```

---

## 3. Example: Complete Insight

### Example 1: Team-Level High WIP

```markdown
## Insight: Excessive Work-in-Progress Reducing Throughput

### 1. Metric Observation
**What was measured**: Work-in-Progress (WIP) per team member
**Value**: 3.2 items per person (average over last 3 sprints)
**Comparison**: Target is ≤ 1.5 items per person (industry best practice)
**Time Period**: December 1-31, 2025
**Data Source**: Jira query: `project = PLATFORM AND status in ("In Progress", "In Review", "In Testing") AND sprint in openSprints()`
**Confidence**: High (100% of team members tracked)

**Raw Data**:
- Sprint 24: WIP = 3.4 per person
- Sprint 25: WIP = 3.1 per person
- Sprint 26: WIP = 3.1 per person
- Peak WIP: Alice had 5 concurrent items in Sprint 24
- Related metrics:
  - Cycle time increased from 6 days → 9 days
  - Throughput decreased from 18 items/sprint → 14 items/sprint

---

### 2. Interpretation
**What this indicates**: The team is taking on more work than they can effectively handle, leading to context switching and reduced delivery speed.

**Why this matters**: 
- **Productivity**: Higher WIP paradoxically reduces throughput (Little's Law)
- **Quality**: Increased context switching correlates with higher defect rates
- **Morale**: Team members report feeling overwhelmed
- **Predictability**: Makes sprint commitments unreliable

**Contextual factors**:
- Multiple high-priority requests from stakeholders
- No explicit WIP limits in place
- Daily standup focuses on "what's starting" vs "what's finishing"

**Impact Assessment**:
- **Severity**: High - affecting throughput and quality
- **Urgency**: Medium - sustainable but trending worse
- **Scope**: Team-level (Platform Team Alpha)

---

### 3. Likely Root Causes
**Based on**: WIP pattern analysis + flow theory principles

1. **Over-commitment / Inability to say "no"**
   - Evidence: 30% scope additions mid-sprint (last 3 sprints)
   - Confidence: High
   - References: [High WIP Anti-Pattern](knowledge/coaching_patterns/high_wip.md)

2. **Lack of WIP Limits**
   - Evidence: No documented working agreement on WIP limits
   - Confidence: High
   - References: [Kanban Principles](knowledge/agile_principles/kanban_principles.md)

3. **Unclear Prioritization**
   - Evidence: 80% of items marked "High Priority" in backlog
   - Confidence: Medium
   - References: [Priority Inflation](knowledge/coaching_patterns/priority_inflation.md)

4. **Interruptions and Unplanned Work**
   - Evidence: 20% of completed work was unplanned (added mid-sprint)
   - Confidence: Medium

**Assumptions**:
- Team has sufficient skill to complete work (not a capability issue)
- Work items are appropriately sized (mostly 3-5 point stories)
- We assume interruptions are coming from outside the team (not internally created)

---

### 4. Recommended Actions

#### Short-Term (Next Sprint - Sprint 27)
**Goal**: Make WIP visible and start behavioral change

1. **Visualize Current WIP**
   - **What**: Create physical/digital board showing all in-progress work with owners
   - **Who**: Scrum Master + Team
   - **Effort**: 1 hour (sprint planning)
   - **Dependencies**: None
   - **Success Signal**: Team can see at a glance who's working on what

2. **Introduce "Finish, Don't Start" Mantra**
   - **What**: Change daily standup focus to "What can we finish today?"
   - **Who**: Scrum Master facilitates, team adopts
   - **Effort**: 0 (change of facilitation)
   - **Dependencies**: None
   - **Success Signal**: Daily standups result in 2-3 items moving to Done

3. **Soft WIP Limit of 2 per Person**
   - **What**: Team agrees to TRY limiting parallel work to 2 items max
   - **Who**: Entire team commits
   - **Effort**: 0 (behavioral)
   - **Dependencies**: Product Owner support
   - **Success Signal**: WIP drops below 2.5 by end of sprint

#### Medium-Term (Next PI - Q1 2026)
**Goal**: Formalize WIP discipline and protect capacity

1. **Formalize WIP Limits in Working Agreement**
   - **What**: Document WIP limit of 1-2 per person in team's working agreement
   - **Who**: Team retrospective decision
   - **Effort**: 1 hour (retro discussion)
   - **Dependencies**: Product Owner buy-in
   - **Success Signal**: Written working agreement updated and visible

2. **Implement Pull System**
   - **What**: Team members pull new work only when capacity opens (not pushed)
   - **Who**: Scrum Master coaches, team adopts
   - **Effort**: 2-3 sprints to build habit
   - **Dependencies**: Backlog must be prioritized
   - **Success Signal**: Zero items "pushed" onto team mid-sprint

3. **Stakeholder Education**
   - **What**: Product Owner presents WIP impact to stakeholders with data
   - **Who**: Product Owner + Scrum Master
   - **Effort**: 1 hour presentation + Q&A
   - **Dependencies**: Stakeholder meeting scheduled
   - **Success Signal**: 50% reduction in mid-sprint interruptions

#### Long-Term (Systemic)
**Goal**: Organizational respect for flow

1. **Capacity-Based Planning Across ART**
   - **What**: All teams adopt throughput-based planning (not velocity/points)
   - **Who**: RTE + Product Management
   - **Governance**: PI Planning includes capacity discussion
   - **Success Signal**: 80%+ PI predictability across ART

---

### 5. Expected Outcome

**Metrics to Watch**:
- **WIP per person**: Expected to decrease from 3.2 → 1.5 within 2 sprints
- **Cycle time**: Expected to decrease from 9 days → 6 days within 3 sprints
- **Throughput**: Expected to increase from 14 items/sprint → 18 items/sprint within 3 sprints
- **Sprint commitment reliability**: Expected to increase from 65% → 80% within PI

**Leading Indicators** (Early signals - within 1-2 sprints):
- More items moving to "Done" each day
- Fewer items in "In Progress" column
- Team members verbally noting less context switching

**Lagging Indicators** (Confirming success - within 3-6 sprints):
- Sustained lower WIP
- Improved cycle time percentiles (P85, P95)
- Higher team satisfaction scores
- Fewer defects escaping to production

**Timeline**: 
- Immediate improvement expected within 1 sprint (WIP reduction)
- Full impact realized within 3-4 sprints (throughput increase)
- Sustained change confirmed after 6 sprints

**Risks**:
- **Risk**: Stakeholders push back on limiting WIP
  - **Mitigation**: Show data on throughput improvement after 2 sprints
- **Risk**: Team reverts to old habits
  - **Mitigation**: Daily WIP visualization, Scrum Master coaching
- **Risk**: Product Owner continues accepting mid-sprint scope additions
  - **Mitigation**: Weekly check-in with PO on sprint protection

---

### Supporting Evidence
- **Jira Query**: [View issues](https://jira.example.com/issues/?jql=project%3DPLATFORM%20AND%20sprint%20in%20openSprints())
- **Knowledge Base**: [High WIP Anti-Pattern](../knowledge/coaching_patterns/high_wip.md)
- **Playbook**: [Reduce WIP](../knowledge/improvement_playbooks/reduce_wip.md)
- **Theory**: [Little's Law](../knowledge/agile_principles/little_law.md)
- **Case Study**: [Team Bravo WIP Reduction Success](../knowledge/case_studies/team_wip_reduction.md)
```

---

## 4. Implementation in Code

### 4.1 Data Model

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MetricObservation(BaseModel):
    """Raw metric observation."""
    metric_name: str
    value: float
    unit: str
    comparison_target: Optional[float] = None
    time_period_start: datetime
    time_period_end: datetime
    data_source: str  # JQL query
    confidence: str = Field(..., pattern="^(High|Medium|Low)$")
    raw_data: dict  # Additional context
    trend: Optional[str] = None  # "increasing", "decreasing", "stable"

class Interpretation(BaseModel):
    """What the observation means."""
    what_this_indicates: str
    why_this_matters: str
    contextual_factors: List[str]
    severity: str = Field(..., pattern="^(Low|Medium|High|Critical)$")
    urgency: str = Field(..., pattern="^(Low|Medium|High|Immediate)$")
    scope: str = Field(..., pattern="^(Team|ART|Portfolio)$")

class RootCause(BaseModel):
    """Likely root cause with evidence."""
    cause: str
    evidence: str
    confidence: str = Field(..., pattern="^(High|Medium|Low)$")
    references: List[str] = Field(default_factory=list)  # Knowledge base links

class ActionableStep(BaseModel):
    """Specific action to take."""
    what: str
    who: str
    effort: str  # "1 hour", "2 days", "1 sprint"
    dependencies: List[str] = Field(default_factory=list)
    success_signal: str

class RecommendedActions(BaseModel):
    """Short/medium/long term actions."""
    short_term: List[ActionableStep]  # Next sprint
    medium_term: List[ActionableStep]  # Next PI
    long_term: List[ActionableStep]  # Systemic

class ExpectedOutcome(BaseModel):
    """What should improve."""
    metrics_to_watch: List[dict]  # [{metric, expected_change, timeframe}]
    leading_indicators: List[str]
    lagging_indicators: List[str]
    timeline: str
    risks: List[dict]  # [{risk, mitigation}]

class ExplainableInsight(BaseModel):
    """Complete explainable insight."""
    title: str
    metric_observation: MetricObservation
    interpretation: Interpretation
    likely_root_causes: List[RootCause]
    recommended_actions: RecommendedActions
    expected_outcome: ExpectedOutcome
    supporting_evidence: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(ge=0.0, le=1.0)  # Overall confidence
```

### 4.2 Template Renderer

```python
def render_insight_markdown(insight: ExplainableInsight) -> str:
    """
    Render ExplainableInsight to markdown format.
    """
    md = f"""## Insight: {insight.title}

### 1. Metric Observation
**What was measured**: {insight.metric_observation.metric_name}
**Value**: {insight.metric_observation.value} {insight.metric_observation.unit}
"""
    
    if insight.metric_observation.comparison_target:
        md += f"**Comparison**: Target is {insight.metric_observation.comparison_target} {insight.metric_observation.unit}\n"
    
    md += f"""**Time Period**: {insight.metric_observation.time_period_start.date()} to {insight.metric_observation.time_period_end.date()}
**Data Source**: `{insight.metric_observation.data_source}`
**Confidence**: {insight.metric_observation.confidence}

---

### 2. Interpretation
**What this indicates**: {insight.interpretation.what_this_indicates}

**Why this matters**: {insight.interpretation.why_this_matters}

**Contextual factors**:
"""
    
    for factor in insight.interpretation.contextual_factors:
        md += f"- {factor}\n"
    
    md += f"""
**Impact Assessment**:
- **Severity**: {insight.interpretation.severity}
- **Urgency**: {insight.interpretation.urgency}
- **Scope**: {insight.interpretation.scope}

---

### 3. Likely Root Causes

"""
    
    for i, cause in enumerate(insight.likely_root_causes, 1):
        md += f"""{i}. **{cause.cause}**
   - Evidence: {cause.evidence}
   - Confidence: {cause.confidence}
"""
        if cause.references:
            md += f"   - References: {', '.join(f'[Link]({ref})' for ref in cause.references)}\n"
        md += "\n"
    
    md += """---

### 4. Recommended Actions

#### Short-Term (Next Sprint/Iteration)

"""
    
    for i, action in enumerate(insight.recommended_actions.short_term, 1):
        md += f"""{i}. **{action.what}**
   - **Who**: {action.who}
   - **Effort**: {action.effort}
   - **Dependencies**: {', '.join(action.dependencies) if action.dependencies else 'None'}
   - **Success Signal**: {action.success_signal}

"""
    
    # Similar for medium_term and long_term...
    
    md += """---

### 5. Expected Outcome

**Metrics to Watch**:
"""
    
    for metric in insight.expected_outcome.metrics_to_watch:
        md += f"- **{metric['metric']}**: {metric['expected_change']} within {metric['timeframe']}\n"
    
    md += f"""
**Timeline**: {insight.expected_outcome.timeline}

---

### Supporting Evidence
"""
    
    for evidence in insight.supporting_evidence:
        md += f"- {evidence}\n"
    
    return md
```

---

## 5. Quality Checklist for Insights

Every generated insight must pass this checklist:

- [ ] **Title is non-blame**: Describes the issue, not the team
- [ ] **Metric observation includes confidence level**: Transparent about data quality
- [ ] **Interpretation explains WHY it matters**: Not just what
- [ ] **Root causes backed by evidence**: Not speculation
- [ ] **Actions are specific and actionable**: Not vague ("improve quality")
- [ ] **Actions have owners**: Clear who is responsible
- [ ] **Expected outcomes are measurable**: Can verify improvement
- [ ] **Risks are identified**: Honest about what could go wrong
- [ ] **Supporting evidence linked**: Traceable to source

---

## 6. Insight Prioritization

When multiple insights are generated, prioritize by:

```python
priority_score = (
    severity_weight * severity_score +
    urgency_weight * urgency_score +
    confidence_weight * confidence_score +
    impact_weight * estimated_impact
)
```

Where:
- **Severity**: How bad is the issue? (Critical=4, High=3, Medium=2, Low=1)
- **Urgency**: How quickly must it be addressed? (Immediate=4, High=3, Medium=2, Low=1)
- **Confidence**: How sure are we? (High=3, Medium=2, Low=1)
- **Estimated Impact**: What's the improvement potential? (0-100 scale)

Default weights:
- Severity: 0.30
- Urgency: 0.25
- Confidence: 0.20
- Impact: 0.25

---

## References

- "Explainable AI: Interpreting, Explaining and Visualizing Deep Learning" - Samek et al.
- SAFe Lean-Agile Principles: #4 (Build incrementally with fast feedback)
- "The Goal" - Goldratt (TOC and visible constraints)
