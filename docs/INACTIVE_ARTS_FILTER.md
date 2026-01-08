# Inactive ARTs Filter Feature

## Overview

This feature allows you to show or hide ARTs that have **zero features delivered** in the Dashboard ART Comparison table. This is configurable via the Admin panel and persists across server restarts.

## Problem Solved

The Dashboard was showing **all 28 ARTs** from DL Webb App, including 5 ARTs with 0 features delivered:
- BCPF
- CAF
- CITPF
- COMSF
- COSART

This made the dashboard cluttered and harder to focus on active ARTs. The DL Webb App's `delivery_analysis.html` also shows all ARTs, so this feature benefits both systems.

## Solution

### Database Configuration
- Added `show_inactive_arts` boolean configuration to `RuntimeConfiguration` table
- Stored as string ("true"/"false") with `config_type = "bool"`
- Persists across server restarts

### Backend Changes
1. **Updated `api_models.py`**: Added `show_inactive_arts: bool = True` to `AdminConfigResponse`
2. **Updated `database.py`**: Changed `config_value` from `Float` to `Text` to support boolean/string values
3. **Updated `main.py`**:
   - `/api/admin/config` (GET): Returns current `show_inactive_arts` setting
   - `/api/admin/config/display` (POST): Saves display options to database
   - `/api/v1/dashboard` (GET): Filters out ARTs with `features_delivered == 0` when config is false

### Frontend Changes
- **Updated `admin.html`**: Added "Display Options" section with checkbox toggle
- Checkbox labeled: "Show Inactive ARTs (ARTs with 0 features delivered)"
- Save button persists the setting to database
- Prompts user to refresh dashboard after saving

## Usage

### Configure via Admin Panel

1. Go to **Admin Configuration** page (http://localhost:8800/admin.html)
2. Scroll to **Display Options** section
3. Check/uncheck **"Show Inactive ARTs"** checkbox:
   - ✅ **Checked** (default): Shows all 28 ARTs including inactive ones
   - ☐ **Unchecked**: Shows only 23 active ARTs (hides 5 with 0 features)
4. Click **"Save Display Options"**
5. Refresh the Dashboard to see changes

### API Usage

#### Get Current Configuration
```bash
curl http://localhost:8850/api/admin/config
```

Response includes:
```json
{
  "show_inactive_arts": true,
  ...
}
```

#### Update Configuration
```bash
curl -X POST http://localhost:8850/api/admin/config/display \
  -H "Content-Type: application/json" \
  -d '{"show_inactive_arts": false}'
```

#### Dashboard Automatically Filters
```bash
# With show_inactive_arts = false
curl http://localhost:8850/api/v1/dashboard

# Returns only 23 ARTs (excludes BCPF, CAF, CITPF, COMSF, COSART)
```

## Testing

### Test 1: Hide Inactive ARTs
```bash
# Set to false
curl -X POST http://localhost:8850/api/admin/config/display \
  -H "Content-Type: application/json" \
  -d '{"show_inactive_arts": false}'

# Check dashboard
curl -s http://localhost:8850/api/v1/dashboard | python3 -c "
import sys, json
arts = json.load(sys.stdin)['art_comparison']
print(f'Total ARTs: {len(arts)}')
print(f'Inactive: {len([a for a in arts if a[\"features_delivered\"] == 0])}')"

# Expected output:
# Total ARTs: 23
# Inactive: 0
```

### Test 2: Show All ARTs
```bash
# Set to true
curl -X POST http://localhost:8850/api/admin/config/display \
  -H "Content-Type: application/json" \
  -d '{"show_inactive_arts": true}'

# Check dashboard
curl -s http://localhost:8850/api/v1/dashboard | python3 -c "
import sys, json
arts = json.load(sys.stdin)['art_comparison']
print(f'Total ARTs: {len(arts)}')
print(f'Inactive: {len([a for a in arts if a[\"features_delivered\"] == 0])}')"

# Expected output:
# Total ARTs: 28
# Inactive: 5
```

### Test 3: Persistence Across Restarts
```bash
# Set configuration
curl -X POST http://localhost:8850/api/admin/config/display \
  -H "Content-Type: application/json" \
  -d '{"show_inactive_arts": false}'

# Restart backend
./stop.sh && ./start.sh

# Verify configuration persisted
curl -s http://localhost:8850/api/admin/config | grep show_inactive_arts

# Expected: "show_inactive_arts": false
```

## For DL Webb App Integration

To add the same functionality to DL Webb App:

1. Add a checkbox in the filters section of `delivery_analysis.html`
2. Filter the `art_comparison` array client-side or server-side
3. Store preference in localStorage or backend configuration

Example JavaScript:
```javascript
// In delivery_analysis.html
const showInactiveArts = document.getElementById('showInactiveArts').checked;

let displayedARTs = artComparisonData;
if (!showInactiveArts) {
    displayedARTs = artComparisonData.filter(art => 
        art.features_delivered > 0
    );
}
```

## Benefits

1. **Cleaner Dashboard**: Focus on active ARTs only
2. **Configurable**: Users can toggle based on their needs
3. **Persistent**: Setting survives server restarts
4. **Matches DL Webb App**: Both systems now show 28 ARTs by default
5. **Flexible**: Easy to expand for other display options

## Files Modified

- `backend/api_models.py` - Added `show_inactive_arts` field
- `backend/database.py` - Updated `RuntimeConfiguration.config_value` to Text
- `backend/main.py` - Added filtering logic and endpoints
- `frontend/admin.html` - Added UI toggle

## Future Enhancements

- Add similar filters for other metrics (e.g., filter by minimum throughput)
- Add PI-level filtering options
- Add team-level inactive filtering
- Export filtered data to Excel
