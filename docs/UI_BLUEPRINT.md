# Dashboard & UI Blueprint

**Purpose**: Provide intuitive, drill-down visualization of metrics, insights, and coaching recommendations.

**Philosophy**: Read-only analysis dashboards focused on **understanding** and **learning**, not operational work tracking.

---

## 1. Navigation Structure

```
┌─────────────────────────────────────────────┐
│  Evaluation Coach                      🔍 ⚙️│
├─────────────────────────────────────────────┤
│                                             │
│  📊 Portfolio View                          │
│  🎯 ART View                                │
│  👥 Team View                               │
│  📚 Knowledge Base                          │
│  📈 Historical Trends                       │
│                                             │
└─────────────────────────────────────────────┘
```

### 1.1 Portfolio View

**Purpose**: Executive-level health across all ARTs

```
Portfolio Overview
 ├── Flow & Predictability Dashboard
 │    ├── Epic lead times
 │    ├── Portfolio WIP
 │    └── Strategic predictability
 │
 ├── ART Comparison Heatmap
 │    ├── ART health scores
 │    ├── Predictability comparison
 │    └── Dependency health
 │
 └── Systemic Bottlenecks
      ├── Cross-ART patterns
      ├── Shared constraints
      └── Investment distribution
```

### 1.2 ART View

**Purpose**: Program execution health and team dynamics

```
ART: Platform Engineering
 ├── PI Health
 │    ├── Current PI objectives progress
 │    ├── Historical PI predictability
 │    └── Feature throughput trends
 │
 ├── Dependencies
 │    ├── Cross-team dependency map
 │    ├── Blocked work visualization
 │    └── External dependency tracking
 │
 └── Team Load Balance
      ├── Team throughput comparison
      ├── WIP distribution
      └── Quality metrics by team
```

### 1.3 Team View

**Purpose**: Sprint-level execution and improvement actions

```
Team: Platform Team Alpha
 ├── Sprint Flow
 │    ├── Current sprint burndown
 │    ├── Cumulative flow diagram
 │    └── Cycle time distribution
 │
 ├── Quality & Rework
 │    ├── Defect trends
 │    ├── Rework ratio
 │    └── Flow efficiency
 │
 └── Improvement Actions
      ├── Active coaching insights
      ├── Action tracker
      └── Success metrics dashboard
```

---

## 2. Core UI Components

### 2.1 Metric Card

**Purpose**: Display current state of a single metric

```html
<div class="metric-card" data-status="warning">
  <div class="metric-header">
    <h3>WIP per Person</h3>
    <span class="trend-indicator">📈</span>
  </div>
  
  <div class="metric-value">
    <span class="current-value">3.2</span>
    <span class="unit">items/person</span>
  </div>
  
  <div class="metric-comparison">
    <span class="target">Target: ≤1.5</span>
    <span class="change">+0.6 from last sprint</span>
  </div>
  
  <div class="metric-sparkline">
    <!-- Inline trend chart -->
    <svg>...</svg>
  </div>
  
  <button class="drill-down-btn">View Details →</button>
</div>
```

**Styling**:
- **Healthy**: Green border, light green background
- **Warning**: Yellow border, light yellow background
- **Critical**: Red border, light red background

### 2.2 Trend Chart

**Purpose**: Show metric evolution over time

```html
<div class="trend-chart-container">
  <h3>Lead Time Trend (Last 6 Sprints)</h3>
  
  <div class="chart-filters">
    <button class="filter-btn active">Sprint</button>
    <button class="filter-btn">PI</button>
    <button class="filter-btn">Month</button>
  </div>
  
  <canvas id="leadTimeTrendChart"></canvas>
  
  <div class="chart-legend">
    <span class="legend-item">
      <span class="color-box" style="background: #4CAF50"></span>
      P50 (Median)
    </span>
    <span class="legend-item">
      <span class="color-box" style="background: #FFC107"></span>
      P85
    </span>
    <span class="legend-item">
      <span class="color-box" style="background: #F44336"></span>
      P95
    </span>
  </div>
</div>
```

**Chart Library**: Chart.js or Recharts (if React)

### 2.3 Heatmap

**Purpose**: Compare multiple teams/ARTs on multiple dimensions

```html
<div class="heatmap-container">
  <h3>ART Health Comparison</h3>
  
  <table class="heatmap-table">
    <thead>
      <tr>
        <th>ART</th>
        <th>PI Predictability</th>
        <th>Flow Efficiency</th>
        <th>Quality</th>
        <th>Dependency Health</th>
        <th>Overall</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Platform</td>
        <td class="cell-warning" data-value="72">72</td>
        <td class="cell-healthy" data-value="85">85</td>
        <td class="cell-warning" data-value="68">68</td>
        <td class="cell-critical" data-value="58">58</td>
        <td class="cell-warning" data-value="71">71</td>
      </tr>
      <tr>
        <td>Mobile</td>
        <td class="cell-healthy" data-value="88">88</td>
        <td class="cell-healthy" data-value="82">82</td>
        <td class="cell-healthy" data-value="90">90</td>
        <td class="cell-healthy" data-value="85">85</td>
        <td class="cell-healthy" data-value="86">86</td>
      </tr>
      <!-- More ARTs -->
    </tbody>
  </table>
</div>
```

**Color Coding**:
- **90-100**: Dark green
- **75-89**: Light green
- **60-74**: Yellow
- **40-59**: Orange
- **0-39**: Red

### 2.4 Insight Panel

**Purpose**: Display AI-generated coaching insights

```html
<div class="insight-panel" data-severity="high">
  <div class="insight-header">
    <span class="insight-icon">⚠️</span>
    <h4>Excessive Work-in-Progress Reducing Throughput</h4>
    <span class="insight-confidence">High Confidence</span>
  </div>
  
  <div class="insight-summary">
    <p>WIP per person is 3.2 (target: ≤1.5), causing context switching and longer cycle times.</p>
  </div>
  
  <div class="insight-metrics">
    <span class="metric-badge">WIP: 3.2</span>
    <span class="metric-badge">Cycle Time: +50%</span>
    <span class="metric-badge">Throughput: -22%</span>
  </div>
  
  <div class="insight-actions">
    <button class="btn-primary" onclick="showFullInsight('insight-123')">
      View Full Analysis
    </button>
    <button class="btn-secondary" onclick="viewActionPlan('insight-123')">
      See Action Plan
    </button>
  </div>
  
  <div class="insight-metadata">
    <span>Based on last 3 sprints</span>
    <span>Generated: 2026-01-02</span>
  </div>
</div>
```

### 2.5 Action Tracker

**Purpose**: Track improvement actions from coaching insights

```html
<div class="action-tracker">
  <h3>Active Improvement Actions</h3>
  
  <div class="action-filters">
    <button class="filter-tag active">All (12)</button>
    <button class="filter-tag">Short-Term (5)</button>
    <button class="filter-tag">Medium-Term (4)</button>
    <button class="filter-tag">Long-Term (3)</button>
  </div>
  
  <div class="action-list">
    <div class="action-item" data-status="in-progress">
      <div class="action-header">
        <input type="checkbox" class="action-checkbox" />
        <h5>Implement Soft WIP Limit of 2 per Person</h5>
        <span class="action-priority">Priority: High</span>
      </div>
      
      <div class="action-details">
        <p><strong>Owner:</strong> Scrum Master + Team</p>
        <p><strong>Effort:</strong> 1 sprint</p>
        <p><strong>Success Signal:</strong> WIP drops below 2.5 by end of sprint</p>
      </div>
      
      <div class="action-progress">
        <div class="progress-bar">
          <div class="progress-fill" style="width: 60%"></div>
        </div>
        <span class="progress-label">60% Complete</span>
      </div>
      
      <div class="action-footer">
        <span class="action-date">Started: 2025-12-15</span>
        <button class="btn-small" onclick="updateAction('action-456')">Update</button>
      </div>
    </div>
    
    <!-- More actions -->
  </div>
</div>
```

### 2.6 Cumulative Flow Diagram (CFD)

**Purpose**: Visualize work flow and identify bottlenecks

```html
<div class="cfd-container">
  <h3>Cumulative Flow Diagram - Last 30 Days</h3>
  
  <canvas id="cumulativeFlowChart"></canvas>
  
  <div class="cfd-insights">
    <div class="insight-box">
      <h5>🔍 Pattern Detected</h5>
      <p>"In Review" queue is widening, indicating code review bottleneck.</p>
    </div>
  </div>
</div>
```

**Chart Configuration** (Chart.js):
```javascript
{
  type: 'line',
  data: {
    labels: dates,  // Last 30 days
    datasets: [
      {
        label: 'Done',
        data: doneData,
        fill: true,
        backgroundColor: '#4CAF50'
      },
      {
        label: 'In Review',
        data: reviewData,
        fill: true,
        backgroundColor: '#2196F3'
      },
      {
        label: 'In Progress',
        data: progressData,
        fill: true,
        backgroundColor: '#FFC107'
      },
      {
        label: 'To Do',
        data: todoData,
        fill: true,
        backgroundColor: '#9E9E9E'
      }
    ]
  },
  options: {
    scales: {
      y: { stacked: true }
    }
  }
}
```

---

## 3. Page Layouts

### 3.1 Portfolio View Layout

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Portfolio View - Evaluation Coach</title>
  <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
  <div class="app-container">
    <!-- Navigation Sidebar -->
    <aside class="sidebar">
      <div class="logo">
        <h2>📊 Evaluation Coach</h2>
      </div>
      <nav class="nav-menu">
        <a href="/portfolio" class="nav-item active">📊 Portfolio</a>
        <a href="/art" class="nav-item">🎯 ARTs</a>
        <a href="/team" class="nav-item">👥 Teams</a>
        <a href="/knowledge" class="nav-item">📚 Knowledge</a>
        <a href="/trends" class="nav-item">📈 Trends</a>
      </nav>
    </aside>
    
    <!-- Main Content -->
    <main class="main-content">
      <header class="page-header">
        <h1>Enterprise Portfolio</h1>
        <div class="header-actions">
          <button class="btn-secondary">📅 Last PI</button>
          <button class="btn-secondary">⚙️ Settings</button>
        </div>
      </header>
      
      <!-- Overall Health Score -->
      <section class="health-score-banner">
        <div class="score-circle" data-score="68">
          <span class="score-value">68</span>
          <span class="score-label">Overall Health</span>
        </div>
        <div class="score-breakdown">
          <div class="score-item">
            <span class="score-name">Strategic Predictability</span>
            <span class="score-value">65</span>
          </div>
          <div class="score-item">
            <span class="score-name">Flow Efficiency</span>
            <span class="score-value">58</span>
          </div>
          <div class="score-item">
            <span class="score-name">Value Realization</span>
            <span class="score-value">75</span>
          </div>
        </div>
      </section>
      
      <!-- Key Metrics Grid -->
      <section class="metrics-grid">
        <div class="metric-card" data-status="warning">
          <!-- WIP Metric Card -->
        </div>
        <div class="metric-card" data-status="critical">
          <!-- Lead Time Card -->
        </div>
        <div class="metric-card" data-status="healthy">
          <!-- Predictability Card -->
        </div>
        <!-- More cards -->
      </section>
      
      <!-- ART Comparison Heatmap -->
      <section class="heatmap-section">
        <div class="heatmap-container">
          <!-- Heatmap component -->
        </div>
      </section>
      
      <!-- Top Insights -->
      <section class="insights-section">
        <h2>🎯 Top Priority Insights</h2>
        <div class="insights-grid">
          <div class="insight-panel" data-severity="high">
            <!-- Insight component -->
          </div>
          <!-- More insights -->
        </div>
      </section>
    </main>
  </div>
  
  <script src="/static/js/main.js"></script>
</body>
</html>
```

### 3.2 Team View Layout

```html
<main class="main-content">
  <header class="page-header">
    <div class="breadcrumb">
      <a href="/portfolio">Portfolio</a> &gt;
      <a href="/art/platform">Platform ART</a> &gt;
      <span>Team Alpha</span>
    </div>
    <h1>Platform Team Alpha</h1>
    <div class="header-meta">
      <span>Sprint 26 (2 days remaining)</span>
      <span>8 team members</span>
    </div>
  </header>
  
  <!-- Current Sprint Overview -->
  <section class="sprint-overview">
    <div class="sprint-summary">
      <h3>Current Sprint Health</h3>
      <div class="summary-stats">
        <div class="stat">
          <span class="stat-value">12</span>
          <span class="stat-label">Committed</span>
        </div>
        <div class="stat">
          <span class="stat-value">7</span>
          <span class="stat-label">Done</span>
        </div>
        <div class="stat">
          <span class="stat-value">58%</span>
          <span class="stat-label">Complete</span>
        </div>
      </div>
    </div>
    
    <div class="sprint-burndown">
      <canvas id="sprintBurndown"></canvas>
    </div>
  </section>
  
  <!-- Key Metrics Row -->
  <section class="metrics-row">
    <div class="metric-card compact">
      <h4>WIP</h4>
      <span class="value">3.2</span>
      <span class="target">Target: 1.5</span>
    </div>
    <div class="metric-card compact">
      <h4>Cycle Time</h4>
      <span class="value">9d</span>
      <span class="target">Target: 5d</span>
    </div>
    <div class="metric-card compact">
      <h4>Throughput</h4>
      <span class="value">14</span>
      <span class="target">Target: 18</span>
    </div>
  </section>
  
  <!-- Coaching Insights -->
  <section class="coaching-section">
    <h2>🤖 Coaching Insights</h2>
    <div class="insight-panel" data-severity="high">
      <!-- Full insight component -->
    </div>
  </section>
  
  <!-- Action Tracker -->
  <section class="actions-section">
    <div class="action-tracker">
      <!-- Action tracker component -->
    </div>
  </section>
  
  <!-- Flow Visualization -->
  <section class="flow-section">
    <div class="cfd-container">
      <!-- Cumulative Flow Diagram -->
    </div>
  </section>
</main>
```

---

## 4. RESTful API Endpoints

### 4.1 API Structure

```
/api/v1/
├── /portfolio
│   ├── GET /health                    # Portfolio health score
│   ├── GET /metrics                   # All portfolio metrics
│   └── GET /arts                      # List of ARTs
│
├── /art/{art_id}
│   ├── GET /health                    # ART health score
│   ├── GET /metrics                   # ART metrics
│   ├── GET /teams                     # Teams in ART
│   ├── GET /dependencies              # Cross-team dependencies
│   └── GET /insights                  # Coaching insights
│
├── /team/{team_id}
│   ├── GET /health                    # Team health score
│   ├── GET /metrics                   # Team metrics
│   ├── GET /sprint/current            # Current sprint data
│   ├── GET /insights                  # Coaching insights
│   └── GET /actions                   # Improvement actions
│
├── /insights
│   ├── GET /{insight_id}              # Single insight details
│   ├── POST /{insight_id}/feedback    # Feedback on insight
│   └── GET /                          # All insights (filterable)
│
├── /actions
│   ├── GET /{action_id}               # Action details
│   ├── PUT /{action_id}               # Update action status
│   └── POST /                         # Create custom action
│
└── /analysis
    ├── POST /run                      # Trigger new analysis
    ├── GET /status/{run_id}           # Check analysis status
    └── GET /results/{run_id}          # Get analysis results
```

### 4.2 Example API Response

**GET /api/v1/team/alpha/health**

```json
{
  "team_id": "alpha",
  "team_name": "Platform Team Alpha",
  "scope": "Team",
  "overall_score": 68,
  "dimensions": {
    "sprint_reliability": {
      "score": 65,
      "status": "warning",
      "signals": {
        "commitment_reliability": 0.65,
        "scope_change_rate": 0.30,
        "spillover_rate": 0.12
      }
    },
    "flow_efficiency": {
      "score": 58,
      "status": "critical",
      "signals": {
        "flow_efficiency": 0.22,
        "cycle_time_days": 9,
        "avg_wait_time_days": 7
      }
    },
    "wip_discipline": {
      "score": 55,
      "status": "critical",
      "signals": {
        "wip_per_person": 3.2,
        "max_wip_per_person": 5,
        "wip_limit_adherence": 0.45
      }
    },
    "quality": {
      "score": 72,
      "status": "warning",
      "signals": {
        "defect_injection_rate": 0.12,
        "bug_fix_time_days": 3,
        "rework_ratio": 0.15
      }
    },
    "team_stability": {
      "score": 90,
      "status": "healthy",
      "signals": {
        "team_churn": 0.05,
        "avg_tenure_months": 18
      }
    }
  },
  "top_priority": "Reduce WIP to improve flow efficiency",
  "confidence": "high",
  "generated_at": "2026-01-02T10:30:00Z"
}
```

---

## 5. Frontend Technology Stack

### 5.1 Recommended Stack

**Option 1: Vanilla JS + HTML/CSS** (Simplest)
- **Framework**: None (plain JavaScript)
- **Charts**: Chart.js
- **Styling**: Custom CSS with CSS Grid/Flexbox
- **Build**: No build step needed

**Option 2: React + TypeScript** (Modern)
- **Framework**: React 18+
- **Language**: TypeScript
- **Charts**: Recharts
- **Styling**: Tailwind CSS or CSS Modules
- **Build**: Vite
- **State Management**: React Query for API data

**Option 3: Next.js** (Full-stack)
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Charts**: Recharts or Chart.js
- **Styling**: Tailwind CSS
- **API**: Next.js API routes
- **Deployment**: Vercel or self-hosted

### 5.2 Recommended: React + Vite

```bash
# Create frontend project
cd /Users/mats/Egna-Dokument/Utveckling/Jobb/Evaluation_coach/frontend
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install
npm install recharts react-query axios tailwindcss
npm install -D @types/node
```

**Project Structure**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── MetricCard.tsx
│   │   ├── TrendChart.tsx
│   │   ├── Heatmap.tsx
│   │   ├── InsightPanel.tsx
│   │   └── ActionTracker.tsx
│   │
│   ├── pages/
│   │   ├── PortfolioView.tsx
│   │   ├── ARTView.tsx
│   │   ├── TeamView.tsx
│   │   └── KnowledgeBase.tsx
│   │
│   ├── services/
│   │   └── api.ts              # API client
│   │
│   ├── types/
│   │   └── index.ts            # TypeScript types
│   │
│   └── App.tsx
│
├── public/
├── package.json
└── vite.config.ts
```

---

## 6. Styling Guidelines

### 6.1 Color Palette

```css
:root {
  /* Status Colors */
  --color-healthy: #4CAF50;
  --color-healthy-light: #E8F5E9;
  --color-warning: #FFC107;
  --color-warning-light: #FFF8E1;
  --color-critical: #F44336;
  --color-critical-light: #FFEBEE;
  
  /* UI Colors */
  --color-primary: #2196F3;
  --color-secondary: #757575;
  --color-background: #FAFAFA;
  --color-surface: #FFFFFF;
  --color-border: #E0E0E0;
  --color-text: #212121;
  --color-text-secondary: #757575;
  
  /* Chart Colors */
  --chart-color-1: #2196F3;
  --chart-color-2: #4CAF50;
  --chart-color-3: #FFC107;
  --chart-color-4: #F44336;
  --chart-color-5: #9C27B0;
}
```

### 6.2 Typography

```css
:root {
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 2rem;
}
```

---

## 7. Accessibility

All UI components must meet WCAG 2.1 Level AA:

- [ ] Color contrast ratio ≥ 4.5:1 for normal text
- [ ] Color contrast ratio ≥ 3:1 for large text
- [ ] Keyboard navigation support
- [ ] Screen reader friendly (ARIA labels)
- [ ] Focus indicators visible
- [ ] Responsive design (mobile-friendly)

---

## References

- Material Design 3
- Tailwind CSS Documentation
- Chart.js Documentation
- Recharts Documentation
- WCAG 2.1 Guidelines
