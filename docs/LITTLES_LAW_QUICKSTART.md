# Quick Start: Little's Law Insight

## What is it?

An AI insight that analyzes your PI performance using Little's Law to identify optimal WIP levels and improve flow efficiency.

**Little's Law**: L = λ × W
- **L** = WIP (Work in Progress)  
- **λ** = Throughput (features/day)
- **W** = Lead Time (days/feature)

## Prerequisites

1. DL Webb App running on `http://localhost:8000`
2. Lead-time service enabled in your `.env`:
   ```bash
   LEADTIME_SERVER_ENABLED=true
   LEADTIME_SERVER_URL=http://localhost:8000
   ```

## How to Use

### Option 1: Via API

Generate insights for a specific PI:

```bash
curl "http://localhost:8850/api/insights?scope=pi&scope_id=24Q4"
```

Generate insights for portfolio (analyzes most recent PI):

```bash
curl "http://localhost:8850/api/insights?scope=portfolio"
```

### Option 2: Via Frontend

1. Open the Evaluation Coach dashboard
2. Navigate to **Insights** section
3. Select scope: **PI** or **Portfolio**
4. The Little's Law insight will appear automatically if data is available

### Option 3: Test Script

Run the dedicated test script:

```bash
./test_littles_law_insight.py
```

Or with Python:

```bash
python test_littles_law_insight.py
```

## What You'll Get

The insight provides:

✅ **Metrics**:
- Current throughput (features/day)
- Average lead time (days)
- Predicted WIP level
- Flow efficiency percentage

✅ **Analysis**:
- Identification of bottlenecks
- Wait time vs. active work time
- Gap between current and optimal WIP

✅ **Recommendations**:
- WIP limit targets
- Actions to improve flow efficiency
- Monitoring strategies

## Example Output

```
📊 Little's Law Analysis for PI 24Q4

🎯 Severity: WARNING
📈 Confidence: 88%

📝 Observation:
42 features completed in 84 days. Throughput = 0.50 features/day.
Average Lead Time = 50.2 days. Predicted WIP = 25.1 features.
Flow Efficiency = 38.5%

💡 Interpretation:
Low flow efficiency indicates features spend 30.9 days waiting vs
19.3 days in active work. To achieve 30-day lead time, reduce WIP
from 25.1 to 15.0 features.

✅ Recommended Actions:
1. [short-term] Implement WIP limits: cap active features at 15
2. [medium-term] Eliminate sources of wait time
3. [ongoing] Monitor metrics weekly
```

## Troubleshooting

### "Lead-time service not available"
- Ensure DL Webb App is running: `http://localhost:8000`
- Check `.env` has `LEADTIME_SERVER_ENABLED=true`
- Test connection: `curl http://localhost:8000/api/flow_leadtime`

### "Insufficient data for Little's Law analysis"
- Ensure PI has at least 5 completed features
- Verify features have `total_leadtime > 0`
- Check PI identifier is correct (e.g., "24Q4")

### "No flow data available for PI"
- Check available PIs: `curl http://localhost:8000/api/filters`
- Verify PI data exists in DL Webb App database

## Files Modified

- **backend/services/insights_service.py**: Added `_generate_littles_law_insight()` method
- **test_littles_law_insight.py**: Test script for the feature
- **docs/LITTLES_LAW_INSIGHT.md**: Full documentation

## Learn More

- Full documentation: [LITTLES_LAW_INSIGHT.md](LITTLES_LAW_INSIGHT.md)
- Lead-time integration: [LEADTIME_INTEGRATION.md](LEADTIME_INTEGRATION.md)
- Little's Law theory: https://en.wikipedia.org/wiki/Little%27s_law
