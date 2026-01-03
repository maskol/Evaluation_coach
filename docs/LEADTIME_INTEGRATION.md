# Lead-Time Data Integration

This document describes how the Evaluation Coach integrates with the external DL Webb App lead-time server.

## Overview

The Evaluation Coach can access comprehensive feature lead-time data from an external server (DL Webb App) running on `http://localhost:8000`. This eliminates the need for duplicate data import and provides real-time access to flow metrics.

## Architecture

```
┌─────────────────────────┐
│  Evaluation Coach       │
│  (Port 8850)            │
│                         │
│  ┌──────────────────┐   │
│  │ Lead-Time Service│   │
│  └────────┬─────────┘   │
│           │             │
│  ┌────────▼─────────┐   │
│  │ Lead-Time Client │   │
│  └────────┬─────────┘   │
└───────────┼─────────────┘
            │ HTTP
            │
┌───────────▼─────────────┐
│  DL Webb App Server     │
│  (Port 8000)            │
│  SQLite Database        │
│  - Flow Lead-Time Data  │
│  - Bottleneck Analysis  │
│  - Throughput Metrics   │
└─────────────────────────┘
```

## Components

### 1. Lead-Time Client (`backend/integrations/leadtime_client.py`)

Low-level HTTP client for communicating with the DL Webb App API.

**Key Methods:**
- `get_flow_leadtime()` - Get detailed issue-by-issue lead-time data
- `get_leadtime_analysis()` - Get statistical analysis of lead-times
- `get_bottleneck_analysis()` - Identify workflow bottlenecks
- `get_waste_analysis()` - Analyze process waste
- `get_throughput_analysis()` - Get delivery rate metrics
- `get_trends_analysis()` - Get trend data over time

### 2. Lead-Time Service (`backend/services/leadtime_service.py`)

High-level service layer providing business logic and data enrichment.

**Key Features:**
- Health checking and availability monitoring
- Data enrichment (adding lead-time to Jira issues)
- Coaching-friendly summary generation
- Error handling and graceful degradation

### 3. API Endpoints (`backend/main.py`)

RESTful endpoints exposing lead-time functionality.

**Available Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `GET /api/leadtime/status` | Check if lead-time server is available |
| `GET /api/leadtime/filters` | Get available filter options (ARTs, PIs, Teams) |
| `GET /api/leadtime/features` | Get feature lead-time data |
| `GET /api/leadtime/statistics` | Get statistical analysis |
| `GET /api/leadtime/bottlenecks` | Get bottleneck analysis |
| `GET /api/leadtime/waste` | Get waste analysis |
| `GET /api/leadtime/throughput` | Get throughput metrics |
| `GET /api/leadtime/trends` | Get trend analysis |
| `GET /api/leadtime/summary` | Get comprehensive coaching summary |
| `POST /api/leadtime/enrich-issues` | Enrich Jira issues with lead-time data |

## Configuration

Add these settings to your `.env` file:

```bash
# Lead-Time Server Configuration
LEADTIME_SERVER_URL=http://localhost:8000
LEADTIME_SERVER_ENABLED=true
LEADTIME_SERVER_TIMEOUT=30
```

## Usage Examples

### 1. Check Server Status

```bash
curl http://localhost:8850/api/leadtime/status
```

**Response:**
```json
{
  "available": true,
  "server_url": "http://localhost:8000",
  "message": "Connected"
}
```

### 2. Get Available Filters

```bash
curl http://localhost:8850/api/leadtime/filters
```

**Response:**
```json
{
  "arts": ["ACEART", "OTHERART"],
  "pis": ["21Q4", "22Q1", "22Q2"],
  "teams": ["CCImprove", "TeamA"],
  "statuses": ["Done", "In Progress"]
}
```

### 3. Get Feature Lead-Time Data

```bash
curl "http://localhost:8850/api/leadtime/features?art=ACEART&pi=21Q4"
```

**Response:**
```json
{
  "count": 150,
  "features": [
    {
      "issue_key": "ACEART-12",
      "summary": "Feature description",
      "status": "Done",
      "art": "ACEART",
      "pi": "21Q4",
      "development_team": "CCImprove",
      "in_backlog": 7.78,
      "in_planned": 0.00,
      "in_analysis": 0.00,
      "in_progress": 20.95,
      "in_reviewing": 0.00,
      "total_leadtime": 33.93
    }
  ]
}
```

### 4. Get Lead-Time Statistics

```bash
curl "http://localhost:8850/api/leadtime/statistics?arts=ACEART"
```

**Response:**
```json
{
  "stage_statistics": {
    "in_backlog": {
      "mean": 36.80,
      "median": 2.86,
      "min": 0.00,
      "max": 1587.99,
      "stdev": 101.92,
      "p85": 63.68,
      "p95": 188.97,
      "count": 42518
    },
    "in_progress": {
      "mean": 68.25,
      "median": 42.14,
      "min": 0.00,
      "max": 2061.02,
      "stdev": 109.46,
      "p85": 108.15,
      "p95": 200.45,
      "count": 35182
    }
  }
}
```

### 5. Get Coaching Summary

```bash
curl "http://localhost:8850/api/leadtime/summary?art=ACEART&pi=22Q1"
```

**Response:**
```json
{
  "available": true,
  "scope": {
    "art": "ACEART",
    "pi": "22Q1"
  },
  "leadtime_statistics": { /* ... */ },
  "bottlenecks": { /* ... */ },
  "waste_analysis": { /* ... */ },
  "throughput": { /* ... */ },
  "data_source": "DL Webb App Lead-Time Server"
}
```

## Python Usage

```python
from services.leadtime_service import leadtime_service

# Check availability
if leadtime_service.is_available():
    
    # Get lead-time data
    features = leadtime_service.get_feature_leadtime_data(
        art="ACEART",
        pi="22Q1"
    )
    
    # Get statistics
    stats = leadtime_service.get_leadtime_statistics(
        arts=["ACEART"],
        pis=["22Q1", "22Q2"]
    )
    
    # Get coaching summary
    summary = leadtime_service.get_summary_for_coaching(
        art="ACEART",
        pi="22Q1"
    )
    
    # Enrich Jira issues
    jira_issues = [...]  # Your Jira issues
    enriched = leadtime_service.enrich_jira_issues_with_leadtime(jira_issues)
```

## Data Model

### Lead-Time Stage Breakdown

Each feature includes time spent in these workflow stages:

- `in_backlog` - Time waiting in backlog
- `in_planned` - Time in planned state
- `in_analysis` - Time in analysis/refinement
- `in_progress` - Time in active development
- `in_reviewing` - Time in code review
- `in_sit` - Time in System Integration Testing
- `in_uat` - Time in User Acceptance Testing
- `ready_for_deployment` - Time waiting for deployment
- `deployed` - Time since deployment
- `total_leadtime` - Total time from start to done

All times are in **days** (decimal format).

### Statistical Metrics

For each stage, the following statistics are provided:

- `mean` - Average time
- `median` - Middle value (50th percentile)
- `min` - Minimum time
- `max` - Maximum time
- `stdev` - Standard deviation
- `p85` - 85th percentile
- `p95` - 95th percentile
- `count` - Number of items

## Benefits

### 1. No Data Duplication
- Single source of truth for lead-time data
- No need to import the same data twice
- Automatic updates when DL Webb App data changes

### 2. Real-Time Access
- Always get the latest data
- No synchronization delays
- Instant updates across systems

### 3. Rich Analytics
- Stage-by-stage lead-time breakdown
- Statistical analysis (mean, median, percentiles)
- Bottleneck identification
- Waste analysis
- Throughput metrics
- Trend analysis

### 4. Easy Integration
- RESTful API endpoints
- Clean service layer
- Error handling and graceful degradation
- Health checking

## Troubleshooting

### Lead-Time Server Not Available

If you see "Lead-time service not available":

1. Check if DL Webb App is running:
   ```bash
   curl http://localhost:8000/api/analysis/filters
   ```

2. Check the configuration in `.env`:
   ```bash
   LEADTIME_SERVER_URL=http://localhost:8000
   LEADTIME_SERVER_ENABLED=true
   ```

3. Check the health endpoint:
   ```bash
   curl http://localhost:8850/api/health
   ```

### Connection Timeout

If requests timeout:

1. Increase the timeout in `.env`:
   ```bash
   LEADTIME_SERVER_TIMEOUT=60
   ```

2. Check network connectivity:
   ```bash
   ping localhost
   ```

### Empty Data

If endpoints return empty data:

1. Verify DL Webb App has data:
   ```bash
   curl http://localhost:8000/api/flow_leadtime
   ```

2. Check filters are valid:
   ```bash
   curl http://localhost:8000/api/analysis/filters
   ```

## Development

### Adding New Endpoints

1. Add method to `LeadTimeClient`:
   ```python
   def get_new_metric(self, param: str) -> Dict:
       return self._get(f"/api/new-endpoint", {"param": param})
   ```

2. Add service method in `LeadTimeService`:
   ```python
   def get_new_metric_with_enrichment(self, param: str) -> Dict:
       # Add business logic
       return self.client.get_new_metric(param)
   ```

3. Add API endpoint in `main.py`:
   ```python
   @app.get("/api/leadtime/new-metric")
   async def get_new_metric(param: str):
       return leadtime_service.get_new_metric_with_enrichment(param)
   ```

### Testing

Run the example script:

```bash
python example_leadtime_usage.py
```

Or test manually:

```bash
# Test with curl
curl http://localhost:8850/api/leadtime/status
curl http://localhost:8850/api/leadtime/filters
curl "http://localhost:8850/api/leadtime/features?art=ACEART"

# Test with httpie
http :8850/api/leadtime/statistics arts==ACEART
```

## Future Enhancements

Potential improvements:

1. **Caching** - Cache frequently accessed data
2. **Webhooks** - Real-time notifications of data changes
3. **Aggregation** - Pre-computed aggregates for common queries
4. **Batch Operations** - Bulk data fetching
5. **GraphQL** - Flexible query interface
6. **Data Sync** - Optional local caching for offline access

## Support

For issues or questions:

1. Check the API documentation: http://localhost:8850/docs
2. Review logs: `tail -f backend.log`
3. Verify DL Webb App status: http://localhost:8000/docs
