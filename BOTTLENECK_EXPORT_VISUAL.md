# Bottleneck Export Fix - Visual Flow

## Before Fix (Problem)

```
┌─────────────────────────────────────────────────┐
│   Bottleneck Insight Generated                   │
│   "Critical Bottleneck in In Sit Stage"         │
│                                                  │
│   Evidence:                                      │
│   - "Mean duration: 87.0 days"                  │
│   - "Maximum observed: 153 days"                │
│   - "2 occurrences exceeding threshold"         │
│                                                  │
│   ❌ NO issue keys in evidence                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│   Export Function                                │
│                                                  │
│   Step 1: Extract issue keys from evidence      │
│   Result: issue_keys = {} (empty set)           │
│                                                  │
│   Step 2: Filter stuck_items by issue_keys      │
│   Result: related_items = [] (empty)            │
│                                                  │
│   Step 3: Create Excel                          │
│   Result: Total Items = 0 ❌                    │
└─────────────────────────────────────────────────┘
```

## After Fix (Solution)

```
┌─────────────────────────────────────────────────┐
│   Bottleneck Insight Generated                   │
│   "Critical Bottleneck in In Sit Stage"         │
│                                                  │
│   Evidence:                                      │
│   - "Mean duration: 87.0 days"                  │
│   - "Maximum observed: 153 days"                │
│   - "2 occurrences exceeding threshold"         │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│   Export Function (ENHANCED)                     │
│                                                  │
│   Step 1: Extract issue keys from evidence      │
│   Result: issue_keys = {} (empty set)           │
│                                                  │
│   Step 2: ⭐ NEW - Detect bottleneck insight   │
│   is_bottleneck_insight = True                   │
│   bottleneck_stage = "in_sit"                    │
│                                                  │
│   Step 3: ⭐ NEW - Get ALL stuck items for      │
│           that stage (bypass issue_keys filter)  │
│   Result: related_items = [                     │
│     UCART-1234 (153 days in in_sit),            │
│     UCART-5678 (87 days in in_sit)              │
│   ]                                              │
│                                                  │
│   Step 4: Create Excel                          │
│   Result: Total Items = 2 ✅                    │
└─────────────────────────────────────────────────┘
```

## Key Insight Detection Logic

```
Input Title: "Critical Bottleneck in In Sit Stage"
                        ↓
                Check for "bottleneck"
                        ↓
                 [Yes] → is_bottleneck_insight = True
                        ↓
           Extract stage using regex pattern
           r"bottleneck in (.+?) stage"
                        ↓
                  Match: "in sit"
                        ↓
              Convert to snake_case: "in_sit"
                        ↓
          Filter all stuck_items where stage == "in_sit"
                        ↓
              Include ALL matching items
                        ↓
                  EXPORT SUCCESS ✅
```

## Database Query Flow

```
┌───────────────────────────────────────┐
│  DL Webb App API                      │
│  /api/analysis/summary                │
└───────────────────────────────────────┘
              ↓
┌───────────────────────────────────────┐
│  bottleneck_analysis:                 │
│    stuck_items: [                     │
│      {                                │
│        issue_key: "UCART-1234",       │
│        stage: "in_sit",               │
│        days_in_stage: 153,            │
│        art: "UCART",                  │
│        team: "Loke",                  │
│        pi: "26Q1"                     │
│      },                               │
│      {                                │
│        issue_key: "UCART-5678",       │
│        stage: "in_sit",               │
│        days_in_stage: 87,             │
│        ...                            │
│      },                               │
│      {                                │
│        issue_key: "UCART-9999",       │
│        stage: "in_dev",  ← Different │
│        days_in_stage: 45,             │
│        ...                            │
│      }                                │
│    ]                                  │
└───────────────────────────────────────┘
              ↓
    Filter by stage == "in_sit"
              ↓
┌───────────────────────────────────────┐
│  Excel Export:                        │
│                                       │
│  Related Features Sheet:              │
│  ┌─────────────────────────────────┐ │
│  │ UCART-1234 | 153 days | in_sit │ │
│  │ UCART-5678 |  87 days | in_sit │ │
│  └─────────────────────────────────┘ │
│                                       │
│  UCART-9999 NOT included (in_dev)    │
└───────────────────────────────────────┘
```
