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
    Action,
    AdminConfigResponse,
    AnalysisRequest,
    ARTPerformance,
    ChatRequest,
    ChatResponse,
    DashboardData,
    ExpectedOutcome,
    HealthScorecard,
    InsightFeedback,
    InsightResponse,
    JiraIssueCreate,
    JiraIssueResponse,
    MetricValue,
    ReportRequest,
    ReportResponse,
    RootCause,
    SystemStatus,
    ThresholdConfig,
)
from config.settings import settings
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


# LLM Configuration Endpoints
@app.post("/api/v1/config/llm")
async def save_llm_config(config: Dict[str, Any]):
    """Save LLM configuration (model and temperature)"""
    try:
        model = config.get("model", "gpt-4o-mini")
        temperature = float(config.get("temperature", 0.7))

        # Update the LLM service
        llm_service.model = model
        llm_service.temperature = temperature

        print(f"✅ LLM config updated: model={model}, temperature={temperature}")

        return {
            "status": "success",
            "config": {"model": model, "temperature": temperature},
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/config/llm")
async def get_llm_config():
    """Get current LLM configuration"""
    return {"model": llm_service.model, "temperature": llm_service.temperature}


# Insights Generation Endpoint
@app.post("/api/v1/insights/generate")
async def generate_insights_endpoint(
    scope: str = "portfolio",
    pis: Optional[str] = None,
    arts: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """Generate AI-powered insights using expert analysis (LLM)

    This is a separate endpoint to allow on-demand insight generation
    without slowing down the initial dashboard load.

    Args:
        scope: Scope of analysis (portfolio, art, team)
        pis: Comma-separated list of PIs
        arts: Comma-separated list of ARTs
        model: LLM model to use (e.g., gpt-4o, gpt-4o-mini)
        temperature: LLM temperature (0.0-2.0)
    """
    try:
        from agents.nodes.advanced_insights import generate_advanced_insights

        # Update LLM service with custom parameters if provided
        if model:
            llm_service.model = model
        if temperature is not None:
            llm_service.temperature = temperature

        print(
            f"🤖 Using LLM: model={llm_service.model}, temperature={llm_service.temperature}"
        )

        # Parse filter parameters
        selected_pis = (
            [pi.strip() for pi in pis.split(",") if pi.strip()] if pis else []
        )
        selected_arts = (
            [art.strip() for art in arts.split(",") if art.strip()] if arts else []
        )

        # Fetch ART comparison data for insights
        art_comparison = []
        if leadtime_service and leadtime_service.is_available():
            try:
                params = {}
                if selected_arts:
                    params["arts"] = (
                        selected_arts  # LeadTimeClient.get_analysis_summary() handles conversion to singular
                    )
                if selected_pis:
                    params["pis"] = (
                        selected_pis  # LeadTimeClient.get_analysis_summary() handles conversion to singular
                    )

                # Add threshold from settings
                params["threshold_days"] = settings.bottleneck_threshold_days

                # Get analysis summary
                analysis_summary = leadtime_service.client.get_analysis_summary(
                    **params
                )

                # Also get ART comparison for context, filtered by selected ARTs
                pip_params = {}
                if selected_arts:
                    pip_params["art"] = selected_arts[
                        0
                    ]  # Get pip_data for first selected ART
                pip_data = leadtime_service.client.get_pip_data(**pip_params)

                if pip_data:
                    art_comparison = [
                        {
                            "art_name": art.get("art_name", "Unknown"),
                            "flow_efficiency": float(
                                art.get("flow_efficiency_percent", 0)
                            ),
                            "planning_accuracy": float(art.get("pi_predictability", 0)),
                            "quality_score": float(art.get("quality_score", 0)),
                            "status": (
                                "healthy"
                                if float(art.get("flow_efficiency_percent", 0)) >= 70
                                else "warning"
                            ),
                        }
                        for art in pip_data
                    ]

                # Generate insights with LLM
                insights = generate_advanced_insights(
                    analysis_summary=analysis_summary,
                    art_comparison=art_comparison,
                    selected_arts=selected_arts,
                    selected_pis=selected_pis,
                    llm_service=llm_service,
                )

                print(f"✅ Generated {len(insights)} AI-powered insights")

                return {
                    "status": "success",
                    "insights": [insight.dict() for insight in insights],
                    "count": len(insights),
                }
            except Exception as e:
                print(f"❌ Error generating insights: {e}")
                import traceback

                traceback.print_exc()
                raise HTTPException(
                    status_code=500, detail=f"Failed to generate insights: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=503, detail="Lead-time service not available"
            )
    except Exception as e:
        print(f"❌ Error in generate insights endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard Endpoints
@app.get("/api/v1/dashboard", response_model=DashboardData)
async def get_dashboard(
    scope: str = "portfolio",
    time_range: str = "last_pi",
    pis: Optional[str] = None,
    arts: Optional[str] = None,
    generate_insights: bool = False,
    db: Session = Depends(get_db),
):
    """Get dashboard data for specified scope and optional PI/ART filter(s)

    Args:
        pis: Comma-separated list of PIs (e.g., "24Q1,24Q2,25Q1")
        arts: Comma-separated list of ARTs (e.g., "ACEART,C4ART,CIART")
        generate_insights: Whether to generate AI-powered insights (expensive LLM calls)
    """
    try:
        # Parse filter parameters
        selected_pis = []
        if pis:
            selected_pis = [pi.strip() for pi in pis.split(",") if pi.strip()]

        selected_arts = []
        if arts:
            selected_arts = [art.strip() for art in arts.split(",") if art.strip()]

        # Get portfolio metrics from lead-time service
        portfolio_metrics = []

        # Initialize default values
        flow_efficiency = 67.0
        planning_accuracy = 82.0
        throughput_count = 0
        avg_leadtime = 0.0

        if leadtime_service and leadtime_service.is_available():
            try:
                # Apply PI filter if specified (use selected PIs or None for all)
                pi_filter = selected_pis if selected_pis else None
                print(f"🔍 Calculating portfolio metrics with PI filter: {pi_filter}")

                # Get planning accuracy from pip_data
                # Planning Accuracy: (features with planned_committed=1 AND plc_delivery=1) / (features with planned_committed=1) * 100
                # Fetch pip_data - if ARTs are specified, fetch per-ART to ensure completeness
                if selected_arts:
                    # Fetch per ART to ensure we get all pip data
                    all_pip_features = []
                    for art in selected_arts:
                        art_pip_features = leadtime_service.client.get_pip_data(
                            art=art, limit=10000
                        )
                        all_pip_features.extend(art_pip_features)
                else:
                    # Get all pip_data when no ART filter
                    all_pip_features = leadtime_service.client.get_pip_data(limit=10000)

                # Filter by selected PIs
                filtered_pip_features = all_pip_features
                if selected_pis:
                    filtered_pip_features = [
                        f for f in filtered_pip_features if f.get("pi") in selected_pis
                    ]

                # Calculate Planning Accuracy from filtered data
                # Planning Accuracy = (committed features that were delivered) / (all committed features) * 100
                # Match DL Webb App logic: delivered means plc_delivery is not null/empty/"0"
                if filtered_pip_features:
                    planned_committed = sum(
                        1
                        for f in filtered_pip_features
                        if f.get("planned_committed", 0) > 0
                    )

                    # Delivered: planned_committed > 0 AND plc_delivery is truthy and not "0"
                    def is_delivered(plc_delivery):
                        if not plc_delivery:
                            return False
                        if plc_delivery in ["0", "", "null"]:
                            return False
                        return True

                    delivered = sum(
                        1
                        for f in filtered_pip_features
                        if f.get("planned_committed", 0) > 0
                        and is_delivered(f.get("plc_delivery"))
                    )

                    if planned_committed > 0:
                        planning_accuracy = round(
                            (delivered / planned_committed) * 100, 1
                        )
                        filter_desc = []
                        if selected_pis:
                            filter_desc.append(f"{len(selected_pis)} PIs")
                        if selected_arts:
                            filter_desc.append(f"{len(selected_arts)} ARTs")
                        print(
                            f"✅ Planning Accuracy: {planning_accuracy}% (filtered by {', '.join(filter_desc) if filter_desc else 'all'})"
                        )

                # Get lead-time statistics for Flow Efficiency
                # Fetch features - if ARTs are specified, fetch per-ART to avoid missing data
                if selected_arts:
                    # Fetch per ART to ensure we get all features
                    all_features = []
                    for art in selected_arts:
                        art_features = leadtime_service.client.get_flow_leadtime(
                            art=art, limit=10000
                        )
                        all_features.extend(art_features)
                else:
                    # Get all features when no ART filter
                    all_features = leadtime_service.client.get_flow_leadtime(
                        limit=10000
                    )

                # Filter by selected PIs if specified
                filtered_features = all_features
                if selected_pis:
                    filtered_features = [
                        f for f in filtered_features if f.get("pi") in selected_pis
                    ]

                if filtered_features:
                    value_add_times = []
                    total_times = []

                    for feature in filtered_features:
                        value_add = feature.get("in_progress", 0) + feature.get(
                            "in_reviewing", 0
                        )
                        total = feature.get("total_leadtime", 0)

                        if total > 0:
                            value_add_times.append(value_add)
                            total_times.append(total)

                    if value_add_times and total_times:
                        avg_value_add = sum(value_add_times) / len(value_add_times)
                        avg_total = sum(total_times) / len(total_times)
                        flow_efficiency = (
                            round((avg_value_add / avg_total) * 100, 1)
                            if avg_total > 0
                            else 0
                        )
                        print(
                            f"✅ Flow Efficiency: {flow_efficiency}% from {len(filtered_features)} features"
                        )

                # Get throughput - use leadtime_thr_data which contains ALL features delivered in a PI
                # This includes features planned in this PI OR previous PIs but delivered during this PI time period
                # Note: Data may have sync delays, so recent PIs might show incomplete counts
                if selected_arts:
                    # Fetch per ART to ensure completeness
                    all_throughput_features = []
                    for art in selected_arts:
                        art_throughput = leadtime_service.client.get_throughput_data(
                            art=art, limit=10000
                        )
                        all_throughput_features.extend(art_throughput)
                else:
                    # Get all throughput data when no ART filter
                    all_throughput_features = (
                        leadtime_service.client.get_throughput_data(limit=10000)
                    )

                # Filter by selected PIs
                filtered_throughput = all_throughput_features
                if selected_pis:
                    filtered_throughput = [
                        f for f in filtered_throughput if f.get("pi") in selected_pis
                    ]

                throughput_count = len(filtered_throughput)
                print(
                    f"✅ Features Delivered: {throughput_count} (from leadtime_thr_data - may have sync delays)"
                )

                # Calculate average lead-time from throughput data (completed features only)
                if filtered_throughput:
                    leadtimes = [
                        f.get("lead_time_days", 0)
                        for f in filtered_throughput
                        if f.get("lead_time_days", 0) > 0
                    ]
                    if leadtimes:
                        avg_leadtime = round(sum(leadtimes) / len(leadtimes), 1)
                        print(
                            f"✅ Average Lead-Time: {avg_leadtime} days from {len(leadtimes)} completed features"
                        )

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
                name="Planning Accuracy",
                value=planning_accuracy,
                unit="%",
                status="healthy" if planning_accuracy >= 70 else "warning",
                trend="stable",
                benchmark={"target": 80.0},
            ),
            MetricValue(
                name="Average Lead-Time",
                value=avg_leadtime,
                unit="days",
                status=(
                    "healthy"
                    if avg_leadtime <= 30
                    else ("warning" if avg_leadtime <= 60 else "critical")
                ),
                trend="stable",
                benchmark={"target": 30.0, "max_acceptable": 60.0},
            ),
            MetricValue(
                name="Features Delivered",
                value=throughput_count,
                unit="features",
                status="healthy" if throughput_count >= 150 else "warning",
                trend="up",
                benchmark={"target": 150.0},
            ),
        ]

        # Get ART comparison from lead-time service
        art_comparison = []
        if leadtime_service and leadtime_service.is_available():
            try:
                # Get available ARTs from lead-time server
                filters = leadtime_service.get_available_filters()
                all_arts = filters.get("arts", [])

                # Filter by selected ARTs if specified
                if selected_arts:
                    arts_list = [art for art in all_arts if art in selected_arts]
                    print(
                        f"🎯 Filtering to {len(arts_list)} ARTs: {', '.join(arts_list)}"
                    )
                else:
                    arts_list = all_arts
                    print(f"📊 Processing all {len(arts_list)} ARTs")

                for art_name in arts_list:
                    try:
                        # Get raw feature data for this ART to calculate accurate metrics
                        # Note: API expects single PI, so we filter in memory if multiple PIs selected
                        features = leadtime_service.client.get_flow_leadtime(
                            art=art_name, limit=10000
                        )

                        # Filter by selected PIs if specified
                        if selected_pis:
                            features = [
                                f for f in features if f.get("pi") in selected_pis
                            ]

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

                            # Get average lead-time from throughput data (completed features only)
                            throughput_features = (
                                leadtime_service.client.get_throughput_data(
                                    art=art_name, limit=10000
                                )
                            )
                            # Filter by selected PIs if specified
                            if selected_pis:
                                throughput_features = [
                                    f
                                    for f in throughput_features
                                    if f.get("pi") in selected_pis
                                ]

                            if throughput_features:
                                thr_leadtimes = [
                                    f.get("lead_time_days", 0)
                                    for f in throughput_features
                                    if f.get("lead_time_days", 0) > 0
                                ]
                                avg_leadtime_art = (
                                    sum(thr_leadtimes) / len(thr_leadtimes)
                                    if thr_leadtimes
                                    else 0
                                )
                            else:
                                avg_leadtime_art = 0

                            # Get planning accuracy for this ART from pip_data
                            pip_features = leadtime_service.client.get_pip_data(
                                art=art_name, limit=10000
                            )

                            # Filter by selected PIs if specified
                            if selected_pis:
                                pip_features = [
                                    f
                                    for f in pip_features
                                    if f.get("pi") in selected_pis
                                ]
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
                                planning_accuracy = (
                                    (delivered / planned_committed * 100)
                                    if planned_committed > 0
                                    else 0
                                )
                            else:
                                planning_accuracy = 0

                            # Quality score: Estimate based on consistency (lower variability = better)
                            # Using coefficient of variation of total lead time
                            if total_times and len(total_times) > 1:
                                import statistics

                                mean_lt = statistics.mean(total_times)
                                stdev_lt = statistics.stdev(total_times)
                                coeff_var = (stdev_lt / mean_lt) if mean_lt > 0 else 1.0
                                # Convert to percentage score (lower variability = higher score)
                                quality_score = max(
                                    0.0, min(100.0, 100.0 - (coeff_var * 50))
                                )
                            else:
                                quality_score = 50.0

                            # Status based on Planning Accuracy
                            if planning_accuracy >= 70:
                                status_val = "healthy"
                            elif planning_accuracy >= 50:
                                status_val = "warning"
                            else:
                                status_val = "critical"

                            art_comparison.append(
                                {
                                    "art_name": art_name,
                                    "flow_efficiency": round(flow_efficiency, 1),
                                    "planning_accuracy": round(planning_accuracy, 1),
                                    "avg_leadtime": round(avg_leadtime_art, 1),
                                    "quality_score": round(quality_score, 1),
                                    "features_delivered": len(throughput_features),
                                    "status": status_val,
                                }
                            )
                        else:
                            # No data for this ART
                            art_comparison.append(
                                {
                                    "art_name": art_name,
                                    "flow_efficiency": 0.0,
                                    "planning_accuracy": 0.0,
                                    "avg_leadtime": 0.0,
                                    "quality_score": 0.0,
                                    "features_delivered": 0,
                                    "status": "no_data",
                                }
                            )
                    except Exception as e:
                        print(f"⚠️  Error calculating metrics for ART {art_name}: {e}")
                        import traceback

                        traceback.print_exc()
                        art_comparison.append(
                            {
                                "art_name": art_name,
                                "flow_efficiency": 0.0,
                                "pi_predictability": 0.0,
                                "quality_score": 0.0,
                                "status": "error",
                            }
                        )
                        continue

            except Exception as e:
                print(f"⚠️  Could not fetch ART data from lead-time service: {e}")
                import traceback

                traceback.print_exc()

        # Fallback to sample data if lead-time service not available
        if not art_comparison:
            art_comparison = [
                {
                    "art_name": "Platform Engineering",
                    "flow_efficiency": 72.0,
                    "planning_accuracy": 85.0,
                    "quality_score": 3.8,
                    "status": "healthy",
                },
                {
                    "art_name": "Customer Experience",
                    "flow_efficiency": 65.0,
                    "planning_accuracy": 78.0,
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

        # Generate automatic insights only if requested (expensive LLM operation)
        if generate_insights and not recent_insights:
            from agents.nodes.advanced_insights import generate_advanced_insights

            # Try to fetch comprehensive analysis summary for advanced insights
            if leadtime_service and leadtime_service.is_available() and art_comparison:
                try:
                    # Build params for analysis summary - use lists for arts and pis
                    params = {}
                    if selected_arts:
                        params["arts"] = selected_arts[
                            :1
                        ]  # Use first ART for summary analysis
                    if selected_pis:
                        params["pis"] = selected_pis[
                            :1
                        ]  # Use first PI for summary analysis

                    # Fetch comprehensive analysis
                    analysis_summary = leadtime_service.client.get_analysis_summary(
                        **params
                    )

                    # Generate advanced insights with LLM expert commentary
                    recent_insights = generate_advanced_insights(
                        analysis_summary=analysis_summary,
                        art_comparison=art_comparison,
                        selected_arts=selected_arts,
                        selected_pis=selected_pis,
                        llm_service=llm_service,
                    )

                    print(
                        f"✅ Generated {len(recent_insights)} advanced insights from analysis summary"
                    )
                    if recent_insights:
                        print(
                            f"   First insight: {recent_insights[0].title if hasattr(recent_insights[0], 'title') else 'Unknown'}"
                        )
                except Exception as e:
                    print(f"⚠️  Could not generate advanced insights: {e}")
                    import traceback

                    traceback.print_exc()
                    # Fall back to basic insights
                    recent_insights = []

        # Fallback to basic insights if advanced generation failed
        if not recent_insights and art_comparison:
            from datetime import datetime

            # Flow efficiency insights
            low_flow_arts = [
                art for art in art_comparison if art.get("flow_efficiency", 0) < 30
            ]
            if low_flow_arts:
                recent_insights.append(
                    InsightResponse(
                        id=0,
                        title=f"Low Flow Efficiency Detected in {len(low_flow_arts)} ART(s)",
                        severity="warning",
                        confidence=0.85,
                        scope="portfolio",
                        scope_id=None,
                        observation=f"ARTs with flow efficiency below 30%: {', '.join([art['art_name'] for art in low_flow_arts[:3]])}",
                        interpretation="These teams are spending too much time waiting (in backlog, planned stages) vs. active work.",
                        root_causes=[
                            RootCause(
                                description="Excessive work in progress (WIP)",
                                evidence=[],
                                confidence=0.8,
                                reference=None,
                            ),
                            RootCause(
                                description="Bottlenecks in workflow",
                                evidence=[],
                                confidence=0.75,
                                reference=None,
                            ),
                        ],
                        recommended_actions=[
                            Action(
                                timeframe="short-term",
                                description="Implement WIP limits",
                                owner="ART leadership",
                                effort="medium",
                                dependencies=[],
                                success_signal="Reduced cycle time",
                            ),
                            Action(
                                timeframe="medium-term",
                                description="Identify and remove bottlenecks",
                                owner="Process improvement team",
                                effort="high",
                                dependencies=[],
                                success_signal="Improved flow efficiency",
                            ),
                        ],
                        expected_outcomes=ExpectedOutcome(
                            metrics_to_watch=["flow_efficiency", "cycle_time"],
                            leading_indicators=["WIP reduction", "Bottleneck removal"],
                            lagging_indicators=["Increased throughput"],
                            timeline="2-3 PIs",
                            risks=["Team resistance to change"],
                        ),
                        metric_references=[
                            f"{art['art_name']}: {art['flow_efficiency']}%"
                            for art in low_flow_arts[:3]
                        ],
                        evidence=["Historical flow data", "ART comparison metrics"],
                        status="active",
                        created_at=datetime.now(),
                    )
                )

            # Planning Accuracy insights
            low_accuracy_arts = [
                art for art in art_comparison if art.get("planning_accuracy", 0) < 70
            ]
            if low_accuracy_arts:
                recent_insights.append(
                    InsightResponse(
                        id=0,
                        title=f"Planning Accuracy Below Target in {len(low_accuracy_arts)} ART(s)",
                        severity="warning",
                        confidence=0.9,
                        scope="portfolio",
                        scope_id=None,
                        observation=f"{len(low_accuracy_arts)} ARTs are below 70% Planning Accuracy target",
                        interpretation="Teams are not consistently delivering what they commit to during PI Planning.",
                        root_causes=[
                            RootCause(
                                description="Over-commitment during planning",
                                evidence=[],
                                confidence=0.85,
                                reference=None,
                            ),
                            RootCause(
                                description="Mid-PI scope changes",
                                evidence=[],
                                confidence=0.7,
                                reference=None,
                            ),
                        ],
                        recommended_actions=[
                            Action(
                                timeframe="short-term",
                                description="Review PI Planning process and capacity calculation",
                                owner="RTE",
                                effort="low",
                                dependencies=[],
                                success_signal="More realistic commitments",
                            ),
                            Action(
                                timeframe="medium-term",
                                description="Implement 20% buffer for unknowns",
                                owner="Team leads",
                                effort="low",
                                dependencies=[],
                                success_signal="Improved predictability",
                            ),
                        ],
                        expected_outcomes=ExpectedOutcome(
                            metrics_to_watch=["planning_accuracy"],
                            leading_indicators=[
                                "More conservative planning",
                                "Buffer utilization",
                            ],
                            lagging_indicators=["Stakeholder satisfaction"],
                            timeline="1-2 PIs",
                            risks=["Perceived as under-committing"],
                        ),
                        metric_references=[
                            f"{art['art_name']}: {art['planning_accuracy']}%"
                            for art in low_accuracy_arts[:3]
                        ],
                        evidence=["PI planning data", "Delivery metrics"],
                        status="active",
                        created_at=datetime.now(),
                    )
                )

            # High performers
            high_performers = [
                art
                for art in art_comparison
                if art.get("flow_efficiency", 0) > 50
                and art.get("planning_accuracy", 0) > 80
            ]
            if high_performers:
                recent_insights.append(
                    InsightResponse(
                        id=0,
                        title=f"High Performing Teams: {', '.join([art['art_name'] for art in high_performers[:3]])}",
                        severity="info",
                        confidence=0.95,
                        scope="portfolio",
                        scope_id=None,
                        observation=f"{len(high_performers)} ART(s) showing excellent flow efficiency (>50%) and predictability (>80%)",
                        interpretation="These teams have optimized workflows and reliable planning practices worth sharing.",
                        root_causes=[
                            RootCause(
                                description="Effective WIP management",
                                evidence=[],
                                confidence=0.9,
                                reference=None,
                            ),
                            RootCause(
                                description="Strong team collaboration and practices",
                                evidence=[],
                                confidence=0.85,
                                reference=None,
                            ),
                        ],
                        recommended_actions=[
                            Action(
                                timeframe="short-term",
                                description="Conduct Communities of Practice sessions to share best practices",
                                owner="Portfolio leadership",
                                effort="low",
                                dependencies=[],
                                success_signal="Knowledge sharing sessions held",
                            ),
                            Action(
                                timeframe="medium-term",
                                description="Document and replicate successful patterns",
                                owner="CoP leaders",
                                effort="medium",
                                dependencies=[],
                                success_signal="Practice guides published",
                            ),
                        ],
                        expected_outcomes=ExpectedOutcome(
                            metrics_to_watch=["flow_efficiency", "pi_predictability"],
                            leading_indicators=[
                                "Practice adoption",
                                "Cross-team collaboration",
                            ],
                            lagging_indicators=["Portfolio-wide improvement"],
                            timeline="2-3 PIs",
                            risks=["Context differences between teams"],
                        ),
                        metric_references=[
                            f"{art['art_name']}: {art['flow_efficiency']}% flow, {art['pi_predictability']}% predictability"
                            for art in high_performers[:3]
                        ],
                        evidence=["Performance metrics", "ART comparison data"],
                        status="active",
                        created_at=datetime.now(),
                    )
                )

        # Get PI data from lead-time service
        current_pi = None
        available_pis = []

        if leadtime_service and leadtime_service.is_available():
            try:
                filters = leadtime_service.get_available_filters()
                all_pis = filters.get("pis", [])
                # Filter to show only PIs from 24Q1 onwards and sort descending
                available_pis = sorted(
                    [pi for pi in all_pis if pi >= "24Q1"], reverse=True
                )
                # Set current PI to the most recent one
                if available_pis:
                    current_pi = available_pis[0]

                # Log selected PIs if any
                if selected_pis:
                    print(f"📅 Filtering by PIs: {selected_pis}")
            except Exception as e:
                print(f"⚠️  Could not fetch PI data: {e}")

        return DashboardData(
            portfolio_metrics=portfolio_metrics,
            art_comparison=art_comparison,
            recent_insights=recent_insights,
            trends={},
            current_pi=current_pi,
            available_pis=available_pis,
            selected_pis=selected_pis if selected_pis else None,
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
                            title=f"Low Planning Accuracy: {score:.1f}%",
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
                                "metrics_to_watch": ["Planning Accuracy"],
                                "leading_indicators": ["Commitment vs Actual"],
                                "lagging_indicators": ["Planning Accuracy"],
                                "timeline": "1-2 PIs",
                                "risks": ["Resistance to reduced commitments"],
                            },
                            metric_references=["planning_accuracy"],
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


# ============================================================================
# Metrics Catalog Endpoint
# ============================================================================


@app.get("/api/metrics/catalog")
async def get_metrics_catalog(
    arts: Optional[str] = None,
    pis: Optional[str] = None,
):
    """
    Get comprehensive metrics catalog with real data.

    Args:
        arts: Comma-separated list of ARTs (e.g., "SAART,ACEART")
        pis: Comma-separated list of PIs (e.g., "26Q1,25Q4")

    Returns:
        Metrics catalog with current values and benchmarks
    """
    if not leadtime_service or not leadtime_service.is_available():
        raise HTTPException(status_code=503, detail="Lead-time service not available")

    try:
        # Parse filters
        selected_arts = (
            [art.strip() for art in arts.split(",") if art.strip()] if arts else []
        )
        selected_pis = (
            [pi.strip() for pi in pis.split(",") if pi.strip()] if pis else []
        )

        # Get analysis summary
        params = {}
        if selected_arts:
            params["arts"] = selected_arts
        if selected_pis:
            params["pis"] = selected_pis
        params["threshold_days"] = settings.bottleneck_threshold_days

        analysis = leadtime_service.client.get_analysis_summary(**params)

        # Extract metrics
        leadtime_data = analysis.get("leadtime_analysis", {})
        stage_stats = leadtime_data.get("stage_statistics", {})
        bottleneck_data = analysis.get("bottleneck_analysis", {})

        # Get Feature-only WIP statistics (not all work items)
        feature_wip_stats = leadtime_service.client.get_feature_wip_statistics(
            arts=selected_arts, pis=selected_pis
        )

        planning_data = analysis.get("planning_accuracy", {})
        throughput_data = analysis.get("throughput_analysis", {})

        # Get waste and throughput analysis
        waste_data = leadtime_service.client.get_waste_analysis(
            arts=selected_arts, pis=selected_pis
        )
        throughput_full = leadtime_service.client.get_throughput_analysis(
            arts=selected_arts, pis=selected_pis
        )

        # Calculate waste metrics
        waiting_waste = waste_data.get("waiting_time_waste", {})
        removed_work = waste_data.get("removed_work", {})
        total_waste = waste_data.get("total_waste_days", 0)
        waste_categories = waste_data.get("waste_categories", {})

        # Extract throughput trends
        throughput_by_pi = throughput_full.get("by_pi", {})
        overall_throughput = throughput_full.get("overall_statistics", {})

        # Get raw flow data for proper calculations
        flow_data = leadtime_service.client.get_flow_leadtime(
            arts=selected_arts, pis=selected_pis
        )

        # Calculate proper lead time statistics (not sum of stage means!)
        completed_items = [f for f in flow_data if f.get("total_leadtime", 0) > 0]
        if completed_items:
            leadtimes = [f["total_leadtime"] for f in completed_items]
            leadtimes_sorted = sorted(leadtimes)
            median_leadtime = (
                leadtimes_sorted[len(leadtimes_sorted) // 2] if leadtimes_sorted else 0
            )
            p85_index = int(len(leadtimes_sorted) * 0.85)
            p85_leadtime = (
                leadtimes_sorted[p85_index]
                if p85_index < len(leadtimes_sorted)
                else leadtimes_sorted[-1] if leadtimes_sorted else 0
            )
            mean_leadtime = sum(leadtimes) / len(leadtimes)
        else:
            median_leadtime = 0
            p85_leadtime = 0
            mean_leadtime = 0

        # Calculate Flow Efficiency (active time / total time)
        active_stages = ["in_progress", "in_reviewing", "in_sit", "in_uat"]
        wait_stages = [
            "in_backlog",
            "in_analysis",
            "in_planned",
            "ready_for_sit",
            "ready_for_uat",
            "ready_for_deployment",
        ]

        total_active_time = sum(
            stage_stats.get(s, {}).get("mean", 0) for s in active_stages
        )
        total_wait_time = sum(
            stage_stats.get(s, {}).get("mean", 0) for s in wait_stages
        )
        total_flow_time = total_active_time + total_wait_time
        flow_efficiency = (
            (total_active_time / total_flow_time * 100) if total_flow_time > 0 else 0
        )

        # Calculate Flow Distribution (work type breakdown)
        # Get feature data to determine types
        feature_data = leadtime_service.client.get_feature_data()
        if selected_arts:
            feature_data = [f for f in feature_data if f.get("art") in selected_arts]
        if selected_pis:
            feature_data = [
                f for f in feature_data if f.get("program_increment") in selected_pis
            ]

        feature_types = {}
        for f in feature_data:
            ftype = f.get("feature_type", "Unknown")
            feature_types[ftype] = feature_types.get(ftype, 0) + 1

        total_features = sum(feature_types.values())
        flow_distribution = (
            {
                ftype: round(count / total_features * 100, 1)
                for ftype, count in feature_types.items()
            }
            if total_features > 0
            else {}
        )

        # Calculate WIP (Features only - not stories/tasks)
        # Active stages = stages where work is actively being done
        # Excludes: in_backlog, in_analysis, in_planned (these are queued/waiting to start)
        wip_total = sum(
            stats.get("total_items", 0) for stats in feature_wip_stats.values()
        )

        # Get planning accuracy - try multiple sources as API structure varies
        planning_accuracy = planning_data.get("overall_accuracy")
        if planning_accuracy is None:
            # Try predictability_score as fallback
            planning_accuracy = planning_data.get("predictability_score", 0)

        # Note: API returns planning_accuracy as a percentage already (e.g., 0.5714 = 0.57%)
        # Do NOT multiply by 100
        if planning_accuracy is None:
            planning_accuracy = 0

        # Build metrics catalog (SAFe Flow Metrics)
        metrics = {
            "flow_metrics": {
                "flow_time": {
                    "name": "Flow Time (Lead Time)",
                    "description": "SAFe: Total time from work start to completion. Median represents typical feature, P85 shows 85% complete within this time.",
                    "formula": "median(end_date - start_date) per feature",
                    "current_value": round(median_leadtime, 1),
                    "median": round(median_leadtime, 1),
                    "p85": round(p85_leadtime, 1),
                    "mean": round(mean_leadtime, 1),
                    "unit": "days",
                    "status": (
                        "critical"
                        if median_leadtime > 90
                        else "warning" if median_leadtime > 30 else "good"
                    ),
                    "target": "<30 days (SAFe High Performer)",
                    "jira_fields": ["created", "resolutiondate", "status transitions"],
                    "stage_breakdown": {
                        stage: {
                            "mean": round(stats.get("mean", 0), 1),
                            "median": round(stats.get("median", 0), 1),
                            "p85": round(stats.get("p85", 0), 1),
                            "count": stats.get("count", 0),
                        }
                        for stage, stats in stage_stats.items()
                    },
                },
                "flow_efficiency": {
                    "name": "Flow Efficiency",
                    "description": "SAFe: Ratio of active work time to total flow time. Measures waste from waiting/queues.",
                    "formula": "(active_time / total_time) × 100%",
                    "current_value": round(flow_efficiency, 1),
                    "active_time": round(total_active_time, 1),
                    "wait_time": round(total_wait_time, 1),
                    "unit": "%",
                    "status": (
                        "good"
                        if flow_efficiency >= 40
                        else "warning" if flow_efficiency >= 15 else "critical"
                    ),
                    "target": "≥40% (SAFe Best Practice)",
                    "jira_fields": ["status", "status transitions"],
                },
                "flow_distribution": {
                    "name": "Flow Distribution",
                    "description": "SAFe: Percentage of work by type (Features, Enablers, Defects, Debt). Ensures balanced value delivery.",
                    "formula": "(count_by_type / total_count) × 100%",
                    "distribution": flow_distribution,
                    "unit": "%",
                    "status": "good",
                    "target": "Features: 50-70%, Defects: <20%, Debt: 10-20%",
                    "jira_fields": ["issuetype", "labels"],
                },
                "flow_load": {
                    "name": "Flow Load (WIP)",
                    "description": "SAFe: Features currently in the system. High WIP increases lead time (Little's Law). ART-level = Features only.",
                    "formula": "count(Features WHERE status IN active_stages)",
                    "current_value": wip_total,
                    "unit": "features",
                    "status": (
                        "critical"
                        if wip_total > 150
                        else "warning" if wip_total > 100 else "good"
                    ),
                    "target": "<100 features (implement WIP limits)",
                    "jira_fields": ["status", "assignee", "issuetype"],
                    "breakdown_by_stage": {
                        stage: stats.get("total_items", 0)
                        for stage, stats in feature_wip_stats.items()
                    },
                },
                "flow_velocity": {
                    "name": "Flow Velocity (Throughput)",
                    "description": "SAFe: Features completed per PI. Tracked per PI to measure predictability and capacity.",
                    "formula": "count(status = 'Done' AND resolved IN pi_timeframe)",
                    "current_value": overall_throughput.get("total_throughput", 0),
                    "unit": "features",
                    "average_per_pi": round(
                        overall_throughput.get("total_throughput", 0)
                        / max(len(throughput_by_pi), 1),
                        1,
                    ),
                    "status": "good",
                    "target": "Stable throughput per PI (use for capacity planning)",
                    "jira_fields": ["status", "resolutiondate", "fixVersion"],
                    "trend_by_pi": {
                        pi: {
                            "throughput": data.get("throughput", 0),
                            "avg_leadtime": round(data.get("average_leadtime", 0), 1),
                        }
                        for pi, data in sorted(throughput_by_pi.items())[
                            -6:
                        ]  # Last 6 PIs
                    },
                },
                "waste": {
                    "name": "Process Waste",
                    "description": "Days wasted in waiting states and removed work",
                    "formula": "sum(waiting_time) + removed_work_count",
                    "current_value": round(total_waste, 1),
                    "unit": "days",
                    "status": (
                        waste_categories.get("waiting_waste", "unknown").lower()
                        if isinstance(waste_categories.get("waiting_waste"), str)
                        else "unknown"
                    ),
                    "jira_fields": ["status", "status transitions"],
                    "breakdown": {
                        "waiting_time": {
                            stage: round(stats.get("total_days_wasted", 0), 1)
                            for stage, stats in waiting_waste.items()
                        },
                        "removed_work": {
                            "duplicates": removed_work.get("duplicates", 0),
                            "planned_removed": removed_work.get(
                                "planned_committed_removed", 0
                            )
                            + removed_work.get("planned_uncommitted_removed", 0),
                            "added_removed": removed_work.get(
                                "added_committed_removed", 0
                            )
                            + removed_work.get("added_uncommitted_removed", 0),
                        },
                    },
                },
            },
            "predictability_metrics": {
                "planning_accuracy": {
                    "name": "Planning Accuracy",
                    "description": "Percentage of committed work completed",
                    "formula": "(completed_count / committed_count) * 100",
                    "current_value": round(planning_accuracy, 1),
                    "unit": "%",
                    "threshold": settings.planning_accuracy_threshold_pct,
                    "status": (
                        "critical"
                        if planning_accuracy < settings.planning_accuracy_threshold_pct
                        else "good"
                    ),
                    "jira_fields": ["labels", "fixVersion", "status"],
                },
                "velocity_stability": {
                    "name": "Velocity Stability",
                    "description": "Standard deviation of velocity over last 6 sprints",
                    "formula": "stdev(story_points_completed)",
                    "current_value": 0,  # Not available yet
                    "unit": "story points",
                    "status": "unknown",
                    "jira_fields": ["customfield_10016 (story points)", "sprint"],
                },
            },
            "quality_metrics": {
                "defect_rate": {
                    "name": "Defect Rate",
                    "description": "Bugs found per feature delivered",
                    "formula": "count(type='Bug') / count(type='Story')",
                    "current_value": 0,  # Not available yet
                    "unit": "bugs/story",
                    "status": "unknown",
                    "jira_fields": ["issuetype", "parent"],
                }
            },
            "scope": {
                "arts": selected_arts if selected_arts else ["All ARTs"],
                "pis": selected_pis if selected_pis else ["All PIs"],
                "threshold_days": settings.bottleneck_threshold_days,
            },
        }

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch metrics: {str(e)}"
        )


# ============================================================================
# Admin Configuration Endpoints
# ============================================================================


@app.get("/api/admin/config", response_model=AdminConfigResponse)
async def get_admin_config():
    """
    Get current admin configuration including thresholds and settings.

    Returns:
        Current configuration settings
    """
    thresholds = ThresholdConfig(
        bottleneck_threshold_days=settings.bottleneck_threshold_days,
        planning_accuracy_threshold_pct=settings.planning_accuracy_threshold_pct,
        threshold_in_backlog=settings.threshold_in_backlog,
        threshold_in_analysis=settings.threshold_in_analysis,
        threshold_in_planned=settings.threshold_in_planned,
        threshold_in_progress=settings.threshold_in_progress,
        threshold_in_reviewing=settings.threshold_in_reviewing,
        threshold_ready_for_sit=settings.threshold_ready_for_sit,
        threshold_in_sit=settings.threshold_in_sit,
        threshold_ready_for_uat=settings.threshold_ready_for_uat,
        threshold_in_uat=settings.threshold_in_uat,
        threshold_ready_for_deployment=settings.threshold_ready_for_deployment,
    )

    return AdminConfigResponse(
        thresholds=thresholds,
        leadtime_server_url=settings.leadtime_server_url,
        leadtime_server_enabled=settings.leadtime_server_enabled,
    )


@app.post("/api/admin/config/thresholds")
async def update_thresholds(thresholds: ThresholdConfig):
    """
    Update threshold configuration.

    NOTE: This updates runtime configuration. For persistent changes,
    update the .env file or environment variables.

    Args:
        thresholds: New threshold configuration

    Returns:
        Updated configuration
    """
    # Update settings (runtime only)
    settings.bottleneck_threshold_days = thresholds.bottleneck_threshold_days
    settings.planning_accuracy_threshold_pct = (
        thresholds.planning_accuracy_threshold_pct
    )
    settings.threshold_in_backlog = thresholds.threshold_in_backlog
    settings.threshold_in_analysis = thresholds.threshold_in_analysis
    settings.threshold_in_planned = thresholds.threshold_in_planned
    settings.threshold_in_progress = thresholds.threshold_in_progress
    settings.threshold_in_reviewing = thresholds.threshold_in_reviewing
    settings.threshold_ready_for_sit = thresholds.threshold_ready_for_sit
    settings.threshold_in_sit = thresholds.threshold_in_sit
    settings.threshold_ready_for_uat = thresholds.threshold_ready_for_uat
    settings.threshold_in_uat = thresholds.threshold_in_uat
    settings.threshold_ready_for_deployment = thresholds.threshold_ready_for_deployment

    return {
        "status": "success",
        "message": "Thresholds updated successfully (runtime only)",
        "thresholds": thresholds,
    }


# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
