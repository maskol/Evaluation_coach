# Evaluation Coach - Project Structure

## Folder Organization

```
Evaluation_coach/
├── backend/
│   ├── __init__.py
│   ├── main.py                      # Application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # Configuration management
│   │   └── jira_config.yaml         # Jira connection settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── jira_models.py           # Jira data models
│   │   ├── metrics_models.py        # Metrics data structures
│   │   ├── analysis_models.py       # Analysis results
│   │   └── coaching_models.py       # Coaching output models
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── graph.py                 # LangGraph workflow definition
│   │   ├── state.py                 # Agent state management
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── data_collector.py    # Node 1: Data collection
│   │       ├── metrics_engine.py    # Node 2: Metrics calculation
│   │       ├── pattern_detector.py  # Node 3: Pattern detection
│   │       ├── knowledge_retriever.py # Node 4: RAG retrieval
│   │       ├── coach.py             # Node 5: Reasoning & coaching
│   │       └── explainer.py         # Node 6: Explanation generation
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── jira_client.py           # Jira REST API client
│   │   ├── jira_query_builder.py    # JQL query construction
│   │   └── data_normalizer.py       # Data transformation
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── metrics/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Base metric calculator
│   │   │   ├── flow_metrics.py      # Throughput, WIP, lead time
│   │   │   ├── predictability.py    # Commitment reliability
│   │   │   ├── quality_metrics.py   # Flow efficiency, blocked time
│   │   │   └── team_metrics.py      # Team-specific metrics
│   │   └── analyzers/
│   │       ├── __init__.py
│   │       ├── base.py              # Base analyzer
│   │       ├── trend_analyzer.py    # Time-series trends
│   │       ├── anomaly_detector.py  # Statistical anomalies
│   │       ├── bottleneck_finder.py # Flow bottlenecks
│   │       └── dependency_analyzer.py # Cross-team dependencies
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── rag_engine.py            # RAG orchestration
│   │   ├── vector_store.py          # Vector DB interface
│   │   ├── embeddings.py            # Embedding generation
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── safe_principles.md   # SAFe knowledge base
│   │       ├── agile_practices.md   # Agile coaching
│   │       ├── flow_metrics.md      # Flow-based metrics
│   │       └── playbooks.md         # Improvement playbooks
│   ├── coaching/
│   │   ├── __init__.py
│   │   ├── reasoner.py              # Root cause reasoning
│   │   ├── proposal_generator.py    # Improvement proposals
│   │   ├── prioritizer.py           # Priority ranking
│   │   └── templates/
│   │       ├── portfolio_report.py  # Portfolio-level output
│   │       ├── art_report.py        # ART-level output
│   │       └── team_report.py       # Team-level output
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py              # Database connection
│   │   ├── cache.py                 # Caching layer
│   │   └── migrations/              # Database migrations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py                # FastAPI/Flask server
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py          # Analysis endpoints
│   │   │   ├── metrics.py           # Metrics endpoints
│   │   │   └── reports.py           # Report endpoints
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── requests.py          # API request models
│   │       └── responses.py         # API response models
│   └── utils/
│       ├── __init__.py
│       ├── logging.py               # Logging configuration
│       ├── exceptions.py            # Custom exceptions
│       └── helpers.py               # Utility functions
│
├── frontend/
│   ├── index.html                   # Main HTML page
│   ├── css/
│   │   ├── main.css                 # Main styles
│   │   ├── components.css           # Component styles
│   │   └── visualizations.css       # Chart styles
│   ├── js/
│   │   ├── app.js                   # Main application
│   │   ├── api-client.js            # Backend API client
│   │   ├── components/
│   │   │   ├── dashboard.js         # Dashboard component
│   │   │   ├── metrics-view.js      # Metrics display
│   │   │   ├── insights-view.js     # Insights display
│   │   │   └── recommendations.js   # Recommendations
│   │   └── visualizations/
│   │       ├── charts.js            # Chart.js wrappers
│   │       ├── flow-diagram.js      # Flow visualizations
│   │       └── trend-charts.js      # Trend visualizations
│   └── assets/
│       ├── images/                  # Images and icons
│       └── fonts/                   # Custom fonts
│
├── data/
│   ├── cache/                       # Cached Jira data
│   ├── vector_store/                # Vector database files
│   └── exports/                     # Generated reports
│
├── docs/
│   ├── ARCHITECTURE.md              # System architecture
│   ├── STRUCTURE.md                 # This file
│   ├── DEVELOPMENT_ROADMAP.md       # Development plan
│   ├── API.md                       # API documentation
│   ├── METRICS_GUIDE.md             # Metrics definitions
│   └── DEPLOYMENT.md                # Deployment guide
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration
│   ├── unit/
│   │   ├── test_metrics.py
│   │   ├── test_analyzers.py
│   │   └── test_jira_client.py
│   ├── integration/
│   │   ├── test_agent_workflow.py
│   │   ├── test_rag_engine.py
│   │   └── test_api.py
│   └── fixtures/
│       ├── sample_jira_data.json
│       └── sample_metrics.json
│
├── scripts/
│   ├── setup_knowledge_base.py      # Initialize RAG sources
│   ├── setup_database.py            # Initialize database
│   └── run_analysis.py              # CLI analysis runner
│
├── .env.example                     # Environment variables template
├── .gitignore
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Python project config
├── README.md                        # Project overview
└── LICENSE

```

## Module Responsibilities

### Backend Modules

#### `config/`
- Manages application configuration
- Loads Jira credentials and connection settings
- Provides environment-specific configurations

#### `models/`
- Defines Pydantic models for type safety
- Ensures data validation across the system
- Provides clear contracts between modules

#### `agents/`
- Orchestrates the LangGraph multi-node workflow
- Manages agent state transitions
- Coordinates execution across nodes

#### `integrations/`
- Handles external system integration (primarily Jira)
- Abstracts API complexity
- Normalizes external data formats

#### `analytics/`
- Computes all metrics (flow, predictability, quality)
- Performs statistical analysis
- Detects patterns and anomalies
- **Key principle**: Metrics are facts, not interpretations

#### `knowledge/`
- Implements RAG (Retrieval-Augmented Generation)
- Manages vector store and embeddings
- Retrieves relevant coaching knowledge

#### `coaching/`
- Performs reasoning over metrics + knowledge
- Generates improvement proposals
- Prioritizes recommendations
- **Key principle**: System thinking, not blame

#### `storage/`
- Manages data persistence
- Implements caching strategies
- Handles database migrations

#### `api/`
- Exposes REST API for frontend
- Handles request/response validation
- Manages API versioning

### Frontend Modules

#### `components/`
- Reusable UI components
- Dashboard, metrics views, insights
- Modular and composable

#### `visualizations/`
- Chart rendering
- Interactive visualizations
- Drill-down capabilities

## Key Design Patterns

### 1. Strategy Pattern (Metrics)
Different metric calculators implement a common interface:
```python
class MetricCalculator(Protocol):
    def calculate(self, data: AnalysisData) -> MetricResult:
        ...
```

### 2. Chain of Responsibility (Analyzers)
Analyzers process data sequentially or in parallel:
```python
class Analyzer(Protocol):
    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        ...
```

### 3. Repository Pattern (Data Access)
Abstract data access behind repositories:
```python
class JiraRepository:
    def get_issues(self, query: JQLQuery) -> List[Issue]:
        ...
```

### 4. Factory Pattern (Report Generation)
Create different report types:
```python
class ReportFactory:
    def create_report(self, scope: Scope) -> Report:
        ...
```

## Dependency Flow

```
Frontend (JS)
    ↓
API Layer (FastAPI/Flask)
    ↓
Agent Graph (LangGraph)
    ↓
Node Implementations
    ↓
Analytics & Knowledge Modules
    ↓
Storage & Integration Layers
```

## Testing Strategy

- **Unit Tests**: Each module independently
- **Integration Tests**: Node interactions, API endpoints
- **End-to-End Tests**: Complete analysis workflows
- **Fixtures**: Realistic Jira data samples

## Configuration Management

- **Environment Variables**: Secrets (API keys, credentials)
- **YAML Files**: Application configuration
- **Code**: Default values and constants
