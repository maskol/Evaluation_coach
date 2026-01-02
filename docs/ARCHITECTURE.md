# Evaluation Coach - System Architecture

**Current Implementation: Phase 0 Complete - Full-Stack Web Application**

*Last Updated: 2 January 2026*

---

## 1. Current Architecture (Phase 0)

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    BROWSER (Client)                         │
│                  http://localhost:8800                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         Frontend (HTML5 + JavaScript)                │  │
│  │                                                       │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┐     │  │
│  │  │Dashboard │   Chat   │ Insights │ Metrics  │     │  │
│  │  └──────────┴──────────┴──────────┴──────────┘     │  │
│  │                                                       │  │
│  │  • Scorecard display    • AI coach interface        │  │
│  │  • ART comparison       • Insight cards             │  │
│  │  • Metric cards         • Metrics catalog           │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API (JSON)
                          │ Fetch API calls
┌─────────────────────────▼───────────────────────────────────┐
│               FastAPI Backend Server                        │
│                http://localhost:8850                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         API Endpoints (main.py - 479 lines)          │  │
│  │                                                       │  │
│  │  GET  /api/health           - System status         │  │
│  │  GET  /api/v1/dashboard     - Overview data         │  │
│  │  POST /api/v1/scorecard     - Generate health score │  │
│  │  POST /api/v1/insights/...  - Insight operations    │  │
│  │  POST /api/v1/chat          - AI coach messages     │  │
│  │  GET  /api/v1/metrics       - Metric queries        │  │
│  │  POST /api/v1/jira/sync     - Jira integration      │  │
│  │                                                       │  │
│  │  • CORS middleware for localhost:8800               │  │
│  │  • Pydantic validation (api_models.py)              │  │
│  │  • Async/await support                              │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │      Service Layer (business logic)                  │  │
│  │                                                       │  │
│  │  ┌─────────────────┬─────────────────┬────────────┐ │  │
│  │  │  LLMService     │ MetricsService  │ Insights   │ │  │
│  │  │  (130 lines)    │ (163 lines)     │ Service    │ │  │
│  │  │                 │                 │ (228 lines)│ │  │
│  │  │  • Chat routing │ • Scorecard gen │ • 5-part   │ │  │
│  │  │  • Keyword      │ • Metric calc   │   insights │ │  │
│  │  │    detection    │ • Demo data     │ • Demo data│ │  │
│  │  └─────────────────┴─────────────────┴────────────┘ │  │
│  └───────────────────────┬─────────────────────────────┘  │
│                          │                                 │
│  ┌───────────────────────▼─────────────────────────────┐  │
│  │       Data Layer (database.py - 220 lines)           │  │
│  │                                                       │  │
│  │  SQLAlchemy ORM Models:                              │  │
│  │  • JiraIssue          • Scorecard                    │  │
│  │  • IssueTransition    • ChatMessage                  │  │
│  │  • MetricCalculation  • KnowledgeDocument            │  │
│  │  • Insight                                           │  │
│  │                                                       │  │
│  │  • Session management with get_db()                  │  │
│  │  • Relationships between models                      │  │
│  └───────────────────────┬─────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ SQLAlchemy ORM
                          │
         ┌────────────────▼─────────────────┐
         │     SQLite Database              │
         │  evaluation_coach.db             │
         │                                  │
         │  8 tables with relationships     │
         └──────────────────────────────────┘
```

### Technology Stack

**Frontend**
- HTML5, CSS3, JavaScript (ES6+)
- No framework dependencies
- Native Fetch API for HTTP requests
- Telia purple design system

**Backend**
- FastAPI 0.115.0+ (Python 3.13)
- SQLAlchemy 2.0.45 (ORM)
- Pydantic 2.11.1 (validation)
- Uvicorn 0.38.0 (ASGI server)

**Database**
- SQLite 3 (embedded)
- File-based storage
- Auto-migration via ORM

---

## 2. Target Architecture (Phases 1-9)

### Future Multi-Node Agent System

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EVALUATION COACH                             │
│                      Multi-Node Agent System                         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
        ┌───────────▼──────────┐      ┌──────────▼──────────┐
        │   Frontend Layer     │      │   Knowledge Base    │
        │   (HTML/JS/CSS)      │      │   (RAG Sources)     │
        └───────────┬──────────┘      └──────────┬──────────┘
                    │                             │
                    │     ┌───────────────────────┤
                    │     │                       │
        ┌───────────▼─────▼───────────────────────▼──────────┐
        │           LangGraph Agent Orchestrator              │
        │                                                      │
        │  ┌────────────────────────────────────────────┐   │
        │  │  1. Data Collector Node                    │   │
        │  │     • Jira API Integration                 │   │
        │  │     • Data Normalization                   │   │
        │  │     • Caching & Persistence                │   │
        │  └──────────────┬─────────────────────────────┘   │
        │                 │                                   │
        │  ┌──────────────▼─────────────────────────────┐   │
        │  │  2. Metrics Engine Node                    │   │
        │  │     • Lead/Cycle Time Calculation          │   │
        │  │     • Predictability Analysis              │   │
        │  │     • Flow Metrics (WIP, Throughput)       │   │
        │  │     • Trend Detection                      │   │
        │  └──────────────┬─────────────────────────────┘   │
        │                 │                                   │
        │  ┌──────────────▼─────────────────────────────┐   │
        │  │  3. Pattern Detection Node                 │   │
        │  │     • Anomaly Detection                    │   │
        │  │     • Bottleneck Identification            │   │
        │  │     • Scope Change Analysis                │   │
        │  │     • Dependency Impact Analysis           │   │
        │  └──────────────┬─────────────────────────────┘   │
        │                 │                                   │
        │  ┌──────────────▼─────────────────────────────┐   │
        │  │  4. Knowledge Retrieval Node (RAG)         │   │
        │  │     • Vector Store (Chroma/FAISS)          │   │
        │  │     • SAFe Principles                      │   │
        │  │     • Agile Best Practices                 │   │
        │  │     • Flow Metrics Knowledge               │   │
        │  └──────────────┬─────────────────────────────┘   │
        │                 │                                   │
        │  ┌──────────────▼─────────────────────────────┐   │
        │  │  5. Reasoning & Coaching Node              │   │
        │  │     • Context Synthesis                    │   │
        │  │     • Root Cause Analysis                  │   │
        │  │     • Improvement Proposal Generation      │   │
        │  │     • Priority Ranking                     │   │
        │  └──────────────┬─────────────────────────────┘   │
        │                 │                                   │
        │  ┌──────────────▼─────────────────────────────┐   │
        │  │  6. Explanation Generator Node             │   │
        │  │     • Human-Readable Output                │   │
        │  │     • Evidence Tracing                     │   │
        │  │     • Multi-Level Summaries                │   │
        │  └────────────────────────────────────────────┘   │
        │                                                      │
        └──────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┴────────────────────────┐
        │                                                     │
┌───────▼────────┐          ┌──────────▼─────────┐  ┌───────▼────────┐
│  Jira REST API │          │  Local Data Store  │  │  Config Store  │
│  (External)    │          │  (Cache/History)   │  │  (YAML/JSON)   │
└────────────────┘          └────────────────────┘  └────────────────┘
```

## 2. Core Design Principles

### Separation of Concerns
- **Data Layer**: Jira integration and data persistence
- **Analytics Layer**: Metric calculation and pattern detection
- **Intelligence Layer**: RAG-based reasoning and coaching
- **Presentation Layer**: Web UI and visualization

### Modularity
- Each node is independently testable
- Pluggable metric calculators
- Extensible knowledge sources
- Configurable analysis scopes

### Explainability
- Every insight traces back to source data
- Metric calculations are transparent
- Coaching rationale is explicit
- Evidence is always provided

### Non-Blame Culture
- Focus on system capabilities, not individual performance
- Distinguish between capacity, capability, and process issues
- Promote flow-based thinking
- Encourage sustainable improvement

## 3. Data Flow

```
Jira API → Data Collector → Normalized Models → Metrics Engine
                                    ↓
                            Pattern Detection ← Knowledge Base (RAG)
                                    ↓
                            Reasoning & Coaching
                                    ↓
                            Explanation Generator
                                    ↓
                            Frontend Visualization
```

## 4. Scoping Model

The system operates at three hierarchical levels:

```
Portfolio Level
    ├── ART 1
    │   ├── Team A
    │   ├── Team B
    │   └── Team C
    ├── ART 2
    │   ├── Team D
    │   └── Team E
    └── ART 3
        └── Team F
```

**Analysis Scope:**
- Portfolio: Strategic alignment, cross-ART dependencies, investment themes
- ART: PI predictability, feature delivery, cross-team flow
- Team: Sprint metrics, WIP, lead time, team health

## 5. Key Metrics Framework

### Flow Metrics
- **Throughput**: Items completed per time period
- **WIP**: Work in progress at any point
- **Lead Time**: Idea to production
- **Cycle Time**: Start to finish

### Predictability Metrics
- **Commitment Reliability**: Planned vs. Delivered
- **Scope Change Rate**: Mid-sprint/PI additions
- **Velocity Stability**: Trend and variance

### Quality & Health Metrics
- **Flow Efficiency**: Value-add time vs. wait time
- **Blocked Time**: Duration and frequency
- **Dependency Impact**: Cross-team blocking

## 6. Technology Stack Details

### Backend
- **Python 3.11+**: Core runtime
- **LangChain**: RAG framework
- **LangGraph**: Agent orchestration
- **Pydantic**: Data validation
- **httpx**: Async HTTP client for Jira
- **pandas**: Data manipulation
- **numpy**: Statistical analysis
- **chromadb/faiss**: Vector storage

### Frontend
- **HTML5/CSS3**: Structure and styling
- **Vanilla JavaScript**: Interactivity
- **Chart.js / D3.js**: Visualizations
- **Fetch API**: Backend communication

### Infrastructure
- **SQLite/PostgreSQL**: Local data persistence
- **YAML**: Configuration files
- **JSON**: API communication

## 7. Extension Points

### Pluggable Metrics
```python
class MetricCalculator(Protocol):
    def calculate(self, data: AnalysisData) -> MetricResult:
        ...
```

### Knowledge Sources
```python
class KnowledgeSource(Protocol):
    def retrieve(self, query: str) -> List[Document]:
        ...
```

### Analysis Modules
```python
class AnalysisModule(Protocol):
    def analyze(self, metrics: MetricsSnapshot) -> AnalysisResult:
        ...
```

## 8. Security & Privacy Considerations

- Jira credentials stored securely (environment variables)
- No sensitive data in logs
- Configurable data retention policies
- Anonymization options for team names

## 9. Deployment Model

**Phase 1: Local Development**
- Run as local Python application
- SQLite for persistence
- VS Code for development

**Phase 2: Team Deployment**
- Docker containerization
- Shared PostgreSQL instance
- Web-accessible UI

**Phase 3: Enterprise**
- Cloud deployment (AWS/Azure/GCP)
- SSO integration
- Multi-tenant support
