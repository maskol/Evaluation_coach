# Insight Export to Excel - Bug Fix

## Issue
When clicking the "💾 Export" button on an AI Insight card, the system was falling back to JSON export instead of producing an Excel file.

## Root Cause
**Frontend API URL Error:** The export function was calling an incorrect URL with duplicate `/api` path segments:
- ❌ **Incorrect:** `http://localhost:8850/api/api/v1/insights/export`
- ✅ **Correct:** `http://localhost:8850/api/v1/insights/export`

Since `API_BASE_URL` is already defined as `'http://localhost:8850/api'`, appending `/api/v1/insights/export` created the duplicate.

## Fix Applied
**File:** `frontend/app.js` (Line 1944)

**Changed:**
```javascript
const response = await fetch(`${API_BASE_URL}/api/v1/insights/export?${queryParams}`, {
```

**To:**
```javascript
const response = await fetch(`${API_BASE_URL}/v1/insights/export?${queryParams}`, {
```

## Testing Performed

### 1. Backend Endpoint Verification
```bash
# Test with actual insight data
curl -X POST "http://localhost:8850/api/v1/insights/export?pis=26Q1&analysis_level=feature" \
  -H "Content-Type: application/json" \
  -d @/Users/maskol/Downloads/insight-critical-bottleneck-in-in-uat-stage-2026-01-12.json \
  -o /Users/maskol/Downloads/test_export.xlsx

# Result: ✅ 200 OK, Valid Excel file (8.3KB)
```

### 2. File Validation
```bash
file /Users/maskol/Downloads/test_export.xlsx
# Result: Microsoft Excel 2007+
```

### 3. URL Endpoint Tests
```bash
# Old incorrect URL - returns 404
curl http://localhost:8850/api/api/v1/insights/export
# Result: 404 Not Found

# Corrected URL - endpoint exists
curl -X POST http://localhost:8850/api/v1/insights/export  
# Result: 422 Unprocessable Entity (correct - missing request body)
```

## Expected Behavior (After Fix)

### When Clicking "💾 Export" Button:
1. ✅ Frontend sends POST request to correct endpoint
2. ✅ Backend extracts issue keys from insight evidence and root causes
3. ✅ Backend fetches all related features/stories from LeadTime service
4. ✅ Backend creates Excel file with 5 sheets:
   - **Sheet 1:** Insight Summary
   - **Sheet 2:** Related Features/Stories (with all mentioned items)
   - **Sheet 3:** Observation & Interpretation  
   - **Sheet 4:** Root Causes
   - **Sheet 5:** Recommended Actions
5. ✅ Browser automatically downloads Excel file

### Excel File Contents
Each related feature/story includes:
- Issue Key (e.g., UCART-2228)
- Category (Stuck Item, Flow Item, or Mentioned in Insight)
- ART
- Team
- Current Stage
- Days in Stage
- Total Lead Time
- Summary
- Status
- PI

## Files Modified
- ✅ `frontend/app.js` - Fixed API endpoint URL (line 1944)

## How to Test
1. Start the application: `./start.sh`
2. Navigate to **Insights** tab
3. Generate AI insights
4. Click **"💾 Export"** button on any insight card
5. Verify Excel file downloads automatically
6. Open Excel file and verify it contains 5 sheets with proper data

## Notes
- The backend functionality was already working correctly
- Only the frontend URL needed correction
- The executive summary export (`/v1/insights/export-summary`) was already using the correct URL pattern
