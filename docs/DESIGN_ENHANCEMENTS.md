# Design Enhancement Summary

**Version**: 2.0  
**Date**: 2026-01-02  
**Status**: Design specifications enhanced with comprehensive detail

---

## Overview

This document summarizes the significant design enhancements based on additional input covering:
1. **Jira Analytics Metric Catalog** - Complete metric definitions
2. **SAFe-Aligned Evaluation Scorecard** - Health assessment framework
3. **RAG Knowledge Taxonomy** - Structured, metadata-driven knowledge base
4. **Explainable Insight Template** - 5-part transparency framework
5. **Dashboard & UI Blueprint** - Complete frontend specification

---

## New Documentation

### 1. METRICS_GUIDE.md (350+ lines)

**Purpose**: Single source of truth for all measurable aspects from Jira

**Contents**:
- **Section 1**: Flow & Delivery Metrics (Lead Time, Cycle Time, Throughput, WIP, Flow Efficiency, Blocked Time)
- **Section 2**: Predictability & Planning Metrics (Commitment Reliability, PI Predictability, Scope Change Rate, Spillover Rate)
- **Section 3**: Quality & Sustainability Metrics (Defect Injection Rate, Rework Ratio, Team Load Index, Team Stability)
- **Section 4**: Structural & Dependency Metrics (Cross-Team Dependencies, Blocker Density, Handovers, External Wait Time)
- **Section 5**: Composite Metrics (Overall Health Score, Performance Category Mapping)
- **Section 6**: Benchmark Values (Industry Average, High Performer, World Class)
- **Section 7**: Metric Implementation Priority (Phase 1-3 roadmap)
- **Section 8**: Jira Field Mapping Reference (Custom field examples)
- **Section 9**: Data Quality Requirements (Minimum thresholds)
- **Section 10**: Metric Usage by Scope (Portfolio/ART/Team)

**Key Features**:
- Formulas for all calculations
- Implementation status tracking (✅ ✔️ 🔜)
- Benchmark values from DORA, SAFe, Vacanti
- Jira field mapping examples

**References**: Accelerate (DORA), Actionable Agile Metrics (Vacanti), SAFe 6.0

---

### 2. SCORECARD_FRAMEWORK.md (320+ lines)

**Purpose**: Structured health assessment at Portfolio, ART, and Team levels

**Philosophy**: NOT a maturity model - an **execution health radar**

**Contents**:

#### Portfolio Level Scorecard (5 dimensions)
1. **Strategic Predictability**: Epic completion rate, ART predictability average
2. **Flow Efficiency**: Epic lead time, WIP, cross-ART dependencies
3. **Economic WIP**: Concurrent epics, blocked time
4. **Value Realization**: Features delivered vs planned
5. **Systemic Bottlenecks**: Repeating constraints across ARTs

#### ART Level Scorecard (5 dimensions)
1. **PI Predictability**: Objectives met, planned vs delivered
2. **Dependency Health**: Blocked time, cross-team dependencies
3. **Flow Distribution**: Features/Enablers/Defects balance (target: 70/20/10)
4. **Load Balance**: Team throughput variance
5. **Quality Trend**: Defect injection rate, escaped defects

#### Team Level Scorecard (5 dimensions)
1. **Sprint Reliability**: Commitment reliability, scope change rate
2. **Flow Efficiency**: Cycle time, wait time
3. **WIP Discipline**: WIP per person (target: ≤1.5)
4. **Quality**: Defect injection rate, rework ratio
5. **Team Stability**: Team churn, tenure

**Key Features**:
- Healthy/Warning/Critical thresholds for each signal
- Coaching guidance for critical states
- JSON scorecard output examples
- Scoring algorithms with weighted dimensions
- Visualization guidance (radar charts, scorecard cards)

---

### 3. RAG_KNOWLEDGE_STRUCTURE.md (450+ lines)

**Purpose**: Metadata-driven, structured knowledge retrieval for coaching

**Philosophy**: Not "documents in a folder" - tagged, queryable, contextual resources

**Contents**:

#### Knowledge Domain Taxonomy (6 domains)
```
knowledge/
├── agile_principles/      # Flow theory, Little's Law, System thinking
├── safe/                  # Portfolio flow, ART execution, PI planning
├── coaching_patterns/     # Symptom → Guidance (high WIP, low predictability, etc.)
├── metrics_interpretation/ # How to read metrics (lead time, throughput, etc.)
├── improvement_playbooks/ # Actionable how-tos (reduce WIP, dependency mgmt)
└── case_studies/          # Real-world examples
```

#### Document Metadata Schema (YAML frontmatter)
```yaml
---
id: [unique_id]
title: [Pattern Name]
category: coaching_pattern
tags: [list of tags]
applicability:
  scope: [Team, ART, Portfolio]
  metrics:
    - name: [metric_name]
      trigger: [threshold]
symptom: [One-line description]
root_causes: [List]
related_metrics: [List]
related_patterns: [List]
confidence: [high, medium, low]
---
```

#### Retrieval Strategy
- **Metadata-driven filtering**: Filter by scope, metrics, confidence before semantic search
- **Hybrid search**: Combine BM25 (keyword) + vector (semantic) search
- **Context-aware**: Filter results based on current state context
- **Structured queries**: Pattern detection → metadata query → relevant knowledge

**Key Features**:
- Complete example document (`coaching_patterns/high_wip.md` with 200+ lines)
- Ingestion pipeline script (`backend/rag/ingest_knowledge.py`)
- ChromaDB integration with OpenAI embeddings
- Metadata-based retrieval reduces search space by 80%+
- Knowledge quality checklist

**Success Criteria**: 95%+ retrieval accuracy, <2s retrieval time

---

### 4. EXPLAINABLE_INSIGHTS.md (480+ lines)

**Purpose**: Ensure every coaching output is transparent, evidence-based, actionable

**Core Principle**: User must understand What/Why/How/Outcome

**Contents**:

#### 5-Part Insight Template Structure
1. **Metric Observation**
   - What was measured, value, comparison, time period, data source
   - Confidence level (High/Medium/Low)
   - Raw data with specific issue keys

2. **Interpretation**
   - What this indicates (systemic, not blame)
   - Why this matters (business/team impact)
   - Contextual factors
   - Impact assessment (Severity, Urgency, Scope)

3. **Likely Root Causes**
   - Evidence-backed causes with confidence scores
   - References to knowledge base documents
   - Explicit assumptions stated

4. **Recommended Actions**
   - **Short-term** (next sprint): Quick wins
   - **Medium-term** (next PI): Structural improvements
   - **Long-term**: Systemic/cultural change
   - Each action: What, Who, Effort, Dependencies, Success Signal

5. **Expected Outcome**
   - Metrics to watch with expected changes
   - Leading indicators (early signals)
   - Lagging indicators (confirming success)
   - Timeline and risks

**Key Features**:
- Complete example insight (Team-level high WIP, 300+ lines)
- Pydantic data models for all 5 parts
- Template renderer (`render_insight_markdown()`)
- Insight prioritization scoring algorithm
- Quality checklist (non-blame, evidence-backed, specific, measurable)

**Quality Checklist**:
- [ ] Title is non-blame
- [ ] Includes confidence level
- [ ] Explains WHY it matters
- [ ] Root causes backed by evidence
- [ ] Actions are specific and actionable
- [ ] Actions have owners
- [ ] Expected outcomes are measurable
- [ ] Risks are identified
- [ ] Supporting evidence linked

---

### 5. UI_BLUEPRINT.md (650+ lines)

**Purpose**: Complete frontend specification for intuitive, drill-down dashboards

**Philosophy**: Read-only analysis dashboards for **understanding and learning**, not operational tracking

**Contents**:

#### Navigation Structure (3 main views)
1. **Portfolio View**: Flow & predictability, ART comparison, systemic bottlenecks
2. **ART View**: PI health, dependencies, team load balance
3. **Team View**: Sprint flow, quality & rework, improvement actions

#### Core UI Components (6 components)
1. **MetricCard**: Current value, target, trend, sparkline, drill-down button
2. **TrendChart**: P50/P85/P95 lines over time (Chart.js/Recharts)
3. **Heatmap**: ART/Team comparison with color-coded cells
4. **InsightPanel**: Severity icon, confidence badge, summary, action buttons
5. **ActionTracker**: Checkbox, progress bars, owner, effort, success signal
6. **CumulativeFlowDiagram**: Stacked area chart with bottleneck detection

#### Page Layouts (Complete HTML)
- Portfolio View layout (health score banner, metrics grid, heatmap, top insights)
- Team View layout (sprint overview, metrics row, coaching section, action tracker, CFD)
- Responsive design patterns

#### RESTful API Endpoints (20+ endpoints)
```
/api/v1/
├── /portfolio/{health, metrics, arts}
├── /art/{art_id}/{health, metrics, teams, dependencies, insights}
├── /team/{team_id}/{health, metrics, sprint/current, insights, actions}
├── /insights/{insight_id, feedback, list}
├── /actions/{action_id, create, update}
└── /analysis/{run, status/{run_id}, results/{run_id}}
```

#### Technology Stack Recommendation
**Primary**: React + TypeScript + Vite
- **Charts**: Recharts
- **Data Fetching**: React Query
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Build**: Vite

**Alternative**: Vanilla JS + HTML/CSS (simpler, no build step)

#### Styling Guidelines
- Color palette (healthy: green, warning: yellow, critical: red)
- Typography system (font sizes, families)
- WCAG 2.1 Level AA compliance (contrast ratios ≥4.5:1)
- Responsive breakpoints

**Success Criteria**: <500ms API response, <2s frontend load, responsive, WCAG AA compliant

---

## Integration Points

### How These Documents Work Together

```
┌─────────────────────────────────────────────────────────────┐
│                    METRICS_GUIDE.md                        │
│  (What can be measured from Jira + benchmarks)            │
└─────────────────┬──────────────────────────────────────────┘
                  │ feeds into
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                 SCORECARD_FRAMEWORK.md                     │
│  (How to assess health at Portfolio/ART/Team levels)      │
└─────────────────┬──────────────────────────────────────────┘
                  │ dimensions trigger
                  ↓
┌─────────────────────────────────────────────────────────────┐
│              RAG_KNOWLEDGE_STRUCTURE.md                    │
│  (Retrieve coaching patterns + improvement playbooks)      │
└─────────────────┬──────────────────────────────────────────┘
                  │ knowledge generates
                  ↓
┌─────────────────────────────────────────────────────────────┐
│              EXPLAINABLE_INSIGHTS.md                       │
│  (5-part transparent insight template)                     │
└─────────────────┬──────────────────────────────────────────┘
                  │ rendered in
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                   UI_BLUEPRINT.md                          │
│  (Dashboard views displaying insights + actions)           │
└─────────────────────────────────────────────────────────────┘
```

**Example Flow**:
1. **Metrics Guide**: WIP per person = 3.2 (target: ≤1.5)
2. **Scorecard**: Team "WIP Discipline" dimension = 55 (critical)
3. **RAG**: Retrieve `coaching_patterns/high_wip.md` + `improvement_playbooks/reduce_wip.md`
4. **Explainable Insight**: Generate 5-part insight with observation, interpretation, root causes, actions, expected outcome
5. **UI**: Display in `InsightPanel` component on Team View with action tracker

---

## Updated Development Roadmap

### Phase 4 (Weeks 9-10) - RAG Knowledge Base
**Enhanced with**:
- Structured taxonomy with 6 domains
- YAML metadata schema for all documents
- ChromaDB + OpenAI embeddings
- Hybrid search (BM25 + semantic)
- 25+ knowledge documents (vs 20)

### Phase 6 (Week 13) - Explainability
**Enhanced with**:
- 5-part ExplainableInsight template
- Scorecard framework (Portfolio/ART/Team)
- Quality checklist validation
- Insight prioritization algorithm

### Phase 7 (Weeks 14-16) - API & Frontend
**Enhanced with**:
- 20+ RESTful API endpoints specified
- 6 core UI components detailed
- 5 dashboard views with layouts
- React + TypeScript + Vite stack
- WCAG 2.1 AA accessibility requirements

---

## Code Artifacts to Create

### Phase 4 (RAG)
1. `knowledge/` folder with 25+ markdown documents following metadata schema
2. `backend/rag/ingest_knowledge.py` - Knowledge ingestion pipeline
3. `backend/rag/rag_engine.py` - Hybrid search engine
4. `backend/rag/metadata_parser.py` - YAML frontmatter extraction

### Phase 6 (Explainability)
1. `backend/models/explainable_insight.py` - 5-part template models
2. `backend/models/scorecard.py` - Scorecard framework models
3. `backend/analytics/scorecards/` - Scorecard calculators
4. `backend/analytics/scorecards/thresholds.yaml` - Configurable thresholds
5. `backend/coaching/insight_renderer.py` - Template renderer
6. `backend/coaching/report_factory.py` - Multi-level report generation

### Phase 7 (API & UI)
1. `backend/api/main.py` - FastAPI application
2. `backend/api/routes/` - Endpoint routers (portfolio, art, team, insights, actions, analysis)
3. `frontend/` - React + TypeScript project
4. `frontend/src/components/` - 6 core UI components
5. `frontend/src/pages/` - 5 dashboard views
6. `frontend/src/services/api.ts` - API client

---

## Strengths of Enhanced Design

### 1. **Transparency & Trust**
- Every insight shows confidence level
- Root causes backed by specific evidence
- Actions linked to expected outcomes
- Risks explicitly stated

### 2. **Actionability**
- Actions have owners, effort estimates, dependencies
- Success signals define "done"
- Short/medium/long term planning
- Priority scores guide sequencing

### 3. **Scalability**
- Metadata-driven retrieval scales to 1000+ knowledge docs
- Scorecard framework applies to any scope (Team/ART/Portfolio)
- UI components are reusable across views

### 4. **Non-Blame Culture**
- Insight titles describe issues, not people
- Root causes focus on systemic issues
- Coaching patterns emphasize learning

### 5. **Evidence-Based**
- All metrics link to Jira queries
- Knowledge documents cite sources
- Benchmark values from industry research

---

## Next Immediate Steps

Based on the enhanced design, the next priority actions are:

1. **Week 3-4 (Phase 1)**: Complete Jira integration with caching
2. **Week 5-6 (Phase 2)**: Implement all 4 metric calculators (Flow ✅, Predictability, Quality, TeamHealth)
3. **Week 7-8 (Phase 3)**: Build pattern detection analyzers
4. **Week 9-10 (Phase 4)**: Create 25+ knowledge documents and RAG system
5. **Week 11-12 (Phase 5)**: Implement coaching logic (Reasoner, ProposalGenerator)
6. **Week 13 (Phase 6)**: Build ExplainableInsight + Scorecard systems
7. **Week 14-16 (Phase 7)**: Create FastAPI + React frontend

---

## Questions to Consider

### Knowledge Base
- Which 5-10 coaching patterns are most critical to document first?
- Should case studies be real or anonymized examples?
- How often should knowledge base be updated?

### Scorecard Thresholds
- Should thresholds be configurable per organization?
- How to handle different team sizes affecting metrics?
- Should benchmarks be industry-specific (finance vs tech)?

### UI/UX
- Should the system support dark mode?
- How to handle mobile/tablet access (read-only dashboards)?
- Should users be able to customize dashboard layouts?

### Deployment
- Single-tenant (self-hosted) or multi-tenant SaaS?
- Database: SQLite (simple) or PostgreSQL (production)?
- Vector store: ChromaDB (embedded) or Pinecone (cloud)?

---

## Documentation Status

| Document | Lines | Status | Purpose |
|----------|-------|--------|---------|
| METRICS_GUIDE.md | 350+ | ✅ Complete | Metric catalog & formulas |
| SCORECARD_FRAMEWORK.md | 320+ | ✅ Complete | Health assessment framework |
| RAG_KNOWLEDGE_STRUCTURE.md | 450+ | ✅ Complete | Knowledge taxonomy & retrieval |
| EXPLAINABLE_INSIGHTS.md | 480+ | ✅ Complete | 5-part transparency template |
| UI_BLUEPRINT.md | 650+ | ✅ Complete | Frontend specification |
| ARCHITECTURE.md | 267 | ✅ Complete | System architecture |
| STRUCTURE.md | 243 | ✅ Complete | Folder organization |
| DEVELOPMENT_ROADMAP.md | 614 | ✅ Enhanced | 20-week implementation plan |
| SUMMARY.md | 290 | 🔄 Needs update | Overall deliverables summary |
| README.md | - | 🔄 Needs update | Project overview |

**Total New Documentation**: 2,250+ lines  
**Grand Total Documentation**: 4,250+ lines

---

## End-State Vision

When complete, the Evaluation Coach will:

1. **Analyze** 1000+ Jira issues in < 60 seconds
2. **Detect** patterns using 15+ metrics across 3 scopes
3. **Retrieve** relevant knowledge from 25+ documents
4. **Generate** transparent insights with 5-part template
5. **Score** health across Portfolio/ART/Team dimensions
6. **Recommend** specific, evidence-based actions
7. **Visualize** in intuitive, drill-down dashboards
8. **Track** improvement actions with success metrics
9. **Explain** every recommendation with confidence levels
10. **Scale** from single team to enterprise portfolio

**Where This Shines**:
✅ System-level coaching (not individual blame)  
✅ Evidence-based improvement (not guesswork)  
✅ SAFe-aligned but not dogmatic  
✅ Executive-safe explanations  
✅ Scales from team → portfolio

---

## References

- **New Design Input**: User-provided specifications (2026-01-02)
- **Original Requirements**: Phase 0 foundation work
- **Industry Standards**: DORA, SAFe 6.0, Actionable Agile Metrics
- **Best Practices**: Lean thinking, Flow theory, Systems thinking
