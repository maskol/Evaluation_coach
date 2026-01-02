# Quick Reference Guide

**Evaluation Coach - Essential Information at a Glance**

*Updated: 2 January 2026 - Phase 0 Complete with Full-Stack Implementation*

---

## 🎯 What Is This?

An AI-powered full-stack application that analyzes Jira data to provide **evidence-based coaching** at Team, ART, and Portfolio levels.

**Current Status**: ✅ **Fully Operational Web Application**
- FastAPI backend on port 8850
- Interactive web UI on port 8800  
- SQLite database with 8 tables
- 20+ REST API endpoints
- Demo mode ready for testing

**Core Differentiators**:
- Non-blame, system-focused coaching
- 5-part explainable insight template
- Metadata-driven RAG knowledge retrieval
- SAFe-aligned health scorecards
- 15+ metrics with industry benchmarks

---

## 🚀 Quick Start

```bash
# 1. Start Backend (Terminal 1)
./start_backend.sh

# 2. Start Frontend (Terminal 2)
cd frontend && python3 -m http.server 8800

# 3. Open Browser
open http://localhost:8800
```

**Test the API**:
```bash
curl http://localhost:8850/api/health
```

---

## 📊 Metrics at a Glance

### Flow & Delivery
| Metric | Formula | Target |
|--------|---------|--------|
| Lead Time | Created → Done | < 7 days (world class) |
| Cycle Time | In Progress → Done | < 3 days (world class) |
| WIP per Person | Active items / team size | ≤ 1.5 |
| Flow Efficiency | Active time / Total time | > 60% (world class) |
| Throughput | Items completed / time | Stable or increasing |

### Predictability
| Metric | Formula | Target |
|--------|---------|--------|
| Commitment Reliability | Completed / Committed | ≥ 80% |
| PI Predictability | Objectives met / Planned | ≥ 80% (SAFe) |
| Scope Change Rate | Added + Removed / Committed | < 10% |

### Quality
| Metric | Formula | Target |
|--------|---------|--------|
| Defect Injection Rate | Bugs / Features | < 0.05 (world class) |
| Rework Ratio | Bugs / Total items | < 10% |

**Full Details**: [METRICS_GUIDE.md](./METRICS_GUIDE.md)

---

## 🎯 Health Scorecards

### Portfolio Level (5 Dimensions)
1. **Strategic Predictability** - Epic completion, ART predictability
2. **Flow Efficiency** - Lead times, WIP, cross-ART dependencies
3. **Economic WIP** - Concurrent epics
4. **Value Realization** - Features delivered
5. **Systemic Bottlenecks** - Repeating constraints

### ART Level (5 Dimensions)
1. **PI Predictability** - Objectives met
2. **Dependency Health** - Blocked time, cross-team dependencies
3. **Flow Distribution** - 70% Features / 20% Enablers / 10% Defects
4. **Load Balance** - Team throughput variance
5. **Quality Trend** - Defect rates

### Team Level (5 Dimensions)
1. **Sprint Reliability** - Commitment reliability
2. **Flow Efficiency** - Cycle time, wait time
3. **WIP Discipline** - WIP per person
4. **Quality** - Defect injection, rework
5. **Team Stability** - Churn, tenure

**Score Ranges**:
- 90-100: Excellent
- 75-89: Good
- 60-74: Average
- 40-59: Below Average
- 0-39: Poor (critical intervention needed)

**Full Details**: [SCORECARD_FRAMEWORK.md](./SCORECARD_FRAMEWORK.md)

---

## 💡 5-Part Explainable Insight Template

Every coaching insight follows this structure:

### 1. Metric Observation
- What was measured
- Value + comparison to target
- Data source (Jira query)
- Confidence level (High/Medium/Low)

### 2. Interpretation
- What this indicates (systemic issue)
- Why this matters (business impact)
- Severity + Urgency

### 3. Likely Root Causes
- Evidence-backed causes
- Confidence scores
- References to knowledge base

### 4. Recommended Actions
- **Short-term** (next sprint): Quick wins
- **Medium-term** (next PI): Structural changes
- **Long-term**: Systemic changes
- Each action: What, Who, Effort, Success Signal

### 5. Expected Outcome
- Metrics to watch
- Leading indicators (early signals)
- Lagging indicators (confirmation)
- Timeline + Risks

**Full Details**: [EXPLAINABLE_INSIGHTS.md](./EXPLAINABLE_INSIGHTS.md)

---

## 📚 Knowledge Base Structure

```
knowledge/
├── agile_principles/         # Flow theory, Little's Law, Kanban
├── safe/                     # Portfolio flow, ART execution, PI planning
├── coaching_patterns/        # High WIP, low predictability, dependencies
├── metrics_interpretation/   # How to read metrics
├── improvement_playbooks/    # Reduce WIP, dependency mgmt
└── case_studies/            # Real-world examples
```

**Key Features**:
- YAML metadata for precise filtering
- Hybrid search (keyword + semantic)
- Retrieval accuracy: 95%+
- Retrieval time: < 2 seconds

**Full Details**: [RAG_KNOWLEDGE_STRUCTURE.md](./RAG_KNOWLEDGE_STRUCTURE.md)

---

## 🖥️ UI Components

### 6 Core Components
1. **MetricCard** - Current value, trend, sparkline
2. **TrendChart** - P50/P85/P95 over time
3. **Heatmap** - ART/Team comparison
4. **InsightPanel** - Severity, confidence, actions
5. **ActionTracker** - Progress, owner, success signal
6. **CumulativeFlowDiagram** - Bottleneck detection

### 5 Dashboard Views
1. **Portfolio View** - Health score, ART comparison, systemic bottlenecks
2. **ART View** - PI health, dependencies, team load
3. **Team View** - Sprint flow, quality, improvement actions
4. **Knowledge Base** - Searchable documents
5. **Historical Trends** - Metric evolution

**Technology**: React + TypeScript + Vite + Recharts + Tailwind CSS

**Full Details**: [UI_BLUEPRINT.md](./UI_BLUEPRINT.md)

---

## 🛠️ Common Commands

### Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Then edit with your credentials
```

### Run Examples
```bash
# Flow metrics calculator
python -m backend.analytics.metrics.flow_metrics

# Coaching report example
python -m backend.coaching.example_report
```

### Testing
```bash
# All tests
pytest

# With coverage
pytest --cov=backend --cov-report=html

# Specific category
pytest tests/unit/
```

### Code Quality
```bash
black backend/ tests/      # Format
ruff check backend/        # Lint
mypy backend/              # Type check
```

---

## 📂 Key File Locations

### Data Models (863 lines)
- `backend/models/jira_models.py` - Issue, Sprint, PI, Team, ART
- `backend/models/metrics_models.py` - FlowMetrics, PredictabilityMetrics
- `backend/models/analysis_models.py` - Pattern, Bottleneck, Anomaly
- `backend/models/coaching_models.py` - Insight, Proposal, CoachingReport

### Agent Workflow (396 lines)
- `backend/agents/state.py` - AgentState TypedDict
- `backend/agents/graph.py` - LangGraph workflow
- `backend/agents/nodes/` - 6 node implementations

### Integrations (436 lines)
- `backend/integrations/jira_client.py` - Jira REST API client
- `backend/integrations/data_normalizer.py` - JSON → domain models

### Analytics
- `backend/analytics/metrics/flow_metrics.py` - ✅ Complete (235 lines)
- `backend/analytics/metrics/predictability_calculator.py` - 🔜 Phase 2
- `backend/analytics/metrics/quality_metrics.py` - 🔜 Phase 2
- `backend/analytics/scorecards/` - 🔜 Phase 6

### Coaching
- `backend/coaching/example_report.py` - ✅ Complete (477 lines)
- `backend/coaching/reasoner.py` - 🔜 Phase 5
- `backend/coaching/proposal_generator.py` - 🔜 Phase 5

### Configuration
- `.env.example` - Environment variable template
- `backend/config/settings.py` - Pydantic Settings

---

## 🚦 Development Roadmap at a Glance

| Phase | Week | Focus | Status |
|-------|------|-------|--------|
| 0 | 1-2 | Foundation & Design | ✅ Complete |
| 1 | 3-4 | Data Ingestion | 🔜 Next |
| 2 | 5-6 | Metrics Engine | 🔜 Planned |
| 3 | 7-8 | Pattern Detection | 🔜 Planned |
| 4 | 9-10 | RAG Knowledge Base | 🔜 Planned |
| 5 | 11-12 | Coaching Logic | 🔜 Planned |
| 6 | 13 | Explainability | 🔜 Planned |
| 7 | 14-16 | API & Frontend | 🔜 Planned |
| 8 | 17-18 | Testing & Optimization | 🔜 Planned |
| 9 | 19-20 | Production Deployment | 🔜 Planned |

**Full Details**: [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)

---

## 🎓 Learning Resources

### Foundational Books
- **Accelerate** (Forsgren, Humble, Kim) - DORA metrics
- **Actionable Agile Metrics** (Vacanti) - Flow metrics
- **The Principles of Product Development Flow** (Reinertsen) - Queuing theory
- **Kanban** (Anderson) - Pull systems
- **SAFe 6.0** (Scaled Agile, Inc.) - Enterprise agility

### Key Concepts
- **Little's Law**: Lead Time = WIP / Throughput
- **Flow Efficiency**: Active time / Total time
- **PI Predictability**: SAFe metric for ART health
- **Commitment Reliability**: Team predictability
- **Economic WIP**: Portfolio capacity management

---

## ❓ FAQ

**Q: How is this different from Jira reports?**  
A: Jira shows raw data. Evaluation Coach interprets patterns, explains root causes, and recommends specific actions with success metrics.

**Q: Does this replace Scrum Masters or RTEs?**  
A: No. It augments them with data-driven insights so they can focus on coaching and facilitation.

**Q: Is this a maturity assessment?**  
A: No. Scorecards assess execution health, not maturity. Focus is on flow and predictability.

**Q: Can it handle non-SAFe organizations?**  
A: Yes. Core metrics (flow, quality) apply to any Agile environment. SAFe concepts (PI, ART) are optional.

**Q: How long does analysis take?**  
A: Target: < 60 seconds for 1000+ issues (Phase 8 optimization goal)

**Q: Is every recommendation AI-generated?**  
A: AI generates insights, but they're grounded in retrieved knowledge from documented patterns and playbooks (RAG).

**Q: How is data quality assessed?**  
A: Minimum 70% completeness required. Checks created dates, resolution dates, status transitions, custom fields.

---

## 📞 Support

For questions or issues:
1. Check documentation in `docs/` folder
2. Review example code in `backend/coaching/example_report.py`
3. Contact development team

---

## 🏆 Success Criteria (End State)

When fully implemented, the Evaluation Coach will:

✅ Analyze 1000+ Jira issues in < 60 seconds  
✅ Generate insights with 90%+ acceptance rate  
✅ Provide traceable reasoning chain for every recommendation  
✅ Support multi-scope analysis (Team/ART/Portfolio)  
✅ Integrate 25+ knowledge documents via RAG  
✅ Deliver via web UI accessible from any device  
✅ Maintain >80% test coverage  
✅ Achieve >99.5% uptime in production  

---

**Last Updated**: 2026-01-02  
**Version**: 2.0 (Design Enhanced)
