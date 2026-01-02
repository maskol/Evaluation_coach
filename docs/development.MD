# Evaluation Coach - Development Guide

**Full-Stack Implementation Complete!**

*Last Updated: 2 January 2026*

---

## ✅ Phase 0: COMPLETE

### What's Been Built

#### Backend (FastAPI + SQLAlchemy)
- **API Server**: 20+ REST endpoints on port 8850
- **Database**: SQLite with 8 tables (ORM models)
- **Services**: LLM, Metrics, and Insights services
- **Documentation**: Auto-generated Swagger UI at `/docs`

#### Frontend (HTML5 + JavaScript)
- **Interactive GUI**: 4 tabs (Dashboard, Chat, Insights, Metrics)
- **Design System**: Telia purple with Apple-inspired aesthetics
- **API Integration**: Full REST API communication
- **Demo Mode**: Fallback mode with mock data

#### Files Created
```
backend/
├── main.py (479 lines)          # FastAPI app with 20+ endpoints
├── database.py (220 lines)       # SQLAlchemy ORM models
├── api_models.py (200+ lines)    # Pydantic schemas
└── services/
    ├── llm_service.py (130 lines)
    ├── metrics_service.py (163 lines)
    └── insights_service.py (228 lines)

frontend/
├── index.html (650+ lines)       # Main GUI
├── app.js (450+ lines)           # Application logic
└── styles.css                     # Telia design system

Total: ~2,500 lines of production code
```

---

## 🎯 You're Now Ready for Phase 1 Development

### Phase 1: Jira Integration (Weeks 3-4)

**Goal**: Connect to real Jira instances and fetch data

#### Tasks
1. **Jira REST API Client** (`backend/integrations/jira_client.py`)
   - Authentication (Basic Auth, OAuth 2.0, PAT)
   - Issue search with JQL
   - Changelog retrieval
   - Custom field mapping
   - Rate limiting & retry logic

2. **Data Ingestion Pipeline**
   - Incremental sync strategy
   - Transform Jira JSON to database models
   - Handle missing/invalid data
   - Update tracking

3. **Caching Layer**
   - TTL-based cache management
   - Cache invalidation strategy
   - Query optimization

4. **Data Quality Module**
   - Missing field detection
   - Data consistency checks
   - Quality score calculation

#### Success Criteria
- [ ] Fetch issues from real Jira instance
- [ ] Store issues in database
- [ ] Handle incremental updates
- [ ] Pass data quality checks (>90% complete data)
- [ ] Sub-second response for cached queries

#### Implementation Example
```python
# backend/integrations/jira_client.py
from jira import JIRA

class JiraClient:
    def __init__(self, url, username, api_token):
        self.jira = JIRA(server=url, basic_auth=(username, api_token))
    
    def fetch_issues(self, jql: str, max_results: int = 1000):
        issues = []
        start_at = 0
        while True:
            batch = self.jira.search_issues(
                jql, 
                startAt=start_at, 
                maxResults=100,
                expand='changelog'
            )
            if not batch:
                break
            issues.extend(batch)
            start_at += len(batch)
            if len(issues) >= max_results:
                break
        return issues
```

---

## 📝 Development Workflow

### Running the Application

**Start Backend** (Terminal 1):
```bash
./start_backend.sh
# Backend runs on http://localhost:8850
```

**Start Frontend** (Terminal 2):
```bash
cd frontend
python3 -m http.server 8800
# Frontend runs on http://localhost:8800
```

**Access Application**:
- Frontend: http://localhost:8800
- API Docs: http://localhost:8850/docs
- Health Check: http://localhost:8850/api/health

### Testing Endpoints

```bash
# Health check
curl http://localhost:8850/api/health

# Dashboard data
curl http://localhost:8850/api/v1/dashboard

# Generate scorecard
curl -X POST http://localhost:8850/api/v1/scorecard \
  -H "Content-Type: application/json" \
  -d '{"scope": "portfolio", "time_range": "last_pi"}'

# Generate insights
curl -X POST http://localhost:8850/api/v1/insights/generate \
  -H "Content-Type: application/json" \
  -d '{"scope": "art", "scope_id": "Platform-Engineering"}'

# Chat with AI coach
curl -X POST http://localhost:8850/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is our flow efficiency?", "session_id": "test-123"}'
```

### Database Management

```bash
# Initialize database
python backend/database.py

# Access database
sqlite3 backend/evaluation_coach.db

# Useful queries
.tables                                    # List all tables
SELECT * FROM jira_issues LIMIT 5;         # View issues
SELECT * FROM insights ORDER BY created_at DESC;  # Recent insights
```

---

## 🔧 Adding New Features

### Adding a New API Endpoint

**Edit `backend/main.py`**:
```python
@app.get("/api/v1/my-endpoint")
async def my_endpoint(db: Session = Depends(get_db)):
    # Your logic here
    return {"status": "success"}
```

### Adding a New Service Method

**Edit appropriate service file**:
```python
# backend/services/metrics_service.py
class MetricsService:
    def calculate_new_metric(self, data):
        # Your calculation
        return result
```

### Adding a New Database Table

**Edit `backend/database.py`**:
```python
class NewTable(Base):
    __tablename__ = "new_table"
    id = Column(Integer, primary_key=True)
    # Your columns
```

**Re-initialize database**:
```bash
python backend/database.py
```

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8850 is in use
lsof -i :8850

# Kill process if needed
kill -9 <PID>

# Check for syntax errors
python -m py_compile backend/main.py
```

### Frontend Can't Connect to Backend
- Verify backend is running: `curl http://localhost:8850/api/health`
- Check CORS settings in `backend/main.py`
- Check API_BASE_URL in `frontend/app.js`

### Database Errors
```bash
# Delete and recreate database
rm backend/evaluation_coach.db
python backend/database.py
```

---

## 📚 Key Resources

### Documentation
- [README.md](../README.md) - Project overview and quick start
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) - Current status and features
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
- [METRICS_GUIDE.md](./METRICS_GUIDE.md) - Metric definitions
- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) - 20-week plan

### API Documentation
- Swagger UI: http://localhost:8850/docs
- ReDoc: http://localhost:8850/redoc

### Code Structure
- Backend services: `backend/services/`
- API models: `backend/api_models.py`
- Database models: `backend/database.py`
- Frontend logic: `frontend/app.js`

---

## ✅ Next Steps for Development

1. **Set up Jira test instance** (or use existing)
2. **Create `.env` file** with Jira credentials
3. **Implement `JiraClient`** in `backend/integrations/jira_client.py`
4. **Test issue fetching** with sample JQL queries
5. **Implement data transformation** to database models
6. **Update `/jira/sync` endpoint** in `main.py`
7. **Test with frontend** - click "Sync with Jira" button

**You're ready to begin Phase 1 implementation!** 🚀