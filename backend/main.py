"""
FastAPI main application for Evaluation Coach
Provides REST API endpoints for frontend and LLM integration
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional

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

        return SystemStatus(
            status="healthy",
            database_connected=db_connected,
            jira_connected=False,  # TODO: Implement Jira connection check
            llm_available=True,  # TODO: Check LLM availability
            last_sync=None,
            total_issues=total_issues,
            total_insights=total_insights,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System unhealthy: {str(e)}",
        )


# Dashboard Endpoints
@app.get("/api/v1/dashboard", response_model=DashboardData)
async def get_dashboard(
    scope: str = "portfolio", time_range: str = "last_pi", db: Session = Depends(get_db)
):
    """Get dashboard data for specified scope"""
    try:
        # Get portfolio metrics
        portfolio_metrics = [
            MetricValue(
                name="Flow Efficiency",
                value=67.0,
                unit="%",
                status="healthy",
                trend="up",
                benchmark={"industry": 15.0, "high_performer": 40.0},
            ),
            MetricValue(
                name="PI Predictability",
                value=82.0,
                unit="%",
                status="healthy",
                trend="up",
                benchmark={"target": 80.0},
            ),
            MetricValue(
                name="Defect Escape Rate",
                value=4.2,
                unit="%",
                status="healthy",
                trend="down",
                benchmark={"target": 5.0},
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

        # Get ART comparison
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
            {
                "art_name": "Data & Analytics",
                "flow_efficiency": 64.0,
                "pi_predictability": 83.0,
                "quality_score": 3.5,
                "status": "healthy",
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
    """Generate new insights for specified scope"""
    try:
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
    scope: str,
    scope_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    time_range: str = "last_pi",
    db: Session = Depends(get_db),
):
    """Get calculated metrics for specified scope"""
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


# Jira Integration Endpoints
@app.post("/api/v1/jira/sync")
async def sync_jira_data(db: Session = Depends(get_db)):
    """Trigger Jira data synchronization"""
    # TODO: Implement Jira sync
    return {"message": "Jira sync started", "status": "in_progress"}


@app.post("/api/v1/jira/issues", response_model=JiraIssueResponse)
async def create_jira_issue(issue: JiraIssueCreate, db: Session = Depends(get_db)):
    """Create or update Jira issue in database"""
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


# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
