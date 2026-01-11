# Story-Level Insights Troubleshooting Guide

**Error**: 500 Internal Server Error when selecting Story-Level analysis

---

## Problem

When selecting "Story Level" in the Analysis Level dropdown, the following error occurs:

```
POST http://localhost:8850/api/v1/insights/generate?analysis_level=story 500 (Internal Server Error)
```

The root cause is that the **DL Webb App backend** (port 8000) is returning 500 errors for story-level API endpoints.

---

## Root Cause Analysis

### Test Results

Running `debug_story_api.py` shows:

```
❌ FAILED: Server error '500 Internal Server Error' for:
  - http://localhost:8000/api/story_analysis_summary
  - http://localhost:8000/api/story_pip_data  
  - http://localhost:8000/api/story_waste_analysis
```

### Why This Happens

The story-level insights feature in **Evaluation Coach** is working correctly, but it depends on story-level API endpoints in the **DL Webb App** backend. These endpoints may:

1. Not be implemented yet in the DL Webb App
2. Be implemented but have errors
3. Be implemented but have no data for the selected filters

---

## Solution Steps

### Step 1: Verify DL Webb App Has Story Endpoints

Check if the DL Webb App has the story endpoints implemented:

```bash
# Test if endpoints exist
curl http://localhost:8000/api/story_analysis_summary?pis=26Q1
curl http://localhost:8000/api/story_pip_data?pi=26Q1
curl http://localhost:8000/api/story_waste_analysis?pis=26Q1
```

**Expected**: Should return JSON data or at least a proper error message, not 500.

### Step 2: Check DL Webb App Logs

Look at the DL Webb App backend logs to see the actual error:

```bash
cd /Users/maskol/Local-Development/DL_Webb_APP
# Check logs for errors
tail -f logs/backend.log  # or wherever DL Webb App logs are
```

### Step 3: Verify Story Data Exists

Check if story data exists in the database:

```sql
-- Connect to DL Webb App database
SELECT COUNT(*) FROM story_flow_leadtime 
WHERE pi = '26Q1' AND art_name = 'UCART' AND development_team = 'Loke';

SELECT COUNT(*) FROM story_leadtime_thr_data
WHERE pi = '26Q1';
```

**Expected**: Should return > 0 records

### Step 4: Update DL Webb App

If the endpoints don't exist, you need to deploy the story-level API implementation to DL Webb App.

According to the attached `CHANGELOG_STORY_API.md`, these files should exist:

**DL Webb App Files Needed**:
- `backend/story_analysis_engine.py` (~460 lines)
- Endpoints added to `backend/main_sqlmodel.py`:
  - `GET /api/story_analysis_summary`
  - `GET /api/story_pip_data`
  - `GET /api/story_waste_analysis`

**To deploy**:
```bash
cd /Users/maskol/Local-Development/DL_Webb_APP

# Check if story_analysis_engine.py exists
ls -la backend/story_analysis_engine.py

# Check if endpoints are registered
grep "story_analysis_summary" backend/main_sqlmodel.py
grep "story_pip_data" backend/main_sqlmodel.py
grep "story_waste_analysis" backend/main_sqlmodel.py

# Restart DL Webb App
./stop.sh && ./start.sh
```

---

## Workaround (Immediate)

Until the DL Webb App story endpoints are fixed, the **Evaluation Coach now provides a helpful error message**:

When you select "Story Level", you'll see:

```
Title: Story-Level Insights Not Available
Severity: info
Observation: Story-level insight analysis is not currently available.
Interpretation: The DL Webb App backend may not have the story-level API 
                endpoints implemented yet, or there may be no story data 
                for the selected filters.
Recommended Actions:
  1. Verify DL Webb App has story-level endpoints
  2. Verify story data exists for selected filters
  3. Switch to Feature-Level analysis as workaround
```

**To use workaround**:
1. Change Analysis Level dropdown to "Feature"
2. View feature-level insights instead
3. Wait for DL Webb App story endpoints to be deployed

---

## Fix Implementation

I've updated the Evaluation Coach backend to handle this error gracefully:

**File**: `backend/main.py` (line ~1034)

**Changes**:
- Added try/catch around story API calls
- Added detailed logging of each API call
- Returns helpful error message if story endpoints fail
- Suggests next steps in the error message

**Result**:
- No more silent 500 errors
- User sees clear explanation
- Suggested actions provided
- System doesn't crash

---

## Testing the Fix

### Test 1: Error Handling Works

```bash
cd /Users/maskol/Local-Development/evaluation_coach/Evaluation_coach
source venv/bin/activate

# Start Evaluation Coach
./start_backend.sh

# In browser:
# 1. Go to http://localhost:8001
# 2. Select Analysis Level: "Story"
# 3. Click generate insights
# 4. Should see helpful error message (not silent 500)
```

### Test 2: Verify Debug Script

```bash
python debug_story_api.py
```

**Expected Output**:
```
❌ FAILED: Server error '500 Internal Server Error' for url...
```

This confirms the issue is with DL Webb App, not Evaluation Coach.

---

## Next Steps

### For DL Webb App Team

1. **Deploy story endpoints** from `CHANGELOG_STORY_API.md`
2. **Import story data** to `story_flow_leadtime` table
3. **Test endpoints** with curl/Postman
4. **Verify** no 500 errors

### For Evaluation Coach Users

1. **Use Feature-Level** analysis until story endpoints are ready
2. **Monitor** DL Webb App deployment status
3. **Re-test** story-level once DL Webb App is updated

---

## Technical Details

### API Call Flow

```
User clicks "Generate Insights" (Story Level)
    ↓
Evaluation Coach: POST /api/v1/insights/generate?analysis_level=story
    ↓
Evaluation Coach backend: main.py line 1034
    ↓
Try to call DL Webb App:
    - GET http://localhost:8000/api/story_analysis_summary
    - GET http://localhost:8000/api/story_pip_data  
    - GET http://localhost:8000/api/story_waste_analysis
    ↓
❌ DL Webb App returns 500 error
    ↓
Evaluation Coach catches error
    ↓
Returns helpful error message to user
```

### Error Logs Location

**Evaluation Coach logs**:
- Console output when running `./start_backend.sh`
- Shows: "❌ Story-level insights failed: Server error..."

**DL Webb App logs**:
- Console output of DL Webb App backend
- Should show actual database/Python error

---

## FAQ

**Q: Why can't Evaluation Coach fix this?**  
A: Evaluation Coach is the client. It can only call APIs that DL Webb App provides. The story endpoints must exist and work in DL Webb App first.

**Q: Is the Evaluation Coach code working?**  
A: Yes! Tests pass with sample data. The issue is the DL Webb App API availability.

**Q: Can I still use Feature-Level insights?**  
A: Yes! Feature-level analysis works perfectly. Just select "Feature" instead of "Story".

**Q: When will story-level work?**  
A: Once DL Webb App deploys the story endpoints and imports story data.

**Q: How do I know when it's fixed?**  
A: Run `python debug_story_api.py`. When you see ✅ SUCCESS instead of ❌ FAILED, it's working.

---

## Status

- ✅ Evaluation Coach story insights implementation: COMPLETE
- ✅ Evaluation Coach error handling: COMPLETE
- ⏳ DL Webb App story endpoints: PENDING DEPLOYMENT
- ⏳ Story data in database: PENDING VERIFICATION

---

## Contact

**For Evaluation Coach issues**: This repository  
**For DL Webb App issues**: DL Webb App repository  
**For story endpoint deployment**: DL Webb App team

---

**Last Updated**: January 11, 2026  
**Evaluation Coach Version**: 1.0.0 (Story Insights Ready)  
**Waiting On**: DL Webb App story endpoint deployment
