# Evaluation Coach - Development Roadmap

## Overview

This roadmap outlines the phased development approach for the Evaluation Coach system. Each phase builds upon the previous one, delivering incremental value while maintaining a production-quality standard.

## Phase 0: Foundation ✅ COMPLETED

**Status**: Complete - Excel import feature implemented and working

**Completed Items**:
- ✅ System architecture defined
- ✅ Folder structure created
- ✅ Core data models (Pydantic)
- ✅ FastAPI backend with 19 endpoints
- ✅ SQLite database with 7 models
- ✅ Frontend UI with 5 tabs
- ✅ **Excel Import Feature** - Admin tab with staging workflow
  - Upload .xlsx files from Jira exports
  - Preview and validate imported data
  - Edit custom fields and standard fields
  - Commit to database with validation
  - Text cleaning (removes _x000D_, h1-3 markers)
  - Custom fields support (Epic Hypothesis Statement, Business Outcome, etc.)
  - Lead-time calculation
- ✅ Server management (start.sh, stop.sh scripts)

**Deliverables**:
- ✅ ARCHITECTURE.md
- ✅ STRUCTURE.md
- ✅ Backend: main.py (572 lines), database.py (221 lines)
- ✅ Frontend: index.html (648 lines), app.js (960 lines), styles.css
- ✅ Services: excel_import_service.py (467 lines)
- ✅ Working application on ports 8850 (backend) and 8800 (frontend)

---

## Phase 0.5: Current Status & Next Steps 🎯 CURRENT

**What's Working Now**:
1. ✅ Excel upload and import with custom fields
2. ✅ Data staging and validation
3. ✅ Issue editing with expandable text areas
4. ✅ Database commit with date parsing
5. ✅ Resizable modal editor (1200px wide)
6. ✅ Clean text import (removes _x000D_, h1-3 markers)

**Immediate Next Steps** (Priority Order):

### 1. Data Visualization & Dashboard 📊 (High Priority - Week 1)
**Goal**: Make imported data useful by showing insights

Tasks:
- [ ] Create "View Issues" page to display all imported issues
- [ ] Add filters: by portfolio, issue type, status
- [ ] Show issue count, status distribution charts
- [ ] Display custom fields in issue cards
- [ ] Export filtered data to Excel

**Why**: Users need to see what they've imported and analyze it

### 2. Metrics Calculation 📈 (High Priority - Week 1-2)  
**Goal**: Calculate actual metrics from imported data

Tasks:
- [ ] Implement lead-time calculation from actual dates
- [ ] Calculate cycle time (if status transition dates available)
- [ ] Show metrics dashboard with charts
- [ ] Portfolio-level rollup metrics
- [ ] Trend analysis over time

**Why**: This is the core value - turning data into insights

### 3. Enhanced Import Features 📥 (Medium Priority - Week 2)
**Goal**: Support more import scenarios

Tasks:
- [ ] Support multiple sheets in Excel files
- [ ] Batch import multiple files
- [ ] Import history and versioning
- [ ] Duplicate detection and merge strategies
- [ ] Status transition history import

**Why**: Production use requires flexible import options

### 4. Data Quality & Validation ✅ (Medium Priority - Week 2-3)
**Goal**: Ensure data integrity

Tasks:
- [ ] Enhanced validation rules (date ranges, required fields)
- [ ] Data quality score per issue
- [ ] Missing data reports
- [ ] Bulk edit capabilities
- [ ] Data cleaning suggestions (AI-powered)

**Why**: Good analysis requires clean data

### 5. Real Jira Integration 🔗 (Low Priority - Week 3-4)
**Goal**: Replace Excel import with live Jira sync

Tasks:
- [ ] Complete JiraClient implementation
- [ ] Implement authentication (Basic Auth, OAuth)
- [ ] Add retry logic and rate limiting
- [ ] Create JQL query builder
- [ ] Background sync scheduler
- [ ] Incremental updates (only changed issues)

**Why**: Eliminates manual Excel exports

---

## Phase 1: Data Ingestion & Normalization (Week 3-5)

**Objectives**:
- Implement complete Jira REST API integration
- Build robust data normalization
- Implement caching layer
- Create data quality assessment

**Tasks**:

### 1.1 Jira Integration (3 days)
- [ ] Complete `JiraClient` with all required endpoints
- [ ] Implement authentication (Basic Auth, OAuth)
- [ ] Add retry logic and rate limiting
- [ ] Create JQL query builder
- [ ] Write unit tests

### 1.2 Data Normalization (3 days)
- [ ] Complete `DataNormalizer` for all issue types
- [ ] Implement sprint normalization
- [ ] Implement PI normalization
- [ ] Handle custom field mapping configuration
- [ ] Write unit tests

### 1.3 Caching & Storage (2 days)
- [ ] Implement SQLite/PostgreSQL schema
- [ ] Create caching layer for Jira data
- [ ] Implement data versioning
- [ ] Add cache invalidation logic

### 1.4 Data Collector Node (2 days)
- [ ] Complete `data_collector_node` implementation
- [ ] Integrate JiraClient and DataNormalizer
- [ ] Add error handling and recovery
- [ ] Write integration tests

**Deliverables**:
- Functional Data Collector node
- 100+ unit tests
- Sample data fixtures

**Success Criteria**:
- Can fetch and normalize 1000+ issues in < 30 seconds
- Data quality score accurately reflects completeness
- Cache reduces redundant API calls by 80%+

---

## Phase 2: Metrics Engine (Week 5-6)

**Objectives**:
- Implement all metric calculators
- Create extensible metrics framework
- Build metrics aggregation and comparison

**Tasks**:

### 2.1 Flow Metrics (3 days)
- [x] Complete `FlowMetricsCalculator` (example done)
- [ ] Add WIP distribution analysis
- [ ] Add flow efficiency calculation
- [ ] Write unit tests

### 2.2 Predictability Metrics (2 days)
- [ ] Implement `PredictabilityCalculator`
- [ ] Calculate commitment reliability
- [ ] Calculate velocity trends
- [ ] Scope change analysis
- [ ] Write unit tests

### 2.3 Quality Metrics (2 days)
- [ ] Implement `QualityMetricsCalculator`
- [ ] Calculate blocked time metrics
- [ ] Calculate rework rates
- [ ] Defect density analysis
- [ ] Write unit tests

### 2.4 Team Health Metrics (2 days)
- [ ] Implement `TeamMetricsCalculator`
- [ ] WIP per person analysis
- [ ] Team stability metrics
- [ ] Cross-team dependency tracking
- [ ] Write unit tests

### 2.5 Metrics Engine Node (1 day)
- [ ] Complete `metrics_engine_node`
- [ ] Integrate all calculators
- [ ] Create `MetricsSnapshot` aggregation
- [ ] Write integration tests

**Deliverables**:
- 4 complete metric calculators
- Comprehensive metrics test suite
- Example metrics outputs

**Success Criteria**:
- All metrics match manual calculations
- Handles edge cases (zero issues, incomplete data)
- Metrics calculation completes in < 5 seconds for 1000 issues

---

## Phase 3: Pattern Detection & Analysis (Week 7-8)

**Objectives**:
- Implement statistical analysis
- Detect bottlenecks, anomalies, and trends
- Build pattern classification

**Tasks**:

### 3.1 Trend Analysis (2 days)
- [ ] Implement `TrendAnalyzer`
- [ ] Time-series analysis for key metrics
- [ ] Statistical significance testing
- [ ] Trend classification (improving/declining/stable)
- [ ] Write unit tests

### 3.2 Anomaly Detection (2 days)
- [ ] Implement `AnomalyDetector`
- [ ] Statistical outlier detection
- [ ] Contextual anomaly detection
- [ ] Positive vs negative anomaly classification
- [ ] Write unit tests

### 3.3 Bottleneck Detection (2 days)
- [ ] Implement `BottleneckFinder`
- [ ] Analyze status transition delays
- [ ] Identify capacity constraints
- [ ] Calculate bottleneck impact
- [ ] Write unit tests

### 3.4 Dependency Analysis (2 days)
- [ ] Implement `DependencyAnalyzer`
- [ ] Cross-team dependency mapping
- [ ] Blocking issue analysis
- [ ] Dependency impact assessment
- [ ] Write unit tests

### 3.5 Pattern Detector Node (2 days)
- [ ] Complete `pattern_detector_node`
- [ ] Integrate all analyzers
- [ ] Pattern prioritization logic
- [ ] Write integration tests

**Deliverables**:
- 4 complete analyzers
- Pattern detection test suite
- Example analysis outputs

**Success Criteria**:
- Detects known patterns with 90%+ accuracy
- No false positives in controlled test data
- Analysis completes in < 10 seconds

---

## Phase 4: Knowledge Retrieval (RAG) (Week 9-10)

**Objectives**:
- Implement vector store
- Create knowledge base
- Build RAG retrieval system

**Tasks**:

### 4.1 Knowledge Base Setup (3 days)
- [ ] Create SAFe principles knowledge base
- [ ] Create Agile best practices knowledge base
- [ ] Create flow metrics knowledge base
- [ ] Create improvement playbooks
- [ ] Format all knowledge in Markdown

### 4.2 Vector Store (2 days)
- [ ] Choose vector DB (ChromaDB recommended)
- [ ] Implement embedding generation (OpenAI text-embedding-3-small)
- [ ] Build document metadata parser (extract YAML frontmatter)
- [ ] Create MarkdownHeaderTextSplitter for chunking
- [ ] Build knowledge indexing pipeline (`backend/rag/ingest_knowledge.py`)
- [ ] Implement metadata-driven filtering
- [ ] Write unit tests

### 4.3 RAG Engine (3 days)
- [ ] Implement `RAGEngine` class with hybrid search (BM25 + semantic)
- [ ] Query generation from detected patterns with metadata
- [ ] Semantic search implementation with confidence scoring
- [ ] Result ranking by relevance + metadata match
- [ ] Context-aware filtering by scope/metric/confidence
- [ ] Write unit tests

### 4.4 Knowledge Retriever Node (2 days)
- [ ] Complete `knowledge_retriever_node` implementation
- [ ] Integrate RAG engine with pattern detector output
- [ ] Structured query construction from patterns
- [ ] Knowledge result formatting for coaching node
- [ ] Write integration tests

**Deliverables**:
- Knowledge base with 25+ documents following metadata schema (see [RAG_KNOWLEDGE_STRUCTURE.md](./RAG_KNOWLEDGE_STRUCTURE.md))
- Vector store with embeddings in `data/vectorstore/`
- `RAGEngine` class with hybrid search
- `knowledge_retriever_node` complete
- `backend/rag/ingest_knowledge.py` ingestion script

**Success Criteria**:
- Knowledge retrieval accuracy ≥ 95% (top 3 results relevant)
- Retrieval time < 2 seconds
- Metadata filtering reduces search space by 80%+
- All knowledge documents pass quality checklist

---

## Phase 5: Reasoning & Coaching (Week 11-12)

**Objectives**:
- Implement coaching logic
- Generate insights and proposals
- Build prioritization system

**Tasks**:

### 5.1 Reasoner (3 days)
- [ ] Implement `Reasoner`
- [ ] Root cause analysis logic
- [ ] Insight generation from patterns + knowledge
- [ ] Evidence linking
- [ ] Write unit tests

### 5.2 Proposal Generator (3 days)
- [ ] Implement `ProposalGenerator`
- [ ] Proposal templates
- [ ] Actionable step generation
- [ ] Success criteria definition
- [ ] Write unit tests

### 5.3 Prioritizer (2 days)
- [ ] Implement `Prioritizer`
- [ ] Impact/effort scoring
- [ ] Priority calculation algorithm
- [ ] Dependency-aware ordering
- [ ] Write unit tests

### 5.4 Coaching Node (2 days)
- [ ] Complete `coaching_node`
- [ ] Integrate reasoner and generator
- [ ] Create executive summary
- [ ] Write integration tests

**Deliverables**:
- Complete coaching logic
- Example coaching outputs
- Prioritization framework

**Success Criteria**:
- Proposals are specific and actionable
- Priority scores align with intuition
- Evidence always links to data

---

## Phase 6: Report Generation & Explainability (Week 13)

**Objectives**:
- Implement 5-part explainable insight template system
- Build scorecard framework for Portfolio/ART/Team health
- Create report factory for different scopes

**Tasks**:

### 6.1 Explainable Insight System (3 days)
- [ ] Implement `ExplainableInsight` Pydantic model (5-part structure)
- [ ] Implement `MetricObservation`, `Interpretation`, `RootCause`, `RecommendedActions`, `ExpectedOutcome` models
- [ ] Create insight template renderer (`render_insight_markdown()`)
- [ ] Implement insight prioritization scoring algorithm
- [ ] Create quality checklist validation
- [ ] Write unit tests

### 6.2 Scorecard Implementation (2 days)
- [ ] Implement `Scorecard`, `Dimension`, `Signal` models
- [ ] Create Portfolio/ART/Team scorecard calculators
- [ ] Implement threshold configuration (YAML-based)
- [ ] Build scoring algorithms (`calculate_dimension_score()`, `calculate_overall_score()`)
- [ ] Create radar chart data generation
- [ ] Write unit tests

### 6.3 Report Factory (2 days)
- [ ] Implement `ReportFactory` class
- [ ] Team-level report generation (scorecard + insights + actions)
- [ ] ART-level report generation
- [ ] Portfolio-level report generation
- [ ] Executive summary generator
- [ ] Write unit tests

### 6.4 Explainer Node (1 day)
- [ ] Complete `explainer_node` implementation
- [ ] Integrate ExplainableInsight generation
- [ ] Integrate Scorecard generation
- [ ] Format complete coaching reports
- [ ] Link supporting evidence (Jira queries, knowledge base docs)
- [ ] Write tests

**Deliverables**:
- `ExplainableInsight` model with 5-part template (see [EXPLAINABLE_INSIGHTS.md](./EXPLAINABLE_INSIGHTS.md))
- `Scorecard` framework with thresholds (see [SCORECARD_FRAMEWORK.md](./SCORECARD_FRAMEWORK.md))
- `ReportFactory` class
- `explainer_node` complete
- Quality checklist for insights

**Success Criteria**:
- Every insight follows 5-part template (Observation → Interpretation → Root Causes → Actions → Expected Outcome)
- All insights pass quality checklist (non-blame, evidence-backed, specific actions)
- Non-technical stakeholders can understand outputs
- Every action has owner, effort, and success signal
- Reports link to supporting evidence

**Objectives**:
- Generate human-readable reports
- Create multi-level summaries
- Build report templates

**Tasks**:

### 6.1 Report Templates (3 days)
- [ ] Team-level report template
- [ ] ART-level report template
- [ ] Portfolio-level report template
- [ ] HTML report generation
- [ ] Markdown report generation

### 6.2 Explainer Node (2 days)
- [ ] Complete `explainer_node`
- [ ] Integrate report templates
- [ ] Generate reasoning explanations
- [ ] Write integration tests

**Deliverables**:
- 3 report templates
- Example HTML/Markdown reports

**Success Criteria**:
- Reports are clear and actionable
- Non-technical stakeholders can understand
- All claims trace back to data

---

## Phase 7: API & Frontend (Week 14-16)

**Objectives**:
- Build REST API
- Create web frontend
- Implement visualizations

**Tasks**:

### 7.1 REST API (4 days)
- [ ] Implement FastAPI server
- [ ] Create analysis endpoints
- [ ] Create metrics endpoints
- [ ] Create report endpoints
- [ ] Add authentication
- [ ] Write API tests

### 7.2 Frontend (6 days)
- [ ] Create HTML/CSS structure
- [ ] Implement dashboard view
- [ ] Implement metrics visualizations (Chart.js)
- [ ] Implement insights view
- [ ] Implement recommendations view
- [ ] Add drill-down capabilities

### 7.3 Integration (2 days)
- [ ] Connect frontend to API
- [ ] Error handling
- [ ] Loading states
- [ ] End-to-end testing

**Deliverables**:
- Functional REST API
- Web-based UI
- Interactive visualizations

**Success Criteria**:
- API responds in < 1 second for cached data
- UI is usable on mobile devices
- Visualizations are interactive

---

## Phase 8: Testing & Refinement (Week 17-18)

**Objectives**:
- Comprehensive testing
- Performance optimization
- Documentation

**Tasks**:

### 8.1 Testing (5 days)
- [ ] Unit test coverage > 80%
- [ ] Integration tests for all workflows
- [ ] End-to-end tests
- [ ] Performance benchmarking
- [ ] Load testing

### 8.2 Optimization (3 days)
- [ ] Optimize slow queries
- [ ] Implement parallel processing
- [ ] Reduce memory footprint
- [ ] Cache optimization

### 8.3 Documentation (2 days)
- [ ] API documentation
- [ ] User guide
- [ ] Deployment guide
- [ ] Troubleshooting guide

**Deliverables**:
- Test coverage report
- Performance benchmarks
- Complete documentation

**Success Criteria**:
- All tests passing
- Full analysis completes in < 60 seconds
- Documentation is clear and complete

---

## Phase 9: Deployment & Production (Week 19-20)

**Objectives**:
- Production deployment
- Monitoring and logging
- User onboarding

**Tasks**:

### 9.1 Deployment (3 days)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Environment configuration
- [ ] Database migrations
- [ ] Backup strategy

### 9.2 Monitoring (2 days)
- [ ] Logging configuration
- [ ] Error tracking (Sentry)
- [ ] Metrics dashboard (Grafana)
- [ ] Alerting rules

### 9.3 Launch (5 days)
- [ ] Beta testing with 1-2 teams
- [ ] Gather feedback
- [ ] Iterate on UX
- [ ] Training sessions
- [ ] Official launch

**Deliverables**:
- Production deployment
- Monitoring dashboard
- User training materials

**Success Criteria**:
- System is stable and reliable
- Users can run analyses independently
- Response time SLA met (95th percentile < 5s)

---

## Future Enhancements (Post-Launch)

### Short-term (3-6 months)
- [ ] Slack/Teams integration for notifications
- [ ] Scheduled automated reports
- [ ] Historical trend comparisons
- [ ] Custom metric definitions
- [ ] Multi-tenant support

### Medium-term (6-12 months)
- [ ] GitHub integration (PR metrics)
- [ ] GitLab integration
- [ ] Jenkins/CI integration
- [ ] Predictive analytics (ML models)
- [ ] What-if scenario analysis

### Long-term (12+ months)
- [ ] Real-time analysis
- [ ] Mobile app
- [ ] Integration marketplace
- [ ] White-label version
- [ ] Enterprise features (SSO, audit logs)

---

## Extension Points for Customization

### Custom Metrics
```python
# backend/analytics/metrics/custom/my_metric.py
from backend.analytics.metrics.base import MetricCalculator

class MyCustomMetric(MetricCalculator):
    def calculate(self, data):
        # Your logic here
        pass
```

### Custom Analyzers
```python
# backend/analytics/analyzers/custom/my_analyzer.py
from backend.analytics.analyzers.base import Analyzer

class MyCustomAnalyzer(Analyzer):
    def analyze(self, context):
        # Your logic here
        pass
```

### Custom Knowledge Sources
```python
# backend/knowledge/sources/custom/my_source.py
from backend.knowledge.sources.base import KnowledgeSource

class MyKnowledgeSource(KnowledgeSource):
    def retrieve(self, query):
        # Your logic here
        pass
```

### Custom Report Templates
```python
# backend/coaching/templates/custom/my_report.py
from backend.coaching.templates.base import ReportTemplate

class MyReportTemplate(ReportTemplate):
    def generate(self, data):
        # Your logic here
        pass
```

---

## Success Metrics

### Technical Metrics
- Test coverage: > 80%
- API response time (p95): < 5 seconds
- Full analysis time: < 60 seconds
- Uptime: > 99.5%

### Business Metrics
- User adoption: 80% of teams use monthly
- User satisfaction: NPS > 40
- Time saved per team: > 4 hours/month
- Actionable insights: > 90% acceptance rate

---

## Risk Mitigation

### Technical Risks
- **Risk**: Jira API rate limiting
  - **Mitigation**: Implement aggressive caching, request batching
- **Risk**: Large data volumes cause performance issues
  - **Mitigation**: Pagination, lazy loading, database indexing
- **Risk**: LLM costs too high
  - **Mitigation**: Use smaller models, cache embeddings, optimize prompts

### Adoption Risks
- **Risk**: Teams don't trust AI recommendations
  - **Mitigation**: Strong explainability, link every claim to data
- **Risk**: Resistance to change
  - **Mitigation**: Focus on systemic issues (not blame), quick wins
- **Risk**: Recommendations ignored
  - **Mitigation**: Track implementation, measure impact, iterate

---

## Team Structure (Recommended)

- **Senior Engineer (You)**: Architecture, backend, LangGraph
- **Frontend Developer**: UI, visualizations, UX
- **Agile Coach**: Domain expertise, knowledge base, validation
- **DevOps Engineer**: Deployment, monitoring, infrastructure

**Estimated Full-Time Equivalent**: 2-3 FTE for 20 weeks
