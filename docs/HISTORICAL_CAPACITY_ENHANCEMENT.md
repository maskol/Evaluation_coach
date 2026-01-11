# Historical Capacity Baseline - Little's Law Enhancement

## Overview

Enhanced the Little's Law analysis to incorporate **historical throughput data as a capacity baseline**, using 8+ PIs of historical data from `leadtime_thr_data` to provide context for current performance.

## What Changed

### 1. New Function: `_calculate_historical_capacity_baseline()`

**Location:** `backend/agents/nodes/littles_law_analyzer.py`

Calculates capacity baseline metrics from historical PIs:
- Average throughput per PI and per day
- Throughput variability (min, max, stddev)
- Historical lead time averages
- PI-by-PI breakdown

**Default:** Analyzes last 8 PIs for robust baseline

### 2. Enhanced Metrics Structure

Added `capacity_analysis` section to Little's Law metrics:

```python
{
    "historical_avg_throughput_per_day": 0.45,  # features/day
    "historical_avg_leadtime": 52.3,            # days
    "throughput_vs_baseline_pct": +12.5,        # % change
    "leadtime_vs_baseline_pct": -8.2,           # % change
    "capacity_utilization_pct": 95.3,           # % of baseline
    "pis_in_baseline": 8,
    "baseline_range": "32-48 features/PI"
}
```

### 3. Enhanced Insights

#### Observations
Now includes:
- Historical baseline comparison
- Capacity utilization percentage
- Throughput trend vs history

**Example:**
> "Historical Baseline (8 PIs): 0.45 features/day average. Current throughput is 12.5% above historical capacity (95.3% capacity utilization)."

#### Interpretations
Automatically interprets:
- **Throughput decline** >20%: Flags capacity constraints
- **Throughput increase** >20%: Highlights improved capacity
- **Lead time increase** >20%: Indicates growing inefficiency
- **Lead time improvement** >10%: Recognizes process improvements

#### Recommended Actions
New capacity-based recommendations:
- **Throughput decline >20%**: Investigate capacity loss
- **Over-capacity (>120%)**: Reduce commitments to sustainable levels
- **Under-capacity (<70%)**: Investigate underutilization

### 4. RAG Enhancement

Added historical capacity context to the AI analysis prompt:
- Historical vs current comparison
- Capacity utilization analysis
- Sustainability assessment
- Realistic capacity planning guidance

## Benefits

### 1. **Realistic Capacity Planning**
Historical data provides evidence-based capacity proxy instead of guessing team velocity

### 2. **Trend Detection**
Identifies capacity improvements or degradation over time

### 3. **Sustainability Assessment**
Flags unsustainable delivery rates (>120% of historical capacity)

### 4. **Root Cause Analysis**
Significant deviations from baseline trigger investigation recommendations

### 5. **Evidence-Based Commitments**
Teams can use historical throughput to commit realistically in PI planning

## Usage Example

### Before Enhancement
```
Throughput (λ) = 0.52 features/day
Average Lead Time (W) = 48.2 days
```

### After Enhancement
```
Throughput (λ) = 0.52 features/day
Historical Baseline (8 PIs): 0.45 features/day average
Current throughput is 15.6% above historical capacity (115.6% utilization)

Interpretation: Throughput has increased 15.6% above historical baseline,
demonstrating improved delivery capacity.
```

## Technical Details

### Data Source
- **Table:** `leadtime_thr_data` (DL Webb App)
- **Scope:** Last 8 PIs (configurable via `lookback_pis` parameter)
- **Filters:** Respects ART filters when provided

### Calculation Logic

```python
# Average throughput per PI
avg_throughput_per_pi = total_features / num_pis

# Throughput per day (84-day PIs)
avg_throughput_per_day = avg_throughput_per_pi / 84

# Capacity utilization
capacity_utilization = (current_throughput / historical_avg) * 100

# Throughput change
throughput_vs_baseline = ((current / historical) - 1) * 100
```

### Performance
- **Time:** ~1-2 seconds for 8 PIs of data
- **Data Volume:** Typically 200-400 features per PI
- **Caching:** Not currently cached (could be optimized)

## Configuration

### Lookback Period
Default: 8 PIs

To change:
```python
historical_baseline = _calculate_historical_capacity_baseline(
    leadtime_service,
    pi_to_analyze,
    art_filter,
    lookback_pis=12  # Use 12 PIs instead
)
```

### Minimum Data Requirements
- At least 1 historical PI with data
- Gracefully degrades if historical data unavailable

## Integration Points

### 1. Little's Law Analyzer Node
Main integration point - calculates baseline before metrics calculation

### 2. Flow Insights
Observations and interpretations include historical context

### 3. RAG Enhancement
Historical context provided to LLM for expert analysis

### 4. Recommended Actions
Capacity-based actions generated automatically

## Future Enhancements

### Short-term
1. **Seasonal Adjustments**: Account for holiday PIs or known anomalies
2. **Confidence Intervals**: Statistical bounds on capacity estimates
3. **Caching**: Cache historical baselines to improve performance

### Medium-term
1. **Trend Charts**: Visualize throughput trends over time
2. **Capacity Forecasting**: Predict future capacity based on trends
3. **ART Comparisons**: Compare ARTs against each other's baselines

### Long-term
1. **Machine Learning**: Predict capacity based on multiple factors
2. **What-If Scenarios**: Model impact of team changes on capacity
3. **Automated Capacity Planning**: Generate PI commitments from baseline

## Metrics to Watch

Key indicators for monitoring this feature:

1. **Baseline Stability**: Historical stddev should be <20% of mean
2. **Capacity Utilization**: Target 80-100% for sustainable delivery
3. **Throughput Trends**: Watch for consistent >20% changes
4. **Lead Time Correlation**: Should inversely correlate with throughput

## Related Documentation

- [LITTLES_LAW_AGENT.md](LITTLES_LAW_AGENT.md) - Main Little's Law documentation
- [LITTLES_LAW_ARCHITECTURE.md](LITTLES_LAW_ARCHITECTURE.md) - Technical architecture
- [LEADTIME_INTEGRATION.md](LEADTIME_INTEGRATION.md) - Data integration details

---

**Last Updated:** January 10, 2026  
**Author:** Evaluation Coach Development Team  
**Version:** 1.0
