"""
FastAPI main application for Evaluation Coach
Provides REST API endpoints for frontend and LLM integration
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import uvicorn
from api_models import (
    AnalysisRequest,
    ARTPerformance,
    ChatRequest,
    ChatResponse,
    DashboardData,
    HealthScorecard,
    InsightFeedback,
    InsightResponse,
    JiraIssueCreate,
    JiraIssueResponse,
    MetricValue,
    ReportRequest,
    ReportResponse,
    SystemStatus,
)
from database import Base, engine, get_db, init_db
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from services.excel_import_service import excel_import_service
from services.insights_service import InsightsService
from services.llm_service import LLMService
from services.metrics_service import MetricsService
from sqlalchemy.orm import Session

# Initialize FastAPI app
app = FastAPI(
    title="Evaluation Coach API",
    description="AI-powered Agile & SAFe Analytics Platform",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8800", "http://127.0.0.1:8800"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()
metrics_service = MetricsService()
insights_service = InsightsService()

# Initialize lead-time service
leadtime_service = None
try:
    from services.leadtime_service import leadtime_service as lt_service

    leadtime_service = lt_service
    print("✅ Lead-time service initialized")
except ImportError as e:
    print(f"⚠️  Lead-time service not available: {e}")
except Exception as e:
    print(f"⚠️  Lead-time service initialization failed: {e}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("🚀 Evaluation Coach API started")


# Health check endpoint
@app.get("/api/health", response_model=SystemStatus)
async def health_check(db: Session = Depends(get_db)):
    """Check system health and connectivity"""
    try:
        # Check database
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        db_connected = True

        # Get stats
        from database import Insight, JiraIssue

        total_issues = db.query(JiraIssue).count()
        total_insights = db.query(Insight).count()

        # Check lead-time service
        leadtime_connected = False
        if leadtime_service:
            try:
                leadtime_connected = leadtime_service.is_available()
            except Exception:
                pass

        return SystemStatus(
            status="healthy",
            database_connected=db_connected,
            jira_connected=False,  # TODO: Implement Jira connection check
            llm_available=True,  # TODO: Check LLM availability
            leadtime_server_connected=leadtime_connected,
            last_sync=None,
            total_issues=total_issues,
            total_insights=total_insights,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System unhealthy: {str(e)}",
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "Evaluation Coach API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# Dashboard Endpoints
@app.get("/api/v1/dashboard", response_model=DashboardData)
async def get_dashboard(
    scope: str = "portfolio", time_range: str = "last_pi", db: Session = Depends(get_db)
):
    """Get dashboard data for specified scope"""
    try:
        # Get portfolio metrics from lead-time service
        portfolio_metrics = []

        # Initialize default values
        flow_efficiency = 67.0
        pi_predictability = 82.0
        throughput_count = 0

        if leadtime_service and leadtime_service.is_available():
            try:
                # Get planning accuracy for PI Predictability
                planning_data = leadtime_service.get_planning_accuracy()
                if planning_data and "predictability_score" in planning_data:
                    pi_predictability = round(planning_data["predictability_score"], 1)

                # Get lead-time statistics for Flow Efficiency
                stats = leadtime_service.get_leadtime_statistics()
                if stats and "stage_statistics" in stats:
                    stage_stats = stats["stage_statistics"]

                    # Calculate flow efficiency: value-add time / total time
                    # Value-add stages: in_progress, in_reviewing
                    # Non-value-add: in_backlog, in_planned, in_analysis, waiting stages
                    value_add_time = stage_stats.get("in_progress", {}).get(
                        "mean", 0
                    ) + stage_stats.get("in_reviewing", {}).get("mean", 0)

                    total_time = sum(
                        stage.get("mean", 0) for stage in stage_stats.values()
                    )

                    if total_time > 0:
                        flow_efficiency = round((value_add_time / total_time) * 100, 1)

                # Get throughput
                throughput_data = leadtime_service.get_throughput_metrics()
                if throughput_data and "items_delivered" in throughput_data:
                    throughput_count = throughput_data["items_delivered"]

            except Exception as e:
                print(f"⚠️  Could not fetch metrics from lead-time service: {e}")

        portfolio_metrics = [
            MetricValue(
                name="Flow Efficiency",
                value=flow_efficiency,
                unit="%",
                status="healthy" if flow_efficiency >= 20 else "warning",
                trend="stable",
                benchmark={"industry": 15.0, "high_performer": 40.0},
            ),
            MetricValue(
                name="PI Predictability",
                value=pi_predictability,
                unit="%",
                status="healthy" if pi_predictability >= 70 else "warning",
                trend="stable",
                benchmark={"target": 80.0},
            ),
            MetricValue(
                name="Features Delivered",
                value=throughput_count if throughput_count > 0 else 156.0,
                unit="features",
                status="healthy",
                trend="up",
                benchmark={"target": 150.0},
            ),
            MetricValue(
                name="Team Stability",
                value=89.0,
                unit="%",
                status="healthy",
                trend="stable",
                benchmark={"target": 85.0},
            ),
        ]

        # Get ART comparison from lead-time service
        art_comparison = []
        if leadtime_service and leadtime_service.is_available():
            try:
                # Get available ARTs from lead-time server
                filters = leadtime_service.get_available_filters()
                arts_list = filters.get("arts", [])[:10]  # Limit to first 10 ARTs

                for art_name in arts_list:
                    try:
                        # Get raw feature data for this ART to calculate accurate metrics
                        features = leadtime_service.client.get_flow_leadtime(
                            art=art_name, limit=10000
                        )

                        if features and len(features) > 0:
                            # Calculate flow efficiency from actual feature data
                            value_add_times = []
                            total_times = []

                            for feature in features:
                                # Value-add stages: in_progress + in_reviewing
                                value_add = feature.get("in_progress", 0) + feature.get(
                                    "in_reviewing", 0
                                )
                                # Total lead time
                                total = feature.get("total_leadtime", 0)

                                if total > 0:
                                    value_add_times.append(value_add)
                                    total_times.append(total)

                            # Calculate average flow efficiency
                            if value_add_times and total_times:
                                avg_value_add = sum(value_add_times) / len(
                                    value_add_times
                                )
                                avg_total = sum(total_times) / len(total_times)
                                flow_efficiency = (
                                    (avg_value_add / avg_total * 100)
                                    if avg_total > 0
                                    else 0
                                )
                            else:
                                flow_efficiency = 0

                            # Get planning accuracy for this ART from pip_data
                            pip_features = leadtime_service.client.get_pip_data(
                                art=art_name, limit=10000
                            )
                            if pip_features:
                                planned_committed = sum(
                                    1
                                    for f in pip_features
                                    if f.get("planned_committed", 0) > 0
                                )
                                delivered = sum(
                                    1
                                    for f in pip_features
                                    if f.get("plc_delivery", "0") == "1"
                                )
                                pi_predictability = (
                                    (delivered / planned_committed * 100)
                                    if planned_committed > 0
                                    else 0
                                )
                            else:
                                pi_predictability = 0

                            # Quality score: Estimate based on consistency (lower is better)
                            # Using coefficient of variation of total lead time
                            if total_times and len(total_times) > 1:
                                import statistics

                                mean_lt = statistics.mean(total_times)
                                stdev_lt = statistics.stdev(total_times)
                                coeff_var = (stdev_lt / mean_lt) if mean_lt > 0 else 1.0
                                # Convert to 1-5 scale (lower variability = better quality)
                                quality_score = max(
                                    1.0, min(5.0, 5.0 - (coeff_var * 2))
                                )
                            else:
                                quality_score = 3.0

                            # Status based on PI predictability
                            if pi_predictability >= 70:
                                status = "healthy"
                            elif pi_predictability >= 50:
                                status = "warning"
                            else:
                                status = "critical"

                            art_comparison.append(
                                {
                                    "art_name": art_name,
                                    "flow_efficiency": round(flow_efficiency, 1),
                                    "pi_predictability": round(pi_predictability, 1),
                                    "quality_score": round(quality_score, 1),
                                    "status": status,
                                }
                            )
                        else:
                            # No data for this ART
                            art_comparison.append(
                                {
                                    "art_name": art_name,
                                    "flow_efficiency": 0,
                                    "pi_predictability": 0,
                                    "quality_score": 0,
                                    "status": "no_data",
                                }
                            )
                    except Exception as e:
                        print(f"⚠️  Error calculating metrics for ART {art_name}: {e}")
                        continue

            except Exception as e:
                print(f"⚠️  Could not fetch ART data from lead-time service: {e}")

        # Fallback to sample data if lead-time service not available
        if not art_comparison:
            art_comparison = [
                {
                    "art_name": "Platform Engineering",
                    "flow_efficiency": 72.0,
                    "pi_predictability": 85.0,
                    "quality_score": 3.8,
                    "status": "healthy",
                },
                {
                    "art_name": "Customer Experience",
                    "flow_efficiency": 65.0,
                    "pi_predictability": 78.0,
                    "quality_score": 5.2,
                    "status": "warning",
                },
            ]

        # Get recent insights from database
        from database import Insight

        db_insights = (
            db.query(Insight)
            .filter(Insight.status == "active")
            .order_by(Insight.created_at.desc())
            .limit(5)
            .all()
        )

        recent_insights = []
        for insight in db_insights:
            recent_insights.append(
                InsightResponse(
                    id=insight.id,
                    title=insight.title,
                    severity=insight.severity,
                    confidence=insight.confidence,
                    scope=insight.scope,
                    scope_id=insight.scope_id,
                    observation=insight.observation,
                    interpretation=insight.interpretation,
                    root_causes=insight.root_causes,
                    recommended_actions=insight.recommended_actions,
                    expected_outcomes=insight.expected_outcomes,
                    metric_references=insight.metric_references,
                    evidence=insight.evidence,
                    status=insight.status,
                    created_at=insight.created_at,
                )
            )

        return DashboardData(
            portfolio_metrics=portfolio_metrics,
            art_comparison=art_comparison,
            recent_insights=recent_insights,
            trends={},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {str(e)}",
        )


# Scorecard Endpoints
@app.post("/api/v1/scorecard", response_model=HealthScorecard)
async def generate_scorecard(request: AnalysisRequest, db: Session = Depends(get_db)):
    """Generate health scorecard for specified scope"""
    try:
        scorecard_data = metrics_service.generate_scorecard(
            scope=request.scope,
            scope_id=request.scope_id,
            time_range=request.time_range,
            db=db,
        )
        return scorecard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating scorecard: {str(e)}",
        )


@app.get("/api/v1/scorecard/{scorecard_id}", response_model=HealthScorecard)
async def get_scorecard(scorecard_id: int, db: Session = Depends(get_db)):
    """Get existing scorecard by ID"""
    from database import Scorecard

    scorecard = db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()
    if not scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not found")

    return HealthScorecard(
        id=scorecard.id,
        scope=scorecard.scope,
        scope_id=scorecard.scope_id,
        overall_score=scorecard.overall_score,
        dimension_scores=scorecard.dimension_scores,
        metrics=[],  # TODO: Convert from JSON
        time_period_start=scorecard.time_period_start,
        time_period_end=scorecard.time_period_end,
        created_at=scorecard.created_at,
    )


# Insights Endpoints
@app.post("/api/v1/insights/generate", response_model=List[InsightResponse])
async def generate_insights(request: AnalysisRequest, db: Session = Depends(get_db)):
    """Generate new insights for specified scope based on real lead-time data"""
    try:
        # If lead-time service available, generate insights from real data
        if leadtime_service and leadtime_service.is_available():
            arts = (
                [request.scope_id]
                if request.scope_id and request.scope == "art"
                else None
            )

            # Get comprehensive data
            stats = leadtime_service.get_leadtime_statistics(arts=arts)
            planning = leadtime_service.get_planning_accuracy(arts=arts)
            bottlenecks = leadtime_service.identify_bottlenecks(arts=arts)
            waste = leadtime_service.analyze_waste(arts=arts)

            # Generate insights based on real data
            generated_insights = []

            # Insight 1: Planning Accuracy
            if planning and "predictability_score" in planning:
                score = planning["predictability_score"]
                if score < 70:
                    generated_insights.append(
                        InsightResponse(
                            id=len(generated_insights) + 1,
                            title=f"Low PI Predictability: {score:.1f}%",
                            severity="warning" if score < 60 else "info",
                            confidence=0.95,
                            scope=request.scope or "portfolio",
                            scope_id=request.scope_id,
                            observation=f"Planning accuracy is {score:.1f}%, below the 70% threshold.",
                            interpretation="Teams are not consistently delivering committed work.",
                            root_causes=[
                                {
                                    "description": "Overcommitment during PI Planning",
                                    "evidence": [
                                        f"Only {score:.1f}% of committed features delivered"
                                    ],
                                    "confidence": 0.9,
                                }
                            ],
                            recommended_actions=[
                                {
                                    "timeframe": "short-term",
                                    "description": "Review velocity data and adjust commitments",
                                    "owner": "RTE/Product Management",
                                    "effort": "medium",
                                    "dependencies": [],
                                    "success_signal": "Predictability improves to >70%",
                                }
                            ],
                            expected_outcomes={
                                "metrics_to_watch": ["PI Predictability"],
                                "leading_indicators": ["Commitment vs Actual"],
                                "lagging_indicators": ["Planning Accuracy"],
                                "timeline": "1-2 PIs",
                                "risks": ["Resistance to reduced commitments"],
                            },
                            metric_references=["pi_predictability"],
                            evidence=[f"Current: {score:.1f}%, Target: 80%"],
                            status="active",
                            created_at=datetime.now(),
                        )
                    )

            # Insight 2: Bottlenecks
            if bottlenecks and bottlenecks.get("bottlenecks"):
                for bottleneck in bottlenecks["bottlenecks"][:2]:  # Top 2
                    generated_insights.append(
                        InsightResponse(
                            id=len(generated_insights) + 1,
                            title=f"Bottleneck Detected: {bottleneck.get('stage', 'Unknown')}",
                            severity="warning",
                            confidence=0.85,
                            scope=request.scope or "portfolio",
                            scope_id=request.scope_id,
                            observation=f"High delay in {bottleneck.get('stage', 'stage')}",
                            interpretation="This stage is causing significant delays in flow",
                            root_causes=[
                                {
                                    "description": f"Excessive time in {bottleneck.get('stage')}",
                                    "evidence": [
                                        f"Mean: {bottleneck.get('mean', 0):.1f} days"
                                    ],
                                    "confidence": 0.8,
                                }
                            ],
                            recommended_actions=[
                                {
                                    "timeframe": "medium-term",
                                    "description": f"Investigate and reduce time in {bottleneck.get('stage')}",
                                    "owner": "Team Leads",
                                    "effort": "high",
                                    "dependencies": [],
                                    "success_signal": "Stage time reduced by 30%",
                                }
                            ],
                            expected_outcomes={
                                "metrics_to_watch": ["Lead Time", "Flow Efficiency"],
                                "leading_indicators": ["Stage Duration"],
                                "lagging_indicators": ["Total Lead Time"],
                                "timeline": "2-3 months",
                                "risks": [],
                            },
                            metric_references=["leadtime"],
                            evidence=[f"Bottleneck: {bottleneck.get('stage')}"],
                            status="active",
                            created_at=datetime.now(),
                        )
                    )

            if generated_insights:
                return generated_insights

        # Fallback to service-generated insights
        insights = await insights_service.generate_insights(
            scope=request.scope,
            scope_id=request.scope_id,
            time_range=request.time_range,
            db=db,
        )
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating insights: {str(e)}",
        )


@app.get("/api/v1/insights", response_model=List[InsightResponse])
async def get_insights(
    scope: Optional[str] = None,
    severity: Optional[str] = None,
    status: str = "active",
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get existing insights with optional filters"""
    from database import Insight

    query = db.query(Insight).filter(Insight.status == status)

    if scope:
        query = query.filter(Insight.scope == scope)
    if severity:
        query = query.filter(Insight.severity == severity)

    insights = query.order_by(Insight.created_at.desc()).limit(limit).all()

    return [
        InsightResponse(
            id=insight.id,
            title=insight.title,
            severity=insight.severity,
            confidence=insight.confidence,
            scope=insight.scope,
            scope_id=insight.scope_id,
            observation=insight.observation,
            interpretation=insight.interpretation,
            root_causes=insight.root_causes,
            recommended_actions=insight.recommended_actions,
            expected_outcomes=insight.expected_outcomes,
            metric_references=insight.metric_references,
            evidence=insight.evidence,
            status=insight.status,
            created_at=insight.created_at,
        )
        for insight in insights
    ]


@app.post("/api/v1/insights/{insight_id}/feedback")
async def submit_insight_feedback(
    insight_id: int, feedback: InsightFeedback, db: Session = Depends(get_db)
):
    """Submit feedback for an insight (accept/dismiss)"""
    from database import Insight

    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")

    insight.status = feedback.action
    if feedback.feedback:
        insight.user_feedback = feedback.feedback

    db.commit()

    return {"message": f"Insight {insight_id} {feedback.action}ed successfully"}


# Chat/AI Coach Endpoints
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Process chat message with AI coach"""
    try:
        # Store user message
        from database import ChatMessage

        user_msg = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.message,
            context=request.context,
        )
        db.add(user_msg)
        db.commit()

        # Generate AI response
        response = await llm_service.generate_response(
            message=request.message, context=request.context, db=db
        )

        # Store assistant message
        assistant_msg = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=response,
            context=request.context,
        )
        db.add(assistant_msg)
        db.commit()

        return ChatResponse(
            message=response, context=request.context or {}, timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat: {str(e)}",
        )


@app.get("/api/v1/chat/history/{session_id}")
async def get_chat_history(
    session_id: str, limit: int = 50, db: Session = Depends(get_db)
):
    """Get chat history for a session"""
    from database import ChatMessage

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {"role": msg.role, "content": msg.content, "timestamp": msg.created_at}
        for msg in reversed(messages)
    ]


# Metrics Endpoints
@app.get("/api/v1/metrics")
async def get_metrics(
    scope: str = "portfolio",
    scope_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    time_range: str = "last_pi",
    db: Session = Depends(get_db),
):
    """Get calculated metrics for specified scope with real data from lead-time service"""

    # If lead-time service is available, return real-time metrics
    if leadtime_service and leadtime_service.is_available():
        try:
            # Parse scope_id for filtering
            arts = [scope_id] if scope_id and scope == "art" else None

            # Get comprehensive metrics
            stats = leadtime_service.get_leadtime_statistics(arts=arts)
            planning = leadtime_service.get_planning_accuracy(arts=arts)
            throughput = leadtime_service.get_throughput_metrics(arts=arts)
            bottlenecks = leadtime_service.identify_bottlenecks(arts=arts)

            metrics = []

            # Lead-time metrics
            if stats and "stage_statistics" in stats:
                for stage, data in stats["stage_statistics"].items():
                    metrics.append(
                        {
                            "name": f"leadtime_{stage}",
                            "value": data.get("mean", 0),
                            "data": {
                                "median": data.get("median", 0),
                                "p85": data.get("p85", 0),
                                "p95": data.get("p95", 0),
                                "count": data.get("count", 0),
                                "unit": "days",
                            },
                            "calculated_at": datetime.now(),
                        }
                    )

            # Planning accuracy
            if planning and "predictability_score" in planning:
                metrics.append(
                    {
                        "name": "pi_predictability",
                        "value": planning["predictability_score"],
                        "data": planning.get("planning_metrics", {}),
                        "calculated_at": datetime.now(),
                    }
                )

            # Throughput
            if throughput:
                metrics.append(
                    {
                        "name": "throughput",
                        "value": throughput.get("items_delivered", 0),
                        "data": throughput,
                        "calculated_at": datetime.now(),
                    }
                )

            # Bottlenecks
            if bottlenecks:
                metrics.append(
                    {
                        "name": "bottlenecks",
                        "value": len(bottlenecks.get("bottlenecks", [])),
                        "data": bottlenecks,
                        "calculated_at": datetime.now(),
                    }
                )

            return metrics

        except Exception as e:
            print(f"⚠️  Error fetching real-time metrics: {e}")

    # Fallback to database metrics
    from database import MetricCalculation

    query = db.query(MetricCalculation).filter(MetricCalculation.scope == scope)

    if scope_id:
        query = query.filter(MetricCalculation.scope_id == scope_id)
    if metric_name:
        query = query.filter(MetricCalculation.metric_name == metric_name)

    metrics = query.order_by(MetricCalculation.calculated_at.desc()).limit(100).all()

    return [
        {
            "name": m.metric_name,
            "value": m.metric_value,
            "data": m.metric_data,
            "calculated_at": m.calculated_at,
        }
        for m in metrics
    ]


# Jira Integration Endpoints (OPTIONAL - Not currently required)
# All data comes from DL Webb App. These endpoints are for future Jira MCP integration.
@app.post("/api/v1/jira/sync")
async def sync_jira_data(db: Session = Depends(get_db)):
    """
    Trigger Jira data synchronization (OPTIONAL - not currently used)

    Note: Currently all data comes from DL Webb App (localhost:8000).
    This endpoint is reserved for future Jira MCP integration if needed.
    """
    # TODO: Implement Jira sync when/if needed
    return {
        "message": "Jira sync not configured - using DL Webb App data",
        "status": "not_required",
        "data_source": "DL Webb App (localhost:8000)",
    }


@app.post("/api/v1/jira/issues", response_model=JiraIssueResponse)
async def create_jira_issue(issue: JiraIssueCreate, db: Session = Depends(get_db)):
    """
    Create or update Jira issue in database (OPTIONAL)

    Note: Currently all issue data comes from DL Webb App.
    This endpoint can be used for future direct Jira integration via MCP.
    """
    from database import JiraIssue

    # Check if issue exists
    existing = (
        db.query(JiraIssue).filter(JiraIssue.issue_key == issue.issue_key).first()
    )

    if existing:
        # Update existing
        for key, value in issue.dict().items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        db_issue = JiraIssue(**issue.dict())
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        return db_issue


# Report/Export Endpoints
@app.post("/api/v1/reports/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest, db: Session = Depends(get_db)):
    """Generate downloadable report"""
    # TODO: Implement report generation
    import uuid

    report_id = str(uuid.uuid4())

    return ReportResponse(
        report_id=report_id,
        download_url=f"/api/v1/reports/download/{report_id}",
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )


# Excel Import/Admin Endpoints
@app.post("/api/v1/admin/import/upload")
async def upload_excel_file(file: UploadFile = File(...)):
    """Upload Excel file for import"""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed"
        )

    # Save uploaded file temporarily
    upload_dir = "backend/data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(
        upload_dir, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    )

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Import to staging
        result = excel_import_service.import_excel_to_staging(file_path)
        result["file_path"] = file_path
        result["filename"] = file.filename

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/import/staged")
async def get_staged_data(skip: int = 0, limit: int = 100):
    """Get staged import data for review"""
    staged_issues = excel_import_service.get_staged_data(skip, limit)
    total = len(excel_import_service.staged_data)

    return {"total": total, "skip": skip, "limit": limit, "issues": staged_issues}


@app.put("/api/v1/admin/import/staged/{row_number}")
async def update_staged_issue(row_number: int, updates: dict):
    """Update a staged issue before committing"""
    result = excel_import_service.update_staged_issue(row_number, updates)
    if not result["success"]:
        raise HTTPException(
            status_code=404, detail=result.get("error", "Issue not found")
        )
    return result


@app.delete("/api/v1/admin/import/staged/{row_number}")
async def delete_staged_issue(row_number: int):
    """Delete a staged issue"""
    return excel_import_service.delete_staged_issue(row_number)


@app.post("/api/v1/admin/import/commit")
async def commit_import(
    selected_rows: Optional[List[int]] = None, db: Session = Depends(get_db)
):
    """Commit staged data to database"""
    result = excel_import_service.commit_to_database(db, selected_rows)
    if not result["success"]:
        raise HTTPException(
            status_code=500, detail=result.get("error", "Commit failed")
        )
    return result


@app.get("/api/v1/admin/import/template")
async def download_template():
    """Generate and download Excel template"""
    template_df = excel_import_service.export_template()

    # Save template
    template_dir = "backend/data/templates"
    os.makedirs(template_dir, exist_ok=True)
    template_path = os.path.join(template_dir, "import_template.xlsx")
    template_df.to_excel(template_path, index=False)

    return {
        "message": "Template generated",
        "download_url": f"/api/v1/admin/import/template/download",
        "template_path": template_path,
    }


# ============================================================================
# ART/Team Endpoints
# ============================================================================


@app.get("/api/arts")
async def get_arts():
    """Get list of all ARTs from lead-time server"""
    if not leadtime_service:
        return {"arts": [], "message": "Lead-time service not available"}

    try:
        filters = leadtime_service.get_available_filters()
        return {
            "arts": filters.get("arts", []),
            "count": len(filters.get("arts", [])),
            "source": "DL Webb App",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not fetch ARTs: {str(e)}")


@app.get("/api/teams")
async def get_teams():
    """Get list of all teams from lead-time server"""
    if not leadtime_service:
        return {"teams": [], "message": "Lead-time service not available"}

    try:
        filters = leadtime_service.get_available_filters()
        return {
            "teams": filters.get("teams", []),
            "count": len(filters.get("teams", [])),
            "source": "DL Webb App",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not fetch teams: {str(e)}")


@app.get("/api/pis")
async def get_pis():
    """Get list of all Program Increments from lead-time server"""
    if not leadtime_service:
        return {"pis": [], "message": "Lead-time service not available"}

    try:
        filters = leadtime_service.get_available_filters()
        return {
            "pis": filters.get("pis", []),
            "count": len(filters.get("pis", [])),
            "source": "DL Webb App",
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not fetch PIs: {str(e)}")


# ============================================================================
# Lead-Time Data Endpoints (from external DL Webb App server)
# ============================================================================


@app.get("/api/leadtime/status")
async def get_leadtime_server_status():
    """Check if lead-time server is available"""
    if not leadtime_service:
        return {
            "available": False,
            "message": "Lead-time service not configured",
        }

    is_available = leadtime_service.is_available()
    return {
        "available": is_available,
        "server_url": leadtime_service.client.base_url if is_available else None,
        "message": "Connected" if is_available else "Server not responding",
    }


@app.get("/api/leadtime/filters")
async def get_leadtime_filters():
    """Get available filter options from lead-time server"""
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    filters = leadtime_service.get_available_filters()
    if not filters:
        raise HTTPException(
            status_code=503, detail="Could not fetch filters from lead-time server"
        )

    return filters


@app.get("/api/leadtime/features")
async def get_leadtime_features(
    art: Optional[str] = None,
    pi: Optional[str] = None,
    team: Optional[str] = None,
):
    """
    Get feature lead-time data with stage-by-stage breakdown.

    Query parameters:
    - art: Filter by Agile Release Train
    - pi: Filter by Program Increment
    - team: Filter by development team
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    data = leadtime_service.get_feature_leadtime_data(art=art, pi=pi, team=team)
    return {
        "count": len(data),
        "features": data,
        "filters_applied": {
            "art": art,
            "pi": pi,
            "team": team,
        },
    }


@app.get("/api/leadtime/statistics")
async def get_leadtime_statistics(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
    teams: Optional[str] = None,
):
    """
    Get statistical analysis of lead-time across workflow stages.

    Query parameters:
    - arts: Comma-separated list of ARTs (e.g., "ACEART,OTHERART")
    - pis: Comma-separated list of PIs (e.g., "21Q4,22Q1")
    - teams: Comma-separated list of teams
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    # Parse comma-separated values
    arts_list = arts.split(",") if arts else None
    pis_list = pis.split(",") if pis else None
    teams_list = teams.split(",") if teams else None

    stats = leadtime_service.get_leadtime_statistics(
        arts=arts_list, pis=pis_list, teams=teams_list
    )

    if not stats:
        raise HTTPException(
            status_code=503, detail="Could not fetch statistics from lead-time server"
        )

    return stats


@app.get("/api/leadtime/bottlenecks")
async def get_bottleneck_analysis(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
):
    """
    Identify workflow bottlenecks.

    Query parameters:
    - arts: Comma-separated list of ARTs
    - pis: Comma-separated list of PIs
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    arts_list = arts.split(",") if arts else None
    pis_list = pis.split(",") if pis else None

    bottlenecks = leadtime_service.identify_bottlenecks(arts=arts_list, pis=pis_list)
    return bottlenecks


@app.get("/api/leadtime/planning-accuracy")
async def get_planning_accuracy(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
):
    """
    Get planning accuracy metrics showing commitment vs delivery.

    Returns:
    - Overall planning accuracy (committed items delivered)
    - Revised planning accuracy (including scope changes)
    - PI-by-PI breakdown
    - Predictability score

    Query parameters:
    - arts: Comma-separated list of ARTs
    - pis: Comma-separated list of PIs
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    arts_list = arts.split(",") if arts else None
    pis_list = pis.split(",") if pis else None

    planning = leadtime_service.get_planning_accuracy(arts=arts_list, pis=pis_list)
    return planning


@app.get("/api/leadtime/waste")
async def get_waste_analysis(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
):
    """
    Analyze waste in the development process.

    Query parameters:
    - arts: Comma-separated list of ARTs
    - pis: Comma-separated list of PIs
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    arts_list = arts.split(",") if arts else None
    pis_list = pis.split(",") if pis else None

    waste = leadtime_service.analyze_waste(arts=arts_list, pis=pis_list)
    return waste


@app.get("/api/leadtime/throughput")
async def get_throughput_metrics(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
):
    """
    Get throughput metrics showing delivery rate.

    Query parameters:
    - arts: Comma-separated list of ARTs
    - pis: Comma-separated list of PIs
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    arts_list = arts.split(",") if arts else None
    pis_list = pis.split(",") if pis else None

    throughput = leadtime_service.get_throughput_metrics(arts=arts_list, pis=pis_list)
    return throughput


@app.get("/api/leadtime/trends")
async def get_trend_analysis(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
):
    """
    Get trend analysis over time.

    Query parameters:
    - arts: Comma-separated list of ARTs
    - pis: Comma-separated list of PIs
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    arts_list = arts.split(",") if arts else None
    pis_list = pis.split(",") if pis else None

    trends = leadtime_service.get_trend_analysis(arts=arts_list, pis=pis_list)
    return trends


@app.get("/api/leadtime/summary")
async def get_leadtime_coaching_summary(
    art: Optional[str] = None,
    pi: Optional[str] = None,
):
    """
    Get a comprehensive coaching summary combining multiple analyses.

    Query parameters:
    - art: Focus on specific ART
    - pi: Focus on specific PI
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    summary = leadtime_service.get_summary_for_coaching(art=art, pi=pi)
    return summary


@app.post("/api/leadtime/enrich-issues")
async def enrich_issues_with_leadtime(issues: List[Dict[str, Any]]):
    """
    Enrich a list of Jira issues with lead-time data.

    Matches issues by key and adds lead-time metrics from external server.
    """
    if not leadtime_service:
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    enriched = leadtime_service.enrich_jira_issues_with_leadtime(issues)
    return {
        "count": len(enriched),
        "enriched_count": len([i for i in enriched if "leadtime" in i]),
        "issues": enriched,
    }


# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
