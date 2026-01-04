# Data Improvements Guide
**Evaluation Coach - Enhanced Analytics Requirements**

This document outlines the data enhancements needed to unlock advanced organizational insights and recommendations.

---

## 📊 Current State

### Existing Data (DL Webb APP - Port 8000)

**Endpoint:** `GET /api/leadtime_thr_data`
```json
{
  "feature": "ACEART-1018",
  "art": "ACEART",
  "lead_time_days": 211,
  "throughput": 1,
  "id": 1,
  "pi": "23Q1"
}
```

**Endpoint:** `GET /api/teams/` ✅ **ALREADY EXISTS**
```json
[
  {
    "team_id": 1,
    "team_name": "API Developer Journey",
    "art_id": 104,
    "team_type_id": 1,
    "portfolio_id": 1,
    "line_organisation_id": 81,
    "domain_id": 6,
    "art": {
      "art_id": 104,
      "art_name": "Enabling Platform ART",
      "art_key_jira": "EPART",
      "portfolio_id": 1
    }
  }
]
```

**Endpoint:** `GET /api/teams/{team_id}` ✅ **ALREADY EXISTS**
```json
{
  "team_id": 1,
  "team_name": "API Developer Journey",
  "art_id": 104,
  "team_type_id": 1,
  "portfolio_id": 1,
  "line_organisation_id": 81,
  "line_manager_id": null,
  "domain_id": 6,
  "comments": null
}
```

**Endpoint:** `GET /api/analysis/bottlenecks`
```json
{
  "bottleneck_stages": [
    {
      "stage": "in_progress",
      "bottleneck_score": 78.38,
      "mean_time": 68.24,
      "max_time": 2061.01,
      "items_exceeding_threshold": 27576
    }
  ],
  "stuck_items": [
    {
      "issue_key": "ACEART-2",
      "stage": "in_progress",
      "days_in_stage": 716.10,
      "art": "ACEART",
      "team": null
    }
  ],
  "wip_statistics": {
    "in_progress": {
      "items_exceeding_threshold": 8474,
      "mean_time": 68.24,
      "max_time": 2061.01,
      "total_items": 35250
    }
  },
  "threshold_days": 30
}
```

---

## 🎯 Required Data Enhancements

### Priority 1: Team-Level Data (HIGH IMPACT, LOW EFFORT)

#### 1.1 Add Team to Feature Data
**Endpoint:** `GET /api/leadtime_thr_data` (MODIFY EXISTING)

**Required Change:**
```json
{
  "feature": "ACEART-1018",
  "art": "ACEART",
  "team": "Team Phoenix",           // ← ADD THIS
  "lead_time_days": 211,
  "throughput": 1,
  "id": 1,
  "pi": "23Q1"
}
```

**DL Webb APP Implementation:**
```sql
-- Current query (simplified)
SELECT 
  f.feature_key as feature,
  a.art_name as art,
  f.lead_time_days,
  f.throughput,
  f.id,
  f.pi
FROM feature f
JOIN art a ON f.art_id = a.art_id

-- Enhanced query
SELECT 
  f.feature_key as feature,
  a.art_name as art,
  t.team_name as team,              -- ADD THIS JOIN
  f.lead_time_days,
  f.throughput,
  f.id,
  f.pi
FROM feature f
JOIN art a ON f.art_id = a.art_id
LEFT JOIN team t ON f.team_id = t.team_id  -- ADD THIS LINE
```

**Impact:** Enables team-level insights, load balancing analysis, team performance comparison

---

#### 1.2 Add Team to Stuck Items
**Endpoint:** `GET /api/analysis/bottlenecks` (MODIFY EXISTING)

**Required Change:**
```json
{
  "stuck_items": [
    {
      "issue_key": "ACEART-2",
      "stage": "in_progress",
      "days_in_stage": 716.10,
      "art": "ACEART",
      "team": "Team Phoenix"        // ← POPULATE THIS (currently null)
    }
  ]
}
```

**DL Webb APP Implementation:**
```sql
-- Add team join to stuck items query
SELECT 
  wh.issue_key,
  wh.stage,
  wh.days_in_stage,
  a.art_name as art,
  t.team_name as team              -- ADD THIS
FROM workflow_history wh
JOIN feature f ON wh.issue_key = f.feature_key
JOIN art a ON f.art_id = a.art_id
LEFT JOIN team t ON f.team_id = t.team_id  -- ADD THIS LINE
WHERE wh.days_in_stage > :threshold
ORDER BY wh.days_in_stage DESC
```

**Impact:** Team-specific bottleneck identification, targeted coaching recommendations

---

#### 1.3 Create Team Performance Metrics Endpoint
**Endpoint:** `GET /api/team-performance` or `GET /api/team-metrics` (NEW ENDPOINT)

**Note:** `/api/teams/` already exists with basic team info. This new endpoint adds **performance metrics**.

**Response Structure:**
```json
{
  "teams": [
    {
      "team_name": "Team Phoenix",
      "art": "ACEART",
      "pi": "25Q4",
      "features_delivered": 12,
      "avg_leadtime": 45.5,
      "total_leadtime": 546.0,
      "features_in_progress": 3,
      "team_size": 8,
      "domain": "Customer Experience"
    }
  ]
}
```

**DL Webb APP Implementation:**
```python
# In main_sqlmodel.pperformance")  # or /api/team-metrics
def get_team_performance_metrics(
    arts: Optional[str] = None,
    pis: Optional[str] = None
):
    """
    Get team-level performance metrics (extends /api/teams/ with delivery metrics)
    Note: /api/teams/ already provides team structure, this adds performance data
    """
    Get team-level performance metrics
    """
    query = """
    SELECT 
        t.team_name,
        a.art_name as art,
        f.pi,
        COUNT(CASE WHEN f.throughput = 1 THEN 1 END) as features_delivered,
        AVG(CASE WHEN f.throughput = 1 THEN f.lead_time_days END) as avg_leadtime,
        SUM(CASE WHEN f.throughput = 1 THEN f.lead_time_days END) as total_leadtime,
        COUNT(CASE WHEN f.throughput = 0 THEN 1 END) as features_in_progress,
        t.team_size,
        t.domain
    FROM feature f
    JOIN team t ON f.team_id = t.team_id
    JOIN art a ON f.art_id = a.art_id
    WHERE 1=1
    """
    
    params = {}
    if arts:
        query += " AND a.art_name IN :arts"
        params["arts"] = tuple(arts.split(','))
    if pis:
        query += " AND f.pi IN :pis"
        params["pis"] = tuple(pis.split(','))
    
    query += " GROUP BY t.team_name, a.art_name, f.pi"
    
    results = session.execute(text(query), params).fetchall()
    
    return {
        "teams": [
            {
                "team_name": r.team_name,
                "art": r.art,
                "pi": r.pi,
                "features_delivered": r.features_delivered,
                "avg_leadtime": float(r.avg_leadtime) if r.avg_leadtime else 0,
                "total_leadtime": float(r.total_leadtime) if r.total_leadtime else 0,
                "features_in_progress": r.features_in_progress,
                "team_size": r.team_size,
                "domain": r.domain
            }
            for r in results
        ]
    }
```

**Impact:** Team load balancing, capacity analysis, organizational structure insights
**Alternative Approach:** Enhance existing `/api/teams/` endpoint with optional `?include_performance=true` parameter to avoid creating a new endpoint.


---

### Priority 2: Workflow History (MEDIUM IMPACT, MEDIUM EFFORT)

#### 2.1 Add Full Transition History to Stuck Items
**Endpoint:** `GET /api/analysis/bottlenecks` (ENHANCE EXISTING)

**Required Change:**
```json
{
  "stuck_items": [
    {
      "issue_key": "ACEART-326",
      "stage": "in_progress",
      "days_in_stage": 175.85,
      "art": "ACEART",
      "team": "Team Phoenix",
      "transition_history": [          // ← ADD THIS
        {
          "stage": "in_backlog",
          "days": 20,
          "sequence": 1
        },
        {
          "stage": "in_analysis",
          "days": 5,
          "sequence": 2
        },
        {
          "stage": "in_progress",
          "days": 30,
          "sequence": 3
        },
        {
          "stage": "in_reviewing",
          "days": 3,
          "sequence": 4
        },
        {
          "stage": "in_progress",       // Rework detected!
          "days": 145.85,
          "sequence": 5,
          "current": true
        }
      ],
      "rework_loops": 1,
      "total_wait_time": 25,
      "total_active_time": 178.85
    }
  ]
}
```

**DL Webb APP Implementation:**
```sql
-- Query to get full workflow history per issue
SELECT 
    issue_key,
    stage,
    days_in_stage,
    sequence_order,
    is_current_stage,
    -- Detect rework: count how many times issue returns to same stage
    COUNT(*) OVER (PARTITION BY issue_key, stage) - 1 as rework_count
FROM workflow_history
WHERE issue_key IN (
    SELECT DISTINCT issue_key 
    FROM workflow_history 
    WHERE days_in_stage > :threshold
)
ORDER BY issue_key, sequence_order
```

**Impact:** Rework loop detection, value vs non-value time analysis, process efficiency insights

---

### Priority 3: Story-Level Granularity (MEDIUM IMPACT, MEDIUM EFFORT)

#### 3.1 Create Story Metrics Endpoint
**Endpoint:** `GET /api/story-metrics` (NEW ENDPOINT)

**Response Structure:**
```json
{
  "stories": [
    {
      "story_key": "ACEART-1234",
      "parent_feature": "ACEART-100",
      "team": "Team Phoenix",
      "art": "ACEART",
      "story_points": 5,
      "lead_time_days": 8,
      "pi": "25Q4",
      "status": "Done",
      "created_date": "2025-10-01",
      "completed_date": "2025-10-09"
    }
  ]
}
```

**DL Webb APP Implementation:**
```python
@app.get("/api/story-metrics")
def get_story_metrics(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
    teams: Optional[str] = None
):
    """
    Get user story level metrics for detailed analysis
    """
    query = """
    SELECT 
        s.story_key,
        f.feature_key as parent_feature,
        t.team_name as team,
        a.art_name as art,
        s.story_points,
        s.lead_time_days,
        s.pi,
        s.status,
        s.created_date,
        s.completed_date
    FROM story s
    JOIN feature f ON s.feature_id = f.id
    JOIN team t ON s.team_id = t.team_id
    JOIN art a ON f.art_id = a.art_id
    WHERE s.story_key IS NOT NULL
    """
    
    # Add filters similar to team-metrics
    # Return paginated results (limit 1000 per call)
```

**Impact:** Velocity tracking, estimation accuracy, story splitting effectiveness

---

### Priority 4: Dependency Tracking (HIGH IMPACT, HIGHER EFFORT)

#### 4.1 Create Dependencies Endpoint
**Endpoint:** `GET /api/dependencies` (NEW ENDPOINT)

**Response Structure:**
```json
{
  "dependencies": [
    {
      "issue_key": "ACEART-123",
      "team": "Team Phoenix",
      "art": "ACEART",
      "blocks": [
        {
          "issue_key": "C4ART-456",
          "team": "Team Alpha",
          "art": "C4ART",
          "blocked_days": 5
        }
      ],
      "blocked_by": [
        {
          "issue_key": "PLATART-999",
          "team": "Platform Team",
          "art": "PLATART",
          "blocking_days": 12
        }
      ],
      "cross_art_dependency": true,
      "total_blocking_days": 12
    }
  ],
  "dependency_summary": {
    "total_dependencies": 156,
    "cross_art_dependencies": 45,
    "avg_blocking_days": 8.3,
    "most_blocking_art": "PLATART",
    "most_blocked_art": "ACEART"
  }
}
```

**DL Webb APP Implementation:**
```sql
-- Assumes dependency table exists or needs to be created
CREATE TABLE IF NOT EXISTS dependency (
    id INTEGER PRIMARY KEY,
    source_issue_key TEXT,
    target_issue_key TEXT,
    dependency_type TEXT, -- 'blocks' or 'blocked_by'
    created_date TIMESTAMP,
    resolved_date TIMESTAMP,
    blocking_days INTEGER
);

-- Query for dependency analysis
SELECT 
    d.source_issue_key as issue_key,
    f1.team_id as source_team,
    f1.art_id as source_art,
    d.target_issue_key,
    f2.team_id as target_team,
    f2.art_id as target_art,
    d.blocking_days,
    CASE WHEN f1.art_id != f2.art_id THEN 1 ELSE 0 END as cross_art
FROM dependency d
JOIN feature f1 ON d.source_issue_key = f1.feature_key
JOIN feature f2 ON d.target_issue_key = f2.feature_key
WHERE d.dependency_type = 'blocks'
```

**Impact:** Cross-ART coordination overhead, organizational coupling detection, value stream optimization

---

## 📈 Expected Analytics Enhancements

### With Team Data (Priority 1):
✅ **Team Load Balancing Analysis** - Identify over/under utilized teams  
✅ **Team Performance Comparison** - Benchmark teams within ARTs  
✅ **Targeted Coaching** - Team-specific recommendations  
✅ **Resource Reallocation** - Data-driven team restructuring  

### With Workflow History (Priority 2):
✅ **Rework Loop Detection** - Identify items bouncing between stages  
✅ **Value vs Non-Value Time** - Measure active vs waiting time  
✅ **Process Efficiency** - Stage transition pattern analysis  
✅ **Quality Injection Points** - Where issues are created vs found  

### With Story-Level Data (Priority 3):
✅ **Velocity Tracking** - Team velocity trends over time  
✅ **Estimation Accuracy** - Planned vs actual comparison  
✅ **Story Splitting Effectiveness** - Batch size optimization  
✅ **Predictability Improvements** - Planning accuracy insights  

### With Dependency Data (Priority 4):
✅ **Cross-ART Dependency Heatmap** - Identify high coupling  
✅ **Coordination Overhead** - Measure dependency cost  
✅ **Organizational Structure** - Value stream realignment recommendations  
✅ **Autonomy Score** - Team independence metrics  

---

## 🚀 Implementation Roadmap (leverage existing team_id relationships)
2. ✅ Populate `team` field in stuck_items (use existing team_id foreign keys)
3. ✅ Create `/api/team-performance` endpoint OR enhance `/api/teams/` with performance metrics
4. 🧪 Test with Evaluation Coach

**Note:** `/api/teams/` and `/api/teams/{team_id}` already exist! Just need to connect this data to feature/throughput data.eadtime_thr_data`
2. ✅ Populate `team` field in stuck_items
3. ✅ Create `/api/team-metrics` endpoint
4. 🧪 Test with Evaluation Coach

**Deliverable:** Team-level insights appear in Evaluation Coach

### Phase 2: Enhanced Analysis (2-4 weeks)
5. ✅ Add `transition_history` to stuck_items
6. ✅ Enhance bottleneck analysis with rework detection
7. ✅ Create `/api/story-metrics` endpoint
8. 🧪 Test story-level analytics

**Deliverable:** Rework detection and story sizing insights

### Phase 3: Advanced Features (4-8 weeks)
9. ✅ Create dependency tracking table/model
10. ✅ Create `/api/dependencies` endpoint
11. ✅ Implement dependency heatmap visualization
12. 🧪 Full integration testing

**Deliverable:** Complete organizational structure insights

---

## 🔧 Testing & Validation (✅ Already exists via /api/teams/):**
```bash
# Verify team endpoint works
curl "http://localhost:8000/api/teams/" | jq 'length'
# Should return: number of teams (e.g., 50+)

curl "http://localhost:8000/api/teams/1" | jq '.team_name'
# Should return: team name (e.g., "API Developer Journey")
```

**Check feature-team relationship

### Validation Queries

**Check team data availability:**
```sql
SELECT 
    COUNT(DISTINCT t.team_name) as total_teams,
    COUNT(f.id) as total_features,
    COUNT(CASE WHEN f.team_id IS NOT NULL THEN 1 END) as features_with_team,
    ROUND(COUNT(CASE WHEN f.team_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(f.id), 2) as coverage_pct
FROM feature f
LEFT JOIN team t ON f.team_id = t.team_id;
```

**Check workflow history completeness:**
```sql
SELECT 
    COUNT(DISTINCT issue_key) as issues_with_history,
    AVG(transitions_per_issue) as avg_transitions,
    MAX(transitions_per_issue) as max_transitions
FROM (
    SELECT issue_key, COUNT(*) as transitions_per_issue
    FROM workflow_history
    GROUP BY issue_key
) sub;
```

**Verify team metrics calculation:**
```sql
-- Sample test query
SELECT 
    t.team_name,
    a.art_name,
    COUNT(*) as features,
    AVG(f.lead_time_days) as avg_leadtime
FROM feature f
JOIN team t ON f.team_id = t.team_id
JOIN art a ON f.art_id = a.art_id
WHERE f.throughput = 1
  AND f.pi IN ('25Q3', '25Q4')
GROUP BY t.team_name, a.art_name
ORDER BY feaperformance endpoint:**
```bash
# Option 1: New endpoint
curl "http://localhost:8000/api/team-performance?pis=25Q4" | jq '.teams | length'
# Should return: number of active teams

# Option 2: Enhanced existing endpoint
curl "http://localhost:8000/api/teams/?include_performance=true&pis=25Q4" | jq 'length'
# Should return: teams with performance data
### API Testing

**Test team-enhanced throughput data:**
```bash
curl "http://localhost:8000/api/leadtime_thr_data?pis=25Q4&limit=5" | jq '.[0].team'
# Should return: "Team Phoenix" (not null)
```

**T✅] Team data structure exists (`/api/teams/` and `/api/teams/{team_id}`)
- [ ] All features in `/api/leadtime_thr_data` have non-null team values
- [ ] `/api/team-performance` returns performance
curl "http://localhost:8000/api/team-metrics?pis=25Q4" | jq '.teams | length'
# Should return: number of active teams
```

**Test Evaluation Coach integration:**
```bash
curl "http://localhost:8850/api/v1/insights?pis=25Q4&arts=ACEART" | jq '.insights[] | select(.title | contains("Load Balance"))'
# Should return: team load balancing insights when data variance exists
```

---

## 📋 Success Criteria

### Phase 1 Complete:
- [ ] All features in `/api/leadtime_thr_data` have non-null team values
- [ ] `/api/team-metrics` returns data for all active teams
- [ ] Evaluation Coach displays "ART Load Balancing" insights
- [ ] Team-specific bottleneck insights appear

### Phase 2 Complete:
- [ ] Stuck items include full transition history
- [ ] Rework loops detected and VERY LOW | 1 | 1-2 days |
| Team performance endpoint | HIGH | LOW | 1 | 2-3 days |
| Populate team in stuck items | MEDIUM | VERY LOW | 1 | 1 day

### Phase 3 Complete:
- [ ] Dependency data captured for features
- [ ] Cross-ART dependency analysis available
- [ ] Coordination overhead metrics calculated
- [ ] Organizational structure recommendations appear

---

## 🎯 Priority Matrix

| Enhancement | Impact | Effort | Priority | Timeline |
|-------------|--------|--------|----------|----------|
| Add team to features | HIGH | LOW | 1 | 2-3 days |
| Team metrics endpoint | HIGH | LOW | 1 | 3-5 days |
| Populate team in stuck items | MEDIUM | LOW | 1 | 1-2 days |
| Workflow history enhancement | MEDIUM | MEDIUM | 2 | 1-2 weeks |
| Story-level metrics | MEDIUM | MEDIUM | 2 | 1-2 weeks |
| Dependency tracking | HIGH | HIGH | 3 | 3-4 weeks |

---

## 📞 Support & Questions

For implementation questions or clarifications:team performance endpoint or enhance existing `/api/teams/`
- DL Webb APP: `/backend/analysis_engine.py` - Enhance analysis logic to include team data
- Evaluation Coach: Already supports team data, will auto-detect new insights

**Key Existing Endpoints to Leverage:**
- ✅ `/api/teams/` - List all teams with ART relationships
- ✅ `/api/teams/{team_id}` - Get team details
- ✅ `/api/teams/{team_id}/arts/` - Get team's ART associations
- ✅ `/api/team-types/` - Get team type classifications

---

**Last Updated:** January 4, 2026  
**Version:** 1.1  
**Status:** Ready for Implementation (Team endpoints already exist!) team data, will auto-detect new insights

---

**Last Updated:** January 4, 2026  
**Version:** 1.0  
**Status:** Ready for Implementation
