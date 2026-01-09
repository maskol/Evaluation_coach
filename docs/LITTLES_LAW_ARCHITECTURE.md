# Little's Law Insight - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LITTLE'S LAW INSIGHT GENERATION                          │
└─────────────────────────────────────────────────────────────────────────────┘

1. TRIGGER
   ┌──────────────────────────────────────┐
   │  User/API Request                     │
   │  - scope: "pi" or "portfolio"        │
   │  - scope_id: "24Q4" (optional)       │
   └──────────────┬───────────────────────┘
                  │
                  ▼
2. INSIGHTS SERVICE (insights_service.py)
   ┌──────────────────────────────────────┐
   │  generate_insights()                 │
   │  ├─ Check scope type                │
   │  ├─ Determine PI to analyze          │
   │  └─ Call Little's Law generator      │
   └──────────────┬───────────────────────┘
                  │
                  ▼
3. LEADTIME SERVICE (leadtime_service.py)
   ┌──────────────────────────────────────┐
   │  LeadTimeService()                   │
   │  ├─ is_available() check             │
   │  ├─ get_filters() - fetch PIs        │
   │  └─ get_flow_leadtime(pi=PI)         │
   └──────────────┬───────────────────────┘
                  │
                  ▼
4. DL WEBB APP API
   ┌──────────────────────────────────────┐
   │  http://localhost:8000               │
   │  GET /api/flow_leadtime?pi=24Q4      │
   │                                      │
   │  Returns: [                          │
   │    {                                 │
   │      "issue_key": "ACEART-123",     │
   │      "status": "Done",              │
   │      "total_leadtime": 45.3,        │
   │      "in_progress": 18.2,           │
   │      "in_analysis": 5.1,            │
   │      ...                             │
   │    },                                │
   │    ...                               │
   │  ]                                   │
   └──────────────┬───────────────────────┘
                  │
                  ▼
5. LITTLE'S LAW CALCULATION
   ┌──────────────────────────────────────┐
   │  _generate_littles_law_insight()     │
   │                                      │
   │  Filter: completed features          │
   │  ├─ status in ['Done', 'Deployed']  │
   │  └─ total_leadtime > 0               │
   │                                      │
   │  Calculate:                          │
   │  ├─ λ = features / 84 days           │
   │  ├─ W = avg(total_leadtime)          │
   │  ├─ L = λ × W                        │
   │  ├─ Flow Efficiency = active/total   │
   │  └─ Optimal WIP = λ × 30 days        │
   │                                      │
   │  Determine Severity:                 │
   │  ├─ Critical: W>60 or FE<30%        │
   │  ├─ Warning:  W>45 or FE<40%        │
   │  ├─ Info:     W>30 or FE<50%        │
   │  └─ Success:  W≤30 and FE≥50%       │
   └──────────────┬───────────────────────┘
                  │
                  ▼
6. INSIGHT STRUCTURE
   ┌──────────────────────────────────────┐
   │  {                                   │
   │    "title": "Little's Law...",       │
   │    "severity": "warning",            │
   │    "confidence": 88.0,               │
   │    "scope": "pi",                    │
   │    "scope_id": "24Q4",               │
   │                                      │
   │    "observation": "...",             │
   │    "interpretation": "...",          │
   │                                      │
   │    "root_causes": [                  │
   │      {                                │
   │        "description": "High wait...",│
   │        "evidence": [...],            │
   │        "confidence": 90.0            │
   │      }                                │
   │    ],                                │
   │                                      │
   │    "recommended_actions": [          │
   │      {                                │
   │        "timeframe": "short-term",    │
   │        "description": "Implement...",│
   │        "owner": "Scrum Masters",     │
   │        "success_signal": "..."       │
   │      }                                │
   │    ],                                │
   │                                      │
   │    "expected_outcomes": {            │
   │      "metrics_to_watch": [...],      │
   │      "timeline": "2-3 PIs",          │
   │      "risks": [...]                  │
   │    }                                 │
   │  }                                   │
   └──────────────┬───────────────────────┘
                  │
                  ▼
7. SAVE TO DATABASE
   ┌──────────────────────────────────────┐
   │  database.py - Insight table         │
   │  ├─ Insert new insight record        │
   │  ├─ status = "active"                │
   │  └─ created_at = now()               │
   └──────────────┬───────────────────────┘
                  │
                  ▼
8. RETURN TO USER
   ┌──────────────────────────────────────┐
   │  API Response / Frontend Display     │
   │  ├─ InsightResponse model            │
   │  ├─ Formatted for display            │
   │  └─ Includes all sections            │
   └──────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         LITTLE'S LAW FORMULA                                │
└─────────────────────────────────────────────────────────────────────────────┘

    L = λ × W

    Where:
    ┌─────────────────────────────────────────┐
    │  L  = Work in Progress (WIP)            │
    │       Average # features being worked   │
    │       Example: 25 features              │
    └─────────────────────────────────────────┘
              ▲
              │
              │ multiply
              │
    ┌─────────┴───────────┬───────────────────┐
    │                     │                   │
    │  λ (lambda)         │        W          │
    │  = Throughput       │        = Lead Time│
    │  = features/day     │        = days     │
    │                     │                   │
    │  Example:           │        Example:   │
    │  0.5 features/day   │        50 days    │
    └─────────────────────┴───────────────────┘

    CALCULATION:
    L = 0.5 features/day × 50 days = 25 features

    TO REDUCE LEAD TIME TO 30 DAYS:
    Optimal L = 0.5 features/day × 30 days = 15 features
    → Reduce WIP by 10 features!


┌─────────────────────────────────────────────────────────────────────────────┐
│                      FLOW EFFICIENCY CALCULATION                            │
└─────────────────────────────────────────────────────────────────────────────┘

    Flow Efficiency = (Active Time / Total Lead Time) × 100%

    ┌─────────────────────────────────────────┐
    │  Active Time (Working)                  │
    │  = in_analysis + in_progress            │
    │    + in_reviewing                       │
    │  Example: 19.3 days                     │
    └─────────────────────────────────────────┘
                    ▲
                    │
                    │ divide by
                    │
    ┌───────────────▼─────────────────────────┐
    │  Total Lead Time                        │
    │  = in_backlog + in_planned +            │
    │    in_analysis + in_progress +          │
    │    in_reviewing + in_sit + in_uat +     │
    │    ready_for_deployment                 │
    │  Example: 50.2 days                     │
    └─────────────────────────────────────────┘

    CALCULATION:
    Flow Efficiency = (19.3 / 50.2) × 100% = 38.5%

    INTERPRETATION:
    - 38.5% = Time actively working
    - 61.5% = Time waiting (waste!)
    - 30.9 days of waiting vs 19.3 days working

    TARGET: >50% flow efficiency
```
