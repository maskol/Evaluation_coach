# Data Sources Configuration

## Current Implementation (Active)

### DL Webb App API - Primary Data Source
**Status**: ✅ **ACTIVE** - All functionality works with this source

The Evaluation Coach currently gets **all data** from the DL Webb App server:

```
URL: http://localhost:8000
Database: SQLite (managed by DL Webb App)
Data: 60,580+ features across 14 ARTs and 24 PIs
```

**Available Data:**
- ✅ Feature lead-time (stage-by-stage breakdown)
- ✅ Planning accuracy (pip_data - committed vs delivered)
- ✅ ARTs, Teams, PIs lists
- ✅ Flow metrics (backlog, analysis, progress, review, etc.)
- ✅ Bottleneck analysis
- ✅ Waste identification
- ✅ Throughput metrics
- ✅ Trend analysis

**Endpoints Used:**
```bash
GET  /api/flow_leadtime          # Feature lead-time data
GET  /api/analysis/leadtime       # Statistical analysis
GET  /api/analysis/planning-accuracy  # Planning metrics
GET  /api/analysis/bottlenecks    # Bottleneck detection
GET  /api/analysis/waste          # Waste analysis
GET  /api/analysis/throughput     # Delivery metrics
GET  /api/analysis/trends         # Time-series trends
GET  /api/analysis/filters        # Available ARTs/PIs/Teams
GET  /api/pip_data                # Planning vs delivery
GET  /api/arts                    # ART list
GET  /api/teams                   # Team list
```

**Configuration:**
```bash
# In .env or settings
LEADTIME_SERVER_URL=http://localhost:8000
LEADTIME_SERVER_ENABLED=true
LEADTIME_SERVER_TIMEOUT=30
```

## Future Integration Options (Not Required)

### Jira via Model Context Protocol (MCP)
**Status**: ⚪ **OPTIONAL** - Not currently needed

Jira integration is available but **NOT required** for current functionality. All data comes from DL Webb App.

**When to Consider Jira:**
- Want to fetch issues directly from Jira Cloud/Server
- Need real-time Jira status updates
- Want to sync Jira comments/attachments
- Need custom field mappings
- Want to create/update Jira issues from Evaluation Coach

**Future MCP Integration:**
The system is designed to support Jira via Model Context Protocol (MCP) when needed:

```python
# Future: Jira MCP Server integration
# This would allow LLM agents to query Jira directly
{
    "mcpServers": {
        "jira": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-jira"],
            "env": {
                "JIRA_URL": "https://your-company.atlassian.net",
                "JIRA_EMAIL": "your-email@company.com",
                "JIRA_API_TOKEN": "your-token"
            }
        }
    }
}
```

**Jira Client Code:**
The `backend/integrations/jira_client.py` exists but is **not currently used**. It's there for future integration if needed.

## Why This Design Works

### Single Source of Truth
- **DL Webb App** already has all your Jira data
- No need to duplicate API calls
- Faster responses (local SQLite vs REST API)
- Reduced external dependencies

### Future Flexibility
- Jira integration can be added anytime
- No code changes needed to core functionality
- MCP makes integration seamless
- Both sources can coexist

### Current Workflow

```
1. Jira → DL Webb App (Your existing process)
2. DL Webb App → SQLite Database
3. Evaluation Coach → DL Webb App API
4. Dashboard/Metrics/Insights → Real Data
```

## Configuration Examples

### Current Setup (.env)
```bash
# Required - Lead-Time Server
LEADTIME_SERVER_URL=http://localhost:8000
LEADTIME_SERVER_ENABLED=true
LEADTIME_SERVER_TIMEOUT=30

# Required - LLM
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Optional - Jira (not used currently)
# JIRA_BASE_URL=https://your-company.atlassian.net
# JIRA_EMAIL=your-email@company.com
# JIRA_API_TOKEN=your-token

# Database
DATABASE_URL=sqlite:///./evaluation_coach.db
```

### Future with Jira (.env)
```bash
# Lead-Time Server (still primary)
LEADTIME_SERVER_URL=http://localhost:8000
LEADTIME_SERVER_ENABLED=true

# Jira (optional additional source)
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-token
JIRA_ENABLED=true

# The system would check both sources
# and use whichever is available/appropriate
```

## Benefits of Current Approach

### ✅ Advantages
1. **No Jira credentials needed** - Works immediately
2. **Faster** - Local database vs REST API calls
3. **More reliable** - No network dependencies
4. **Simpler** - One integration point
5. **Historical data** - 24 PIs readily available
6. **Pre-aggregated** - Statistics already calculated

### 🔮 Future Enhancements (When Needed)
1. Real-time Jira sync
2. Direct issue creation/updates
3. Custom field queries
4. Jira comments integration
5. Attachment handling

## Testing Data Sources

### Check DL Webb App Connection
```bash
# Health check
curl http://localhost:8000/api/analysis/filters

# Get sample data
curl http://localhost:8000/api/flow_leadtime | head -20
```

### Check Evaluation Coach Integration
```bash
# Status
curl http://localhost:8850/api/leadtime/status

# Get metrics
curl http://localhost:8850/api/v1/metrics?scope=portfolio

# Generate insights
curl -X POST http://localhost:8850/api/v1/insights/generate \
  -H "Content-Type: application/json" \
  -d '{"scope":"portfolio","time_range":"last_pi"}'
```

## Summary

**Current State:**
- ✅ Fully functional with DL Webb App only
- ✅ All 60K+ features accessible
- ✅ Real-time metrics and insights
- ✅ No Jira required

**Future Option:**
- ⚪ Jira can be added via MCP if needed
- ⚪ Code structure supports both sources
- ⚪ No breaking changes required

**Recommendation:**
Continue using DL Webb App as the primary source. It provides everything needed. Consider Jira integration only if you need features not available through DL Webb App.
