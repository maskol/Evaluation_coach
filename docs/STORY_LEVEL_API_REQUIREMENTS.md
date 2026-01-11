# Story-Level Analysis API Requirements for DL Webb App

## Document Information
- **Date**: January 11, 2026
- **Requestor**: Evaluation Coach Team
- **Target System**: DL Webb App API
- **Priority**: High
- **Status**: Requirements Definition

## Executive Summary

The Evaluation Coach application currently supports both Feature-level and Story-level analysis views. However, the DL Webb App API only provides comprehensive analysis endpoints for feature-level data. This document outlines the required API enhancements to support story-level bottleneck analysis, enabling teams to analyze user story flow in addition to epic/feature flow.

## Business Need

### Current Limitation
- **Dashboard Metrics**: Story-level metrics display correctly using the `story_flow_leadtime` endpoint
- **AI Insights**: Bottleneck analysis and AI-powered insights only work at the feature level due to API limitations
- **User Experience**: Users selecting "Story Level" see a mismatch between dashboard data (stories) and insights (features)

### Business Value
1. **Granular Analysis**: Enable teams to identify bottlenecks at the user story level, providing more actionable insights for daily standups and sprint planning
2. **Complete Feature Parity**: Ensure story-level analysis has the same depth as feature-level analysis
3. **Workflow Visibility**: Story-level flow often differs from feature-level flow (different stages, different bottlenecks)
4. **Team-Level Insights**: Stories are more relevant for individual team analysis than features

## Current State

### Existing Endpoints (Feature-Level)
The DL Webb App currently provides:

```
GET /flow_leadtime
- Returns feature-level flow data
- Includes stage times, lead times, status, ART, team, PI
- Supports filtering by: art, development_team, pi, limit

GET /analysis_summary
- Comprehensive bottleneck analysis for features
- Parameters: arts, pis, team, threshold_days
- Returns:
  * bottleneck_analysis
    - stage_analysis (mean_time, max_time, items_exceeding_threshold, bottleneck_score)
    - stuck_items (feature_key, days_in_stage, current_stage)
    - wip_statistics (total_wip, average_age, wip_by_stage)
  * flow_efficiency_data
  * planning_accuracy_data
  * waste_metrics

GET /pip_data
- PI planning metrics by ART/team
- Returns: flow_efficiency_percent, pi_predictability, quality_score
```

### Existing Story-Level Endpoint
```
GET /story_flow_leadtime
- Returns story-level flow data
- Similar structure to flow_leadtime but for user stories
- Supports same filtering parameters
- **Missing**: No corresponding analysis_summary endpoint
```

## Required API Enhancements

### Priority 1: Story-Level Analysis Summary Endpoint

#### New Endpoint
```
GET /story_analysis_summary
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| arts | string | No | Comma-separated list of ART keys (e.g., "UCART,SAAS") |
| pis | string | No | Comma-separated list of PIs (e.g., "26Q1,25Q4") |
| team | string | No | Development team name for team-level filtering |
| threshold_days | integer | No | Threshold for identifying bottlenecks (default: 60) |
| limit | integer | No | Maximum number of items to analyze (default: 10000) |

#### Expected Response Structure
```json
{
  "bottleneck_analysis": {
    "stage_analysis": {
      "refinement": {
        "mean_time": 12.5,
        "median_time": 10.0,
        "max_time": 45,
        "min_time": 1,
        "items_exceeding_threshold": 3,
        "stage_occurrences": 150,
        "bottleneck_score": 65.0,
        "p50": 10.0,
        "p85": 25.0,
        "p95": 35.0
      },
      "in_progress": { /* same structure */ },
      "code_review": { /* same structure */ },
      "testing": { /* same structure */ },
      "deployed": { /* same structure */ }
    },
    "stuck_items": [
      {
        "story_key": "UCART-ST-1234",
        "story_name": "User login functionality",
        "feature_key": "UCART-2228",
        "current_stage": "code_review",
        "days_in_stage": 15.5,
        "total_age": 45.0,
        "art": "UCART",
        "development_team": "Loke",
        "pi": "26Q1",
        "status": "In Progress",
        "priority": "High"
      }
    ],
    "wip_statistics": {
      "total_wip": 45,
      "average_age": 18.5,
      "median_age": 15.0,
      "wip_by_stage": {
        "refinement": 5,
        "in_progress": 15,
        "code_review": 12,
        "testing": 8,
        "deployed": 5
      },
      "wip_by_team": {
        "Loke": 12,
        "Thor": 15,
        "Odin": 18
      }
    },
    "flow_distribution": {
      "by_priority": {
        "High": 15,
        "Medium": 20,
        "Low": 10
      },
      "by_status": {
        "In Progress": 25,
        "Blocked": 5,
        "Ready": 15
      }
    }
  },
  "story_stages": ["refinement", "in_progress", "code_review", "testing", "deployed"],
  "threshold_days": 60,
  "analysis_date": "2026-01-11T10:30:00Z",
  "filters_applied": {
    "arts": ["UCART"],
    "pis": ["26Q1"],
    "team": "Loke"
  }
}
```

#### Calculation Logic
- **Stage Analysis**: Calculate mean/median/max/min/percentiles for time spent in each story stage
- **Bottleneck Score**: Percentage of items exceeding threshold for each stage
- **Stuck Items**: Stories that have been in current stage > threshold_days
- **WIP Statistics**: Count and age distribution of work-in-progress stories
- **Stage Names**: Story stages differ from feature stages:
  - Feature stages: `in_backlog`, `rfp`, `in_sit`, `in_uat`, `deployed`
  - Story stages: `refinement`, `in_progress`, `code_review`, `testing`, `deployed`

### Priority 2: Story-Level Planning Accuracy Endpoint

#### New Endpoint
```
GET /story_pip_data
```

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| pi | string | Yes | Program Increment (e.g., "26Q1") |
| art | string | No | ART key for filtering |
| team | string | No | Development team name |

#### Expected Response Structure
```json
[
  {
    "art_name": "UCART",
    "development_team": "Loke",
    "pi": "26Q1",
    "story_metrics": {
      "planned_stories": 45,
      "completed_stories": 38,
      "completion_rate": 84.4,
      "story_predictability": 84.4,
      "average_story_leadtime": 12.5,
      "median_story_leadtime": 10.0,
      "story_flow_efficiency_percent": 65.0
    },
    "velocity_metrics": {
      "planned_points": 120,
      "completed_points": 105,
      "velocity_predictability": 87.5
    },
    "quality_metrics": {
      "defect_rate": 0.05,
      "rework_rate": 0.08,
      "quality_score": 87.0
    }
  }
]
```

### Priority 3: Story-Level Waste Analysis

#### Enhancement to Existing Endpoint
Add story-level support to existing waste analysis or create:

```
GET /story_waste_analysis
```

#### Expected Response
```json
{
  "waste_metrics": {
    "blocked_stories": {
      "count": 5,
      "total_blocked_days": 75,
      "average_blocked_days": 15.0,
      "stories": [
        {
          "story_key": "UCART-ST-1234",
          "blocked_days": 20,
          "reason": "Waiting for dependency"
        }
      ]
    },
    "rework_stories": {
      "count": 8,
      "rework_rate": 0.08,
      "stories": [...]
    },
    "stories_exceeding_threshold": {
      "count": 12,
      "percentage": 15.0
    }
  }
}
```

## Story Stage Definitions

### Required Story Workflow Stages
Stories typically flow through different stages than features. Please ensure the API recognizes these story-specific stages:

| Stage | Description | Equivalent Feature Stage |
|-------|-------------|-------------------------|
| `refinement` | Story is being refined/groomed | Similar to `in_backlog` |
| `in_progress` | Active development | Similar to `in_sit` |
| `code_review` | Code review/PR stage | (New - story-specific) |
| `testing` | QA/Testing phase | Similar to `in_uat` |
| `deployed` | Deployed to production | Same as feature `deployed` |

**Note**: The story stages should be configurable as different teams may have different workflows.

## Data Consistency Requirements

### Story-Feature Relationship
- Each story should maintain its parent feature relationship
- API responses should include both `story_key` and `feature_key`
- Enable filtering stories by parent feature

### Team Filtering
- Must support `development_team` parameter for story-level endpoints
- Team filtering should match the behavior of feature endpoints
- Support for team-specific stage workflows if applicable

### Time Calculations
- Calculate time in stage using the same logic as feature endpoints
- Handle stories that move backward through stages (rework)
- Include timestamp fields for stage transitions

## Implementation Notes

### Backward Compatibility
- Existing feature-level endpoints should remain unchanged
- New story endpoints should follow the same API patterns and conventions
- Use consistent parameter naming across feature and story endpoints

### Performance Considerations
- Story-level data will be significantly larger than feature data (10-50x more records)
- Consider pagination for large datasets
- Implement efficient indexing on commonly filtered fields (art, team, pi, status)
- Cache frequently requested aggregations

### Error Handling
- Return appropriate HTTP status codes (400 for invalid parameters, 404 for no data)
- Include helpful error messages
- Handle missing or incomplete story data gracefully

## Testing Requirements

### Test Scenarios
1. **Team-Level Story Analysis**
   - Filter by team: `GET /story_analysis_summary?team=Loke&arts=UCART&pis=26Q1`
   - Verify only Loke team's stories are included
   - Verify bottleneck calculations are accurate

2. **Multi-PI Story Analysis**
   - Request multiple PIs: `GET /story_analysis_summary?pis=26Q1,25Q4&arts=UCART`
   - Verify data from both PIs is included
   - Verify time calculations are correct

3. **Story-Level Planning Accuracy**
   - Request PI planning data: `GET /story_pip_data?pi=26Q1&team=Loke`
   - Verify completion rates match actual story counts
   - Cross-check with feature-level pip_data

4. **Empty Result Sets**
   - Request data with no matching stories
   - Verify appropriate empty response structure

### Sample Data
Please provide sample responses for:
- A typical team with 30-50 stories in a PI
- A team with bottlenecks (some stories >threshold)
- A team with no WIP (all stories completed)

## Integration Points

### Evaluation Coach Integration
The Evaluation Coach will consume these endpoints in:

1. **Dashboard View** (`/api/v1/dashboard`)
   - When `analysis_level=story`, call story-level analysis endpoint
   - Display story-specific metrics in dashboard cards

2. **Insights Generation** (`/api/v1/insights/generate`)
   - Generate AI insights from story-level bottleneck data
   - Identify story-level flow issues and recommendations

3. **Little's Law Analysis** (`/api/v1/littles-law`)
   - Calculate WIP, Throughput, Lead Time from story data
   - Compare story-level vs feature-level flow patterns

## Timeline & Priorities

### Phase 1: Core Analysis (High Priority)
- `GET /story_analysis_summary` endpoint
- Full bottleneck analysis including stuck items and WIP statistics
- **Target**: Q1 2026

### Phase 2: Planning & Metrics (Medium Priority)
- `GET /story_pip_data` endpoint
- Story-level planning accuracy and velocity metrics
- **Target**: Q2 2026

### Phase 3: Advanced Analytics (Lower Priority)
- `GET /story_waste_analysis` endpoint
- Story-level waste and efficiency metrics
- **Target**: Q3 2026

## Questions for DL Webb App Team

1. **Data Availability**: Does the database currently track story stage transitions with timestamps?
2. **Stage Configuration**: Are story stages configurable per team/ART, or standardized?
3. **Performance**: What's the typical dataset size for stories in a single PI?
4. **Existing Code**: Can story endpoints reuse existing feature analysis logic with minimal changes?
5. **API Design**: Any concerns with the proposed endpoint structure or naming?

## Success Criteria

### Functional Requirements
- ✅ Story-level bottleneck analysis matches feature-level analysis depth
- ✅ Team filtering works correctly for story endpoints
- ✅ API response times < 2 seconds for typical queries (1 PI, 1 team)
- ✅ Story and feature data can be compared side-by-side

### Non-Functional Requirements
- ✅ API documentation updated with story endpoints
- ✅ Sample code/curl examples provided
- ✅ Endpoint available in all environments (dev, staging, prod)
- ✅ Monitoring and logging in place

## Contact Information

**Evaluation Coach Team**
- Integration Lead: [Your Name]
- Technical Contact: [Your Email]
- Project Repository: Evaluation_coach

**Next Steps**
1. Review requirements with DL Webb App team
2. Clarify any questions about data structures or calculations
3. Agree on timeline for Phase 1 implementation
4. Schedule integration testing session

---

**Document Version**: 1.0  
**Last Updated**: January 11, 2026  
**Review Status**: Ready for DL Webb App Team Review
