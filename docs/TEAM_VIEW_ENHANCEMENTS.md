# Team View Enhancements - Feature and Story Level Analysis

## Overview

Enhanced the Team View to support filtering teams by ART and selecting between Feature-level and Story-level analysis with different process stages.

## Changes Implemented

### 1. Backend Changes

#### New API Endpoint: `/api/teams/with-art`
- Returns teams with their ART mapping
- Enables filtering teams by ART in the frontend
- Response format:
```json
{
  "teams": [
    {
      "team_name": "API Developer Journey",
      "team_id": 1,
      "art_name": "Enabling Platform ART",
      "art_id": 104
    }
  ],
  "count": 235,
  "source": "DL Webb App"
}
```

#### Enhanced Lead-Time Client (`backend/integrations/leadtime_client.py`)
- Added `get_story_flow_leadtime()` method for user story-level data
- Story stages: `refinement`, `ready_for_development`, `in_development`, `in_review`, `ready_for_test`, `in_testing`, `ready_for_deployment`, `deployed`, `total_leadtime`

#### Enhanced Lead-Time Service (`backend/services/leadtime_service.py`)
- Added `get_story_leadtime_data()` method
- Supports fetching story-level lead-time data with team filtering

#### Enhanced Dashboard API (`backend/main.py`)
- Added `team` parameter for team selection
- Added `analysis_level` parameter (`feature` or `story`)
- Dashboard now switches between:
  - **Feature Level**: Uses `flow_leadtime` API with stages: `in_backlog`, `in_planned`, `in_analysis`, `in_progress`, `in_reviewing`, `in_sit`, `in_uat`, `ready_for_deployment`, `deployed`
  - **Story Level**: Uses `story_flow_leadtime` API with stages: `refinement`, `ready_for_development`, `in_development`, `in_review`, `ready_for_test`, `in_testing`, `ready_for_deployment`, `deployed`

### 2. Frontend Changes

#### Enhanced State Management (`frontend/app.js`)
- Added `allTeams` array to store teams with ART mapping
- Added `analysisLevel` property (`'feature'` or `'story'`)

#### New UI Components (`frontend/index.html`)
- Added **Analysis Level Selection** section (visible only in Team view):
  - Dropdown with "Feature Level" and "Story Level" options
  - Helpful description explaining the difference

#### Enhanced Team Filtering
- `updateTeamSelector()` function filters teams based on selected ART
- When ART is selected in Team view, only teams belonging to that ART are shown
- Team selection is reset when ART changes

#### Enhanced Context Display
- Shows current analysis level in Team view context
- Format: `Team | ART: [name] | Team: [name] | Level: Feature/Story`

#### Enhanced Dashboard Loading
- Passes `team` parameter when team is selected
- Passes `analysis_level` parameter in Team view
- Properly encodes team names in URL

### 3. Process Stage Differences

#### Feature Level (Epic-level work items)
Process stages from `flow_leadtime`:
1. `in_backlog` - Feature in backlog
2. `in_planned` - Feature planned
3. `in_analysis` - Under analysis
4. `in_progress` - Active development
5. `in_reviewing` - Code review
6. `in_sit` - System integration testing
7. `in_uat` - User acceptance testing
8. `ready_for_deployment` - Ready to deploy
9. `deployed` - Deployed to production

**Value-add time calculation**: `in_progress + in_reviewing`

#### Story Level (User story-level items)
Process stages from `story_flow_leadtime`:
1. `refinement` - Story refinement
2. `ready_for_development` - Ready for dev
3. `in_development` - Active development
4. `in_review` - Code review
5. `ready_for_test` - Ready for testing
6. `in_testing` - Testing in progress
7. `ready_for_deployment` - Ready to deploy
8. `deployed` - Deployed to production

**Value-add time calculation**: `in_development + in_review`

## Usage

### Selecting Team View with ART Filtering

1. Click **"👥 Team View"** in the sidebar
2. Select an **ART** from the dropdown (optional)
   - Team list will filter to show only teams in the selected ART
3. Select a **Team** from the filtered list
4. Choose **Analysis Level**:
   - **Feature Level**: Analyze epic-level work items (Features)
   - **Story Level**: Analyze user story-level items
5. Dashboard updates with team-specific metrics

### Example URLs

```
# Team view with Feature level
/api/v1/dashboard?scope=team&arts=ACEART&team=CCImprove&analysis_level=feature

# Team view with Story level
/api/v1/dashboard?scope=team&arts=ACEART&team=CCImprove&analysis_level=story
```

## Benefits

1. **Better Team Analysis**: Teams can be analyzed at the appropriate granularity
2. **ART-based Filtering**: Easier to find teams within a specific ART
3. **Flexible Analysis**: Switch between feature and story levels based on need
4. **Accurate Metrics**: Different process stages for different work item types
5. **Clear Context**: UI clearly shows which level is being analyzed

## Technical Notes

- Feature data comes from DL Webb App's `flow_leadtime` table
- Story data comes from DL Webb App's `story_flow_leadtime` table
- Team-ART mapping retrieved from DL Webb App's `/api/teams/` endpoint
- Both data sources support filtering by ART, PI, and team
- Flow efficiency calculation adapts to the selected analysis level

## Future Enhancements

1. Add PI-level team comparison (similar to ART comparison)
2. Support mixed Feature/Story analysis in Portfolio view
3. Add story-level bottleneck analysis
4. Create team-specific insights based on analysis level
5. Add trend analysis comparing feature vs story metrics
