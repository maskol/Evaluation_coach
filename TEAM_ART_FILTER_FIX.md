# Team View ART Filter Enhancement

## Problem
When filtering by ART in Team view, the team dropdown was showing ALL teams from all ARTs, not just teams belonging to the selected ART. This made it confusing and difficult to select the correct team.

Example: If user selected ART "UCART", the team dropdown still showed teams from "ACET", "FDIST", etc.

## Root Cause
The team filtering logic existed in `updateTeamSelector()` function but was only called during initial page load. When the user changed the ART selection, the team dropdown was not refreshed to reflect the new filter.

## Solution
Enhanced the ART selector change event to:
1. Detect when in Team view
2. Clear the previously selected team (since it might not belong to the new ART)
3. Call `updateTeamSelector()` to refresh the team dropdown with filtered teams
4. Also call `updateTeamSelector()` when switching to Team scope

### Changes Made

#### File: `frontend/app.js`

**1. ART Selector Change Handler (Line ~3673)**
```javascript
artSelector.addEventListener('change', (e) => {
    appState.selectedART = e.target.value;
    
    // Update team dropdown if in team view to show only teams from selected ART
    if (appState.scope === 'team') {
        // Clear team selection when ART changes (team might not belong to new ART)
        appState.selectedTeam = '';
        updateTeamSelector();
    }
    
    updateContext();
    // Reload dashboard when ART is selected in ART view
    if (appState.scope === 'art') {
        loadDashboardData();
    }
});
```

**2. Scope Selection Function (Line ~836)**
```javascript
} else if (scope === 'team') {
    artSelection.style.display = 'block';
    teamSelection.style.display = 'block';
    analysisLevelSelection.style.display = 'block';
    
    // Update team dropdown to show only teams from selected ART
    updateTeamSelector();
}
```

## Existing Logic (Already Correct)

The `updateTeamSelector()` function already had the correct filtering logic:

```javascript
function updateTeamSelector() {
    // Clear existing options
    teamSelector.innerHTML = '<option value="">-- Select Team --</option>';

    // Filter teams by selected ART if in team view
    let teamsToShow = appState.allTeams;
    if (appState.scope === 'team' && appState.selectedART) {
        // Filter teams that belong to the selected ART
        teamsToShow = appState.allTeams.filter(team => team.art_key === appState.selectedART);
    }

    // Add filtered teams to selector
    teamsToShow.forEach(team => {
        const option = document.createElement('option');
        option.value = team.team_name;
        option.textContent = team.team_name;
        teamSelector.appendChild(option);
    });

    // Restore previous selection if still valid
    if (currentSelection && teamsToShow.some(team => team.team_name === currentSelection)) {
        teamSelector.value = currentSelection;
    }
}
```

## User Experience

### Before Fix
1. User switches to Team View
2. User selects ART "UCART" from dropdown
3. Team dropdown still shows ALL teams (Loke, Adamo, Odin, Thor, etc.) from all ARTs ❌
4. User has to remember which teams belong to UCART

### After Fix
1. User switches to Team View  
   → Team dropdown shows all teams (no ART selected yet)
2. User selects ART "UCART" from dropdown  
   → Team dropdown automatically refreshes ✅  
   → Shows ONLY teams with art_key="UCART" (e.g., Loke, Adamo)  
   → Previously selected team is cleared
3. User sees only relevant teams for the selected ART ✅

## Testing Checklist

- [x] Switch to Team View → team dropdown shows all teams
- [x] Select an ART → team dropdown filters to show only that ART's teams
- [x] Select a team → team is selected
- [x] Change to different ART → team selection is cleared, dropdown shows new ART's teams
- [x] Clear ART selection → team dropdown shows all teams again
- [x] Switch between Portfolio/ART/Team views → team dropdown behaves correctly

## Impact
- ✅ Improved user experience when filtering by ART in Team view
- ✅ Reduces confusion by showing only relevant teams
- ✅ Prevents selecting invalid team/ART combinations
- ✅ Automatic clearing of team selection when ART changes
- ✅ Works seamlessly with existing filtering logic
