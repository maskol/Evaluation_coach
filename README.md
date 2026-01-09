# Evaluation Coach

**An AI-Powered Agile Analytics & Coaching System**

The Evaluation Coach is an intelligent agent that analyzes Jira execution data across Portfolio, Agile Release Train (ART), and Team scopes to provide evidence-based insights and improvement recommendations.

## 🎯 Purpose

- **Analyze** planned vs actual execution across Portfolio/ART/Team levels with 15+ metrics
- **Detect** systemic delivery issues using flow metrics, pattern detection, and SAFe-aligned scorecards
- **Provide** explainable, evidence-based improvement proposals grounded in Agile/SAFe/Lean principles
- **Coach** leaders and teams with actionable, data-driven recommendations following a 5-part transparency template
- **Track** improvement actions with measurable success criteria

## 🌟 What Makes This Special

- **System-Level Coaching**: Focuses on process, not people. Non-blame culture.
- **Evidence-Based**: Every insight links to specific Jira data with confidence scores.
- **Transparent Reasoning**: 5-part explainable insight template (Observation → Interpretation → Root Causes → Actions → Expected Outcome).
- **Metadata-Driven RAG**: Structured knowledge base with 25+ documents, filtered by scope/metric/pattern.
- **Multi-Scope Analysis**: Works at Team, ART, or Portfolio level with appropriate metrics.
- **Executive-Safe**: Clear explanations, scorecards, and health metrics suitable for all levels.

## 🏗️ Architecture

The Evaluation Coach is built as a **multi-node LangGraph agent** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                   LANGGRAPH WORKFLOW                        │
│                                                             │
│  1. Data Collector → Jira API → Normalized Data            │
│          ↓                                                  │
│  2. Metrics Engine → Flow, Predictability, Quality Metrics │
│          ↓                                                  │
│  3. Pattern Detector → Bottlenecks, Anomalies, Trends      │
│          ↓                                                  │
│  4. Knowledge Retriever (RAG) → SAFe, Agile, Flow Metrics  │
│          ↓                                                  │
│  5. Coaching Node → Insights + Improvement Proposals        │
│          ↓                                                  │
│  6. Explainer → Human-Readable Report                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+ (tested with 3.13.0)
- Jira Cloud/Server instance with API access (optional for demo mode)
- OpenAI API key (optional - for LLM-based reasoning)

### Installation

```bash
# Clone the repository
cd Evaluation_coach

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python backend/database.py

# Set up environment variables (optional)
cp .env.example .env
# Edit .env with your Jira credentials and OpenAI API key
```

### Configuration

**Database**: SQLite database is automatically created at `backend/evaluation_coach.db`

**Ports**:
- Frontend: http://localhost:8800
- Backend API: http://localhost:8850

Create a `.env` file (optional for future Jira/LLM integration):

```env
# Jira Configuration (coming in Phase 1)
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token

# OpenAI Configuration (coming in Phase 4)
OPENAI_API_KEY=your-openai-api-key

# Database (auto-configured)
DATABASE_URL=sqlite:///./evaluation_coach.db
```

### Running the Application

**Start Backend Server** (Terminal 1):
```bash
./start_backend.sh
# Or manually:
cd backend
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8850
```

**Start Frontend Server** (Terminal 2):
```bash
cd frontend
python3 -m http.server 8800
```

**Access the Application**:
- Open http://localhost:8800 in your browser
- The frontend will automatically connect to the backend API

### Testing the API

```bash
# Check backend health
curl http://localhost:8850/api/health

# Get dashboard data (demo mode)
curl http://localhost:8850/api/v1/dashboard

# Generate a scorecard
curl -X POST http://localhost:8850/api/v1/scorecard \
  -H "Content-Type: application/json" \
  -d '{"scope": "portfolio", "time_range": "last_pi"}'
```

## 📊 Core Capabilities

### 1. Comprehensive Metric Catalog

**15+ Metrics Across 4 Categories** (see [METRICS_GUIDE.md](docs/METRICS_GUIDE.md))

**Flow & Delivery**
- Lead Time (Created → Done) - P50/P85/P95
- Cycle Time (In Progress → Done)
- Throughput (items completed/time)
- Work In Progress (WIP) with daily sampling
- Flow Efficiency (active time / total time)
- Blocked Time (time in blocked states)

**Predictability & Planning**
- Planned vs Done ratio
- Commitment Reliability (% committed items completed)
- PI Predictability (SAFe - % objectives met)
- Scope Change Rate (mid-execution changes)
- Spillover Rate (incomplete carried work)
- Estimation Accuracy

**Quality & Sustainability**
- Defect Injection Rate (bugs per feature)
- Escaped Defects (bugs after release)
- Rework Ratio (bugs / total items)
- Team Load Index (WIP per person - target: ≤1.5)
- Team Stability (membership change)

**Structural & Dependencies**
- Cross-Team Dependencies (linked issues)
- Blocker Density (% items blocked)
- Handovers (status ownership changes)
- External Wait Time (waiting on other ARTs/vendors)

### 2. SAFe-Aligned Health Scorecards

**Three-Level Assessment** (see [SCORECARD_FRAMEWORK.md](docs/SCORECARD_FRAMEWORK.md))

**Portfolio Level** (5 dimensions)
- Strategic Predictability (epic completion, ART predictability)
- Flow Efficiency (lead times, WIP, cross-ART dependencies)
- Economic WIP (concurrent epics, blocked time)
- Value Realization (features delivered vs planned)
- Systemic Bottlenecks (repeating constraints)

**ART Level** (5 dimensions)
- PI Predictability (objectives met, planned vs delivered)
- Dependency Health (blocked time, cross-team dependencies)
- Flow Distribution (Features 70% / Enablers 20% / Defects 10%)
- Load Balance (team throughput variance)
- Quality Trend (defect rates, rework)

**Team Level** (5 dimensions)
- Sprint Reliability (commitment reliability, scope change)
- Flow Efficiency (cycle time, wait time)
- WIP Discipline (WIP per person, limit adherence)
- Quality (defect injection, bug fix time, rework)
- Team Stability (churn, tenure)

### 3. AI-Generated Insights

**Little's Law Analysis** (see [LITTLES_LAW_INSIGHT.md](docs/LITTLES_LAW_INSIGHT.md))

Automatic PI-level analysis using Little's Law (L = λ × W) to optimize WIP and flow:
- **Throughput Analysis**: Features delivered per day
- **Lead Time Optimization**: Identify gaps between current and target (30 days)
- **WIP Recommendations**: Calculate optimal work-in-progress levels
- **Flow Efficiency**: Measure active work vs. wait time percentage
- **Actionable Targets**: Specific WIP limits and improvement actions

**Data Source**: Real-time flow metrics from `flow_leadtime` API (DL Webb App integration)

### 4. Explainable Insights with 5-Part Template

**Every Insight Follows This Structure** (see [EXPLAINABLE_INSIGHTS.md](docs/EXPLAINABLE_INSIGHTS.md))

1. **Metric Observation**: What was measured, value, comparison, data source, confidence
2. **Interpretation**: What this indicates, why it matters, impact assessment
3. **Likely Root Causes**: Evidence-backed causes with confidence levels
4. **Recommended Actions**: Short/medium/long term actions with owners, effort, success signals
5. **Expected Outcome**: Metrics to watch, timeline, leading/lagging indicators, risks

### 5. Metadata-Driven Knowledge Retrieval (RAG)

**Structured Knowledge Base** (see [RAG_KNOWLEDGE_STRUCTURE.md](docs/RAG_KNOWLEDGE_STRUCTURE.md))

- **25+ Documents** across 6 domains (agile_principles, SAFe, coaching_patterns, metrics_interpretation, improvement_playbooks, case_studies)
- **YAML Metadata** for precise filtering (scope, metrics, symptoms, confidence)
- **Hybrid Search**: Combines keyword (BM25) + semantic (vector embeddings)
- **Context-Aware**: Retrieves knowledge relevant to detected patterns

### 6. Pattern Detection

- **Bottlenecks**: Identifies where work gets stuck
- **Anomalies**: Detects statistical outliers
- **Trends**: Tracks metric changes over time
- **Dependencies**: Analyzes cross-team blocking

### Coaching Philosophy

The Evaluation Coach adheres to these principles:

1. **System Thinking**: Focus on systemic issues, not individual blame
2. **Data-Driven**: Every insight links back to evidence
3. **Actionable**: Recommendations are specific and implementable
4. **Explainable**: Complete reasoning chain provided
5. **Contextual**: Uses RAG to apply relevant Agile/SAFe knowledge

## 📁 Project Structure

```
Evaluation_coach/
├── backend/
│   ├── main.py              # FastAPI application (479 lines, 20+ endpoints)
│   ├── database.py          # SQLAlchemy ORM models (8 tables)
│   ├── api_models.py        # Pydantic request/response schemas
│   ├── services/            # Business logic layer
│   │   ├── llm_service.py   # AI coaching responses
│   │   ├── metrics_service.py  # Scorecard & metrics calculation
│   │   └── insights_service.py # Insight generation
│   ├── integrations/        # External API clients (future)
│   ├── analytics/           # Metrics & analyzers (future)
│   ├── knowledge/           # RAG engine (future)
│   └── evaluation_coach.db  # SQLite database
├── frontend/
│   ├── index.html           # Main GUI (650+ lines, 4 tabs)
│   ├── app.js               # Frontend logic (450+ lines)
│   └── styles.css           # Telia purple design system
├── data/                    # Cache & vector store (future)
├── docs/                    # Comprehensive documentation (10+ files)
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies (40+ packages)
├── start_backend.sh         # Backend startup script
└── README.md                # This file
```

See [docs/STRUCTURE.md](docs/STRUCTURE.md) for detailed structure.

## 📖 Documentation

### Core Documentation
- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) - System architecture and design principles
- [**STRUCTURE.md**](docs/STRUCTURE.md) - Folder structure and module responsibilities
- [**DEVELOPMENT_ROADMAP.md**](docs/DEVELOPMENT_ROADMAP.md) - 20-week phased development plan

### Design Specifications (✨ NEW)
- [**METRICS_GUIDE.md**](docs/METRICS_GUIDE.md) - Complete metric catalog with formulas and benchmarks
- [**SCORECARD_FRAMEWORK.md**](docs/SCORECARD_FRAMEWORK.md) - Portfolio/ART/Team health assessment
- [**RAG_KNOWLEDGE_STRUCTURE.md**](docs/RAG_KNOWLEDGE_STRUCTURE.md) - Metadata-driven knowledge base
- [**EXPLAINABLE_INSIGHTS.md**](docs/EXPLAINABLE_INSIGHTS.md) - 5-part transparency template
- [**UI_BLUEPRINT.md**](docs/UI_BLUEPRINT.md) - Frontend components and API specification
- [**DESIGN_ENHANCEMENTS.md**](docs/DESIGN_ENHANCEMENTS.md) - Summary of design v2.0

### Implementation Documentation
- [**SUMMARY.md**](docs/SUMMARY.md) - Phase 0 deliverables summary
- [**API.md**](docs/API.md) - REST API documentation *(coming in Phase 7)*

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run example demonstrations
python -m backend.coaching.example_report
python -m backend.analytics.metrics.flow_metrics
```

## 🔧 Development

### Current Status

**Phase 0: Foundation (✅ Complete - Enhanced with Full-Stack Implementation)**

*Design & Architecture (4,250+ lines of documentation):*
- System architecture designed
- Core data models defined (863 lines)
- LangGraph workflow created
- Comprehensive metric catalog (15+ metrics)
- SAFe-aligned scorecard framework (Portfolio/ART/Team)
- RAG knowledge structure with metadata schema
- 5-part explainable insight template
- Complete UI/API blueprint

*Full-Stack Implementation (COMPLETED ✅):*
- **Backend API** (FastAPI, 479 lines, 20+ endpoints)
  - Health check, dashboard, scorecard generation
  - Insights generation and feedback
  - Chat interface with session management
  - Metrics retrieval and Jira sync endpoints
- **Database Layer** (SQLAlchemy ORM, 8 tables)
  - JiraIssue, IssueTransition, MetricCalculation
  - Insight, Scorecard, ChatMessage, KnowledgeDocument
- **Service Layer** (3 service classes, 540+ lines)
  - LLMService: Keyword-based routing (ready for LLM integration)
  - MetricsService: Scorecard generation with demo data
  - InsightsService: 5-part insight generation
- **Frontend GUI** (HTML5 + JavaScript, 1,100+ lines)
  - 4 main tabs: Dashboard, Chat, Insights, Metrics
  - Interactive scorecard display and ART comparison
  - AI coach chat interface with context awareness
  - Detailed insight cards with acceptance/dismissal
  - Metrics catalog with formulas and benchmarks
  - Telia purple design system (Apple-inspired)
- **API Integration**
  - Frontend communicates with backend via REST API
  - Fallback demo mode when backend unavailable
  - Session management for chat continuity

**Next: Phase 1 - Data Ingestion (Weeks 3-4)**
- [ ] Complete Jira REST API client with all endpoints
- [ ] Implement authentication (Basic Auth, OAuth, PAT)
- [ ] Add retry logic and rate limiting
- [ ] Create caching layer with TTL management
- [ ] Build data quality assessment module
- [ ] Implement incremental sync strategy

**Phase 2: Metrics Engine (Weeks 5-7)** - Replace demo data with real calculations
- [ ] Flow metrics: Lead time, cycle time, WIP, throughput
- [ ] Predictability metrics: Commitment reliability, PI predictability
- [ ] Quality metrics: Defect injection, rework ratio
- [ ] Team stability metrics

**Phase 3-9**: See [DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md) for complete 20-week plan

### Code Quality

```bash
# Format code
black backend/ tests/

# Lint code
ruff check backend/ tests/

# Type check
mypy backend/
```

## 🤝 Contributing

This is currently an internal project. For questions or suggestions, contact the development team.

### Extending the System

The Evaluation Coach is designed for extensibility:

**Custom Metrics**
```python
from backend.analytics.metrics.base import MetricCalculator

class MyMetric(MetricCalculator):
    def calculate(self, data):
        # Your logic
        pass
```

**Custom Knowledge Sources**
```python
from backend.knowledge.sources.base import KnowledgeSource

class MyKnowledge(KnowledgeSource):
    def retrieve(self, query):
        # Your logic
        pass
```

See [DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md#extension-points-for-customization) for more.

## 📜 License

Copyright © 2026. All rights reserved.

## 🙏 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/) for agent orchestration
- [FastAPI](https://fastapi.tiangolo.com/) for REST API
- [Pydantic](https://docs.pydantic.dev/) for data validation
- Inspired by "Actionable Agile Metrics" (Daniel Vacanti) and SAFe principles

## 📞 Support

For issues, questions, or feature requests, please contact the development team.

---

**Built with ❤️ by engineers who believe in data-driven continuous improvement.**
