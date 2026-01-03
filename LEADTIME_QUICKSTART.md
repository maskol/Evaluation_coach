# Lead-Time Integration - Quick Start

## What Was Created

I've set up a complete integration between your Evaluation Coach app and the DL Webb App lead-time server. This allows you to access all feature lead-time data without duplicate imports.

## Files Created

1. **`backend/integrations/leadtime_client.py`** - HTTP client for DL Webb App API
2. **`backend/services/leadtime_service.py`** - Service layer with business logic
3. **`backend/main.py`** - Updated with 10 new API endpoints
4. **`backend/config/settings.py`** - Added lead-time server configuration
5. **`backend/api_models.py`** - Added lead-time data models
6. **`docs/LEADTIME_INTEGRATION.md`** - Complete documentation
7. **`example_leadtime_usage.py`** - Example usage script

## How It Works

```
Your Evaluation Coach (Port 8850)
         ↓ HTTP Requests
DL Webb App Server (Port 8000)
         ↓ SQLite Database
Lead-Time Data (No duplication!)
```

## Quick Test

### 1. Start Your Evaluation Coach

```bash
cd /Users/maskol/Local-Development/evaluation_coach/Evaluation_coach
./start.sh
```

### 2. Check Lead-Time Server Status

```bash
curl http://localhost:8850/api/leadtime/status
```

**Expected Response:**
```json
{
  "available": true,
  "server_url": "http://localhost:8000",
  "message": "Connected"
}
```

### 3. Get Real ARTs, Teams, and PIs

```bash
# Get all ARTs (14 available)
curl http://localhost:8850/api/arts

# Get all teams (100+ available)
curl http://localhost:8850/api/teams

# Get all Program Increments (24 available)
curl http://localhost:8850/api/pis
```

### 4. Get Available Filters

```bash
curl http://localhost:8850/api/leadtime/filters
```

This shows all ARTs, PIs, and teams available in the DL Webb App.

### 4. Get Lead-Time Data for an ART

```bash
curl "http://localhost:8850/api/leadtime/features?art=ACEART"
```

This returns all features with their lead-time breakdown.

### 5. Get Statistics

```bash
curl "http://localhost:8850/api/leadtime/statistics?arts=ACEART"
```

This returns statistical analysis (mean, median, p85, p95) for each workflow stage.

## Configuration

No configuration needed! The default settings work:

```bash
# In .env (optional, these are the defaults)
LEADTIME_SERVER_URL=http://localhost:8000
LEADTIME_SERVER_ENABLED=true
LEADTIME_SERVER_TIMEOUT=30
```

## Available Endpoints

| Endpoint | What It Does |
|----------|--------------|
| `GET /api/leadtime/status` | Check if DL Webb App is available |
| `GET /api/leadtime/filters` | Get available ARTs, PIs, Teams |
| `GET /api/leadtime/features` | Get feature lead-time data |
| `GET /api/leadtime/statistics` | Get statistical analysis |
| `GET /api/leadtime/bottlenecks` | Identify workflow bottlenecks |
| `GET /api/leadtime/waste` | Analyze process waste |
| `GET /api/leadtime/throughput` | Get delivery rate metrics |
| `GET /api/leadtime/trends` | Get trend analysis over time |
| `GET /api/leadtime/summary` | Get comprehensive coaching summary |
| `POST /api/leadtime/enrich-issues` | Add lead-time data to Jira issues |

## Use in Your Code

### Python Example

```python
from services.leadtime_service import leadtime_service

# Check if available
if leadtime_service.is_available():
    
    # Get lead-time for ACEART
    features = leadtime_service.get_feature_leadtime_data(art="ACEART")
    
    # Get statistics
    stats = leadtime_service.get_leadtime_statistics(arts=["ACEART"])
    
    # Get coaching summary
    summary = leadtime_service.get_summary_for_coaching(art="ACEART", pi="22Q1")
```

### Frontend Example (JavaScript)

```javascript
// Check status
fetch('http://localhost:8850/api/leadtime/status')
  .then(r => r.json())
  .then(data => console.log('Lead-time server:', data));

// Get features for an ART
fetch('http://localhost:8850/api/leadtime/features?art=ACEART')
  .then(r => r.json())
  .then(data => {
    console.log(`Found ${data.count} features`);
    data.features.forEach(f => {
      console.log(`${f.issue_key}: ${f.total_leadtime} days`);
    });
  });

// Get statistics
fetch('http://localhost:8850/api/leadtime/statistics?arts=ACEART')
  .then(r => r.json())
  .then(stats => {
    Object.entries(stats.stage_statistics).forEach(([stage, data]) => {
      console.log(`${stage}: mean=${data.mean.toFixed(2)} days`);
    });
  });
```

## Benefits

✅ **No Duplicate Data** - Single source of truth in DL Webb App  
✅ **Real-Time Access** - Always get the latest data  
✅ **Rich Analytics** - Stage-by-stage breakdown, statistics, bottlenecks  
✅ **Easy to Use** - Simple REST API  
✅ **Well Documented** - Complete docs in `docs/LEADTIME_INTEGRATION.md`  
✅ **Error Handling** - Gracefully handles server unavailability  

## What This Gives You

### Lead-Time Data Per Feature

For each feature, you get:
- Time in backlog
- Time in planning
- Time in analysis
- Time in development
- Time in review
- Time in testing (SIT, UAT)
- Time waiting for deployment
- **Total lead-time**

### Statistical Analysis

For each stage:
- Mean (average)
- Median (typical)
- 85th percentile (most items)
- 95th percentile (almost all items)
- Min/max (extremes)
- Standard deviation (variability)
- Count (how many items)

### Bottleneck Identification

Find which stages cause the most delay.

### Waste Analysis

Identify non-value-adding time.

### Throughput Metrics

See delivery rate over time.

### Trend Analysis

Track improvements or regressions.

## Next Steps

1. **Test the integration:**
   ```bash
   python example_leadtime_usage.py
   ```

2. **View API docs:**
   Visit http://localhost:8850/docs

3. **Integrate with your frontend:**
   Use the endpoints in your JavaScript code

4. **Use in LLM coaching:**
   The coaching agents can now access lead-time data for insights

## Troubleshooting

**Problem:** "Lead-time service not available"

**Solution:** Make sure DL Webb App is running on port 8000:
```bash
curl http://localhost:8000/api/analysis/filters
```

**Problem:** Import errors

**Solution:** Make sure you're running from the backend directory or using the proper PYTHONPATH

**Problem:** Empty data

**Solution:** Check that DL Webb App has data by querying it directly

## Documentation

Full documentation is available at:
- `docs/LEADTIME_INTEGRATION.md` - Complete guide
- `http://localhost:8850/docs` - Interactive API documentation
- `http://localhost:8000/docs` - DL Webb App API documentation

## Questions?

Check the comprehensive documentation in `docs/LEADTIME_INTEGRATION.md` which includes:
- Architecture diagrams
- All endpoints with examples
- Data models
- Python and JavaScript usage examples
- Troubleshooting guide
- Development guide
