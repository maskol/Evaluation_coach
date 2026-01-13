"""
FastAPI main application for Evaluation Coach
Provides REST API endpoints for frontend and LLM integration
"""

import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
    LLMConfigUpdate,
    MetricValue,
    PIReportRequest,
    ReportRequest,
    ReportResponse,
    RootCause,
    SystemStatus,
    ThresholdConfig,
)
from config.settings import settings
from database import (
    Base,
    RuntimeConfiguration,
    StrategicTarget,
    engine,
    get_db,
    init_db,
)
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    allow_origins=[
        "http://localhost:8800",
        "http://127.0.0.1:8800",
        "http://localhost:8850",
        "http://127.0.0.1:8850",
    ],
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
    import sys

    init_db()
    # Load persisted configuration from database
    print("📦 Loading configuration from database...", flush=True)
    sys.stdout.flush()
    load_config_from_db()
    print("🚀 Evaluation Coach API started", flush=True)
    sys.stdout.flush()


# Configuration persistence helpers
def load_config_from_db():
    """Load configuration from database into settings object"""
    print("📦 Loading configuration from database...")
    # `get_db()` is a generator dependency for request scope.
    # Calling `next(get_db())` here leaks the generator/session and can stall startup.
    from database import SessionLocal

    db = SessionLocal()
    loaded_count = 0
    try:
        config_fields = [
            # Strategic targets
            "leadtime_target_2026",
            "leadtime_target_2027",
            "leadtime_target_true_north",
            "planning_accuracy_target_2026",
            "planning_accuracy_target_2027",
            "planning_accuracy_target_true_north",
            # Feature-level thresholds
            "bottleneck_threshold_days",
            "planning_accuracy_threshold_pct",
            # Story-level thresholds
            "story_bottleneck_threshold_days",
            # Feature stage-specific thresholds
            "threshold_in_backlog",
            "threshold_in_analysis",
            "threshold_in_planned",
            "threshold_in_progress",
            "threshold_in_reviewing",
            "threshold_ready_for_sit",
            "threshold_in_sit",
            "threshold_ready_for_uat",
            "threshold_in_uat",
            "threshold_ready_for_deployment",
            # Story stage-specific thresholds
            "story_threshold_refinement",
            "story_threshold_ready_for_development",
            "story_threshold_in_development",
            "story_threshold_in_review",
            "story_threshold_ready_for_test",
            "story_threshold_in_testing",
            "story_threshold_ready_for_deployment",
        ]

        for field in config_fields:
            try:
                config_row = (
                    db.query(RuntimeConfiguration)
                    .filter(RuntimeConfiguration.config_key == field)
                    .first()
                )

                if config_row and config_row.config_value is not None:
                    setattr(settings, field, config_row.config_value)
                    print(f"   ✅ Loaded {field} = {config_row.config_value}")
                    loaded_count += 1
            except Exception as field_error:
                print(f"   ⚠️  Error loading {field}: {field_error}")

        if loaded_count == 0:
            print("   ℹ️  No configuration values found in database")
        else:
            print(f"   ✅ Loaded {loaded_count} configuration values")

    except Exception as e:
        print(f"⚠️  Could not load configuration from database: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


def save_config_to_db(db: Session, config_key: str, config_value: Optional[float]):
    """Save a configuration value to database"""
    try:
        config_row = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == config_key)
            .first()
        )

        if config_row:
            config_row.config_value = config_value
            config_row.updated_at = datetime.now()
        else:
            config_row = RuntimeConfiguration(
                config_key=config_key,
                config_value=config_value,
            )
            db.add(config_row)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def get_excluded_feature_statuses(db: Session) -> List[str]:
    """
    Get list of feature statuses to exclude from analysis.

    Args:
        db: Database session

    Returns:
        List of status strings to exclude (e.g., ['Cancelled', 'On Hold'])
    """
    try:
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "excluded_feature_statuses")
            .first()
        )
        if config_entry and config_entry.config_value:
            # Parse comma-separated list
            excluded = [
                s.strip() for s in config_entry.config_value.split(",") if s.strip()
            ]
            if excluded:
                print(f"🔍 Excluding feature statuses: {excluded}")
            return excluded
        return []
    except Exception as e:
        print(f"⚠️ Could not load excluded_feature_statuses config: {e}")
        return []


def filter_features_by_status(
    features: List[Dict[str, Any]], excluded_statuses: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter out features with excluded statuses.

    Args:
        features: List of feature dictionaries
        excluded_statuses: List of status strings to exclude

    Returns:
        Filtered list of features
    """
    if not excluded_statuses:
        return features

    original_count = len(features)
    filtered_features = [
        f for f in features if f.get("status") not in excluded_statuses
    ]
    filtered_count = len(filtered_features)

    if filtered_count < original_count:
        print(
            f"🔍 Filtered {original_count - filtered_count} features with excluded statuses (showing {filtered_count})"
        )

    return filtered_features


# Get available AI models endpoint
@app.get("/api/v1/models/available")
async def get_available_models():
    """Get list of available AI models (OpenAI + Ollama)"""
    try:
        models = {"openai": [], "ollama": []}

        # OpenAI models (if API key is configured)
        if llm_service.use_openai:
            models["openai"] = [
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "description": "Fast, Recommended",
                },
                {"id": "gpt-4o", "name": "GPT-4o", "description": "Balanced"},
                {
                    "id": "gpt-4-turbo",
                    "name": "GPT-4 Turbo",
                    "description": "Detailed, Slower",
                },
                {
                    "id": "gpt-4-turbo-preview",
                    "name": "GPT-4 Turbo Preview",
                    "description": "Preview",
                },
            ]

        # Ollama models (check what's actually installed)
        ollama_models = llm_service.get_available_ollama_models()
        if ollama_models:
            # Map model IDs to friendly names
            model_descriptions = {
                "llama3.3": "Latest Llama",
                "llama3.2": "Llama 3.2",
                "llama3.1": "Llama 3.1",
                "llama3": "Llama 3",
                "mistral": "Fast & Efficient",
                "mistral-nemo": "Mistral Nemo",
                "qwen2.5": "Excellent Reasoning",
                "qwen2.5-coder": "Qwen Coder",
                "qwen2": "Qwen 2",
                "deepseek-r1": "Advanced Reasoning",
                "deepseek-coder": "DeepSeek Coder",
                "phi4": "Small & Fast",
                "phi3": "Phi 3",
                "gemma2": "Gemma 2",
                "gemma": "Gemma",
            }

            for model_id in ollama_models:
                models["ollama"].append(
                    {
                        "id": model_id,
                        "name": model_id.title(),
                        "description": model_descriptions.get(model_id, "Local Model"),
                    }
                )

        return {
            "models": models,
            "default": (
                "gpt-4o-mini"
                if llm_service.use_openai
                else (ollama_models[0] if ollama_models else None)
            ),
        }
    except Exception as e:
        print(f"⚠️  Error getting available models: {e}")
        return {"models": {"openai": [], "ollama": []}, "default": None}


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


# PI Report Generation Endpoint
@app.post("/api/v1/insights/pi-report")
async def generate_pi_report(
    request: PIReportRequest,
    db: Session = Depends(get_db),
):
    """Generate comprehensive PI management report

    Creates a detailed report comparing performance vs targets,
    improvements from previous PI, and actionable proposals.
    Supports single or multiple PI analysis (e.g., full year).

    Args:
        request: PIReportRequest containing pis, compare_with_previous, model, temperature
        db: Database session
    """
    try:
        # Extract values from request (support both single PI and multiple PIs)
        pis = request.pis if request.pis else ([request.pi] if request.pi else [])
        if not pis:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one PI must be specified",
            )

        compare_with_previous = request.compare_with_previous
        model = request.model
        temperature = request.temperature

        # Update LLM config if provided
        if model:
            llm_service.model = model
        if temperature is not None:
            llm_service.temperature = temperature

        # Get metrics for all selected PIs
        all_pi_metrics = {}
        previous_metrics = {}

        is_multi_pi = len(pis) > 1

        if leadtime_service and leadtime_service.is_available():
            try:
                # Get all features once
                all_features = leadtime_service.client.get_flow_leadtime(limit=10000)
                all_pip_features = leadtime_service.client.get_pip_data(limit=10000)
                all_throughput = leadtime_service.client.get_throughput_data(
                    limit=10000
                )

                def calculate_pi_from_resolved_date(
                    resolved_date: str,
                ) -> Optional[str]:
                    """Calculate PI based on resolved date."""
                    if not resolved_date:
                        return None
                    try:
                        resolved_dt = datetime.strptime(resolved_date[:10], "%Y-%m-%d")
                        # Get PI configurations from database
                        config_entry = (
                            db.query(RuntimeConfiguration)
                            .filter(
                                RuntimeConfiguration.config_key == "pi_configurations"
                            )
                            .first()
                        )
                        if config_entry and config_entry.config_value:
                            import json

                            pi_configurations = json.loads(config_entry.config_value)
                            for pi_config in pi_configurations:
                                start_date = datetime.strptime(
                                    pi_config["start_date"], "%Y-%m-%d"
                                )
                                end_date = datetime.strptime(
                                    pi_config["end_date"], "%Y-%m-%d"
                                )
                                if start_date <= resolved_dt <= end_date:
                                    return pi_config.get("pi")
                        return None
                    except:
                        return None

                def calculate_pi_metrics(pi_name, features, pip_data, throughput_data):
                    """Calculate metrics for a single PI"""
                    metrics = {"pi_name": pi_name}

                    # Flow efficiency and lead time
                    # For Done features (throughput), use resolved date to determine PI
                    # For other statuses, use the stored pi field
                    pi_features = [
                        f
                        for f in features
                        if (
                            f.get("status") == "Done"
                            and calculate_pi_from_resolved_date(f.get("resolved_date"))
                            == pi_name
                        )
                        or (f.get("status") != "Done" and f.get("pi") == pi_name)
                    ]
                    if pi_features:
                        value_add_times = []
                        total_times = []
                        for f in pi_features:
                            value_add = f.get("in_progress", 0) + f.get(
                                "in_reviewing", 0
                            )
                            total = f.get("total_leadtime", 0)
                            if total > 0:
                                value_add_times.append(value_add)
                                total_times.append(total)

                        if value_add_times and total_times:
                            avg_value_add = sum(value_add_times) / len(value_add_times)
                            avg_total = sum(total_times) / len(total_times)
                            metrics["flow_efficiency"] = round(
                                (avg_value_add / avg_total) * 100, 1
                            )
                            metrics["avg_leadtime"] = round(avg_total, 1)

                    # Planning accuracy
                    pi_pip = [f for f in pip_data if f.get("pi") == pi_name]
                    if pi_pip:
                        planned = sum(
                            1 for f in pi_pip if f.get("planned_committed", 0) > 0
                        )
                        delivered = sum(
                            1
                            for f in pi_pip
                            if f.get("planned_committed", 0) > 0
                            and f.get("plc_delivery") not in ["", "0", None, "null"]
                        )
                        if planned > 0:
                            metrics["planning_accuracy"] = round(
                                (delivered / planned) * 100, 1
                            )

                    # Throughput
                    pi_throughput = [
                        f for f in throughput_data if f.get("pi") == pi_name
                    ]
                    metrics["throughput"] = len(pi_throughput)

                    return metrics

                # Calculate metrics for each selected PI
                for pi in pis:
                    all_pi_metrics[pi] = calculate_pi_metrics(
                        pi, all_features, all_pip_features, all_throughput
                    )

                # Get previous PI metrics for comparison (only if single PI or first PI)
                if compare_with_previous:
                    first_pi = pis[0]
                    year = first_pi[:2]
                    quarter = first_pi[2:]
                    prev_quarter = (
                        f"{year}Q{int(quarter[1]) - 1}"
                        if int(quarter[1]) > 1
                        else f"{int(year)-1}Q4"
                    )

                    previous_metrics = calculate_pi_metrics(
                        prev_quarter, all_features, all_pip_features, all_throughput
                    )

                    previous_metrics = calculate_pi_metrics(
                        prev_quarter, all_features, all_pip_features, all_throughput
                    )

            except Exception as e:
                print(f"⚠️  Could not fetch PI metrics: {e}")
                import traceback

                traceback.print_exc()

        # Get excluded feature statuses from database
        excluded_statuses = get_excluded_feature_statuses(db)

        # Get strategic targets from database
        targets = db.query(StrategicTarget).all()
        target_dict = {t.metric_name: t for t in targets}

        # Get PI Management Report system prompt from prompt service
        from services.prompt_service import prompt_service

        system_prompt_obj = prompt_service.get_prompt(
            "pi_management_report_system_prompt"
        )
        system_prompt = system_prompt_obj.get("prompt", "") if system_prompt_obj else ""

        # Build the data context for the report
        if is_multi_pi:
            # Multi-PI report (e.g., full year)
            pi_list = ", ".join(pis)
            excluded_status_note = (
                f"\n**Note:** Features with the following statuses are excluded from analysis: {', '.join(excluded_statuses)}"
                if excluded_statuses
                else ""
            )
            data_context = f"""
**Analysis Period:** {pi_list} ({len(pis)} Program Increments)
**Report Type:** Multi-PI Performance Analysis{excluded_status_note}

"""
            # Show metrics for each PI
            data_context += "**Performance by PI:**\n\n"
            for pi_name in pis:
                metrics = all_pi_metrics.get(pi_name, {})
                data_context += f"**{pi_name}:**\n"
                data_context += (
                    f"- Flow Efficiency: {metrics.get('flow_efficiency', 'N/A')}%\n"
                )
                data_context += (
                    f"- Average Lead-Time: {metrics.get('avg_leadtime', 'N/A')} days\n"
                )
                data_context += (
                    f"- Planning Accuracy: {metrics.get('planning_accuracy', 'N/A')}%\n"
                )
                data_context += (
                    f"- Features Delivered: {metrics.get('throughput', 'N/A')}\n\n"
                )

            # Calculate aggregate metrics
            all_flow_eff = [
                m.get("flow_efficiency")
                for m in all_pi_metrics.values()
                if m.get("flow_efficiency")
            ]
            all_leadtime = [
                m.get("avg_leadtime")
                for m in all_pi_metrics.values()
                if m.get("avg_leadtime")
            ]
            all_planning = [
                m.get("planning_accuracy")
                for m in all_pi_metrics.values()
                if m.get("planning_accuracy")
            ]
            total_throughput = sum(
                m.get("throughput", 0) for m in all_pi_metrics.values()
            )

            if all_flow_eff:
                data_context += f"\n**Aggregate Metrics ({pi_list}):**\n"
                data_context += f"- Average Flow Efficiency: {round(sum(all_flow_eff) / len(all_flow_eff), 1)}%\n"
                data_context += f"- Average Lead-Time: {round(sum(all_leadtime) / len(all_leadtime), 1)} days\n"
                data_context += f"- Average Planning Accuracy: {round(sum(all_planning) / len(all_planning), 1)}%\n"
                data_context += f"- Total Features Delivered: {total_throughput}\n"

            # Trend analysis
            if len(pis) > 1:
                first_pi_metrics = all_pi_metrics.get(pis[0], {})
                last_pi_metrics = all_pi_metrics.get(pis[-1], {})

                if first_pi_metrics and last_pi_metrics:
                    flow_trend = last_pi_metrics.get(
                        "flow_efficiency", 0
                    ) - first_pi_metrics.get("flow_efficiency", 0)
                    leadtime_trend = last_pi_metrics.get(
                        "avg_leadtime", 0
                    ) - first_pi_metrics.get("avg_leadtime", 0)
                    planning_trend = last_pi_metrics.get(
                        "planning_accuracy", 0
                    ) - first_pi_metrics.get("planning_accuracy", 0)

                    data_context += f"\n**Trend Analysis ({pis[0]} → {pis[-1]}):**\n"
                    data_context += f"- Flow Efficiency: {flow_trend:+.1f}% ({'improving' if flow_trend > 0 else 'declining'})\n"
                    data_context += f"- Lead-Time: {leadtime_trend:+.1f} days ({'improving' if leadtime_trend < 0 else 'worsening'})\n"
                    data_context += f"- Planning Accuracy: {planning_trend:+.1f}% ({'improving' if planning_trend > 0 else 'declining'})\n"

        else:
            # Single PI report
            pi = pis[0]
            current_metrics = all_pi_metrics.get(pi, {})
            excluded_status_note = (
                f"\n**Note:** Features with the following statuses are excluded from analysis: {', '.join(excluded_statuses)}"
                if excluded_statuses
                else ""
            )
            data_context = f"""
**PI Being Analyzed:** {pi}{excluded_status_note}

**Current PI Performance:**
- Flow Efficiency: {current_metrics.get('flow_efficiency', 'N/A')}%
- Average Lead-Time: {current_metrics.get('avg_leadtime', 'N/A')} days
- Planning Accuracy: {current_metrics.get('planning_accuracy', 'N/A')}%
- Features Delivered: {current_metrics.get('throughput', 'N/A')}
"""

            if compare_with_previous and previous_metrics:
                flow_change = current_metrics.get(
                    "flow_efficiency", 0
                ) - previous_metrics.get("flow_efficiency", 0)
                leadtime_change = current_metrics.get(
                    "avg_leadtime", 0
                ) - previous_metrics.get("avg_leadtime", 0)
                planning_change = current_metrics.get(
                    "planning_accuracy", 0
                ) - previous_metrics.get("planning_accuracy", 0)
                throughput_change = current_metrics.get(
                    "throughput", 0
                ) - previous_metrics.get("throughput", 0)

                data_context += f"""

**Previous PI ({previous_metrics.get('pi_name')}) Performance:**
- Flow Efficiency: {previous_metrics.get('flow_efficiency', 'N/A')}%
- Average Lead-Time: {previous_metrics.get('avg_leadtime', 'N/A')} days
- Planning Accuracy: {previous_metrics.get('planning_accuracy', 'N/A')}%
- Features Delivered: {previous_metrics.get('throughput', 'N/A')}

**Changes from Previous PI:**
- Flow Efficiency: {flow_change:+.1f}% ({'+improved' if flow_change > 0 else 'declined'})
- Average Lead-Time: {leadtime_change:+.1f} days ({'improved' if leadtime_change < 0 else 'increased'})
- Planning Accuracy: {planning_change:+.1f}% ({'+improved' if planning_change > 0 else 'declined'})
- Throughput: {throughput_change:+d} features ({'+increased' if throughput_change > 0 else 'decreased'})
"""

        # Add strategic targets
        if target_dict:
            data_context += "\n**Strategic Targets:**\n"
            for metric_name, target in target_dict.items():
                data_context += f"- {metric_name}: 2026 target = {target.target_2026}, 2027 target = {target.target_2027}, True North = {target.true_north}\n"

        # Get RAG context
        rag_context = ""
        try:
            from services.rag_service import rag_service

            if rag_service:
                rag_docs = rag_service.query(
                    f"PI performance analysis, metrics improvement, agile coaching recommendations for {pi}",
                    n_results=3,  # Reduced from 5 to 3 to limit prompt size
                )
                if rag_docs and len(rag_docs) > 0:
                    rag_context = "\n\n**Knowledge Base Context:**\n"
                    for i, doc in enumerate(
                        rag_docs[:2], 1
                    ):  # Only use top 2 most relevant docs
                        # Truncate long documents to prevent prompt overflow
                        text = doc.get("text", "")
                        if len(text) > 500:
                            text = text[:500] + "... (truncated)"
                        rag_context += f"\n{i}. {text}\n"
        except Exception as e:
            print(f"⚠️  Could not retrieve RAG context: {e}")

        # Combine system prompt with data context
        pi_query = ", ".join(pis) if is_multi_pi else pis[0]
        full_prompt = f"""{system_prompt}

---

DATA CONTEXT

{data_context}
{rag_context}

---

Please generate a comprehensive {"Multi-PI" if is_multi_pi else "PI"} Management Report based on the data context provided above. 
{"This report covers multiple Program Increments and should provide year-over-year or period analysis with trends and patterns." if is_multi_pi else ""}
Follow the structure and guidelines specified in your role instructions.
Use clear markdown formatting with headers (##, ###), bullet points, and **bold** text for emphasis.
"""

        # Generate report with LLM
        print(
            f"📊 Generating {'Multi-' if is_multi_pi else ''}PI Report for {pi_query} using prompt: {system_prompt_obj.get('name', 'N/A') if system_prompt_obj else 'fallback'}..."
        )
        print(
            f"📏 Prompt size: {len(full_prompt)} characters (~{len(full_prompt.split())} words)"
        )
        print(
            f"🤖 Using model: {llm_service.model} (temperature: {llm_service.temperature})"
        )

        # Add recommendation for large reports
        if is_multi_pi and len(pis) > 2:
            print(
                f"💡 Tip: For multi-PI reports with {len(pis)} PIs, consider using gpt-4o-mini for faster generation"
            )

        report_content = llm_service.generate_completion(
            full_prompt, max_tokens=4000, retry_count=2
        )

        # Check if report generation failed due to timeout
        if report_content.startswith("Error:"):
            print("⚠️  Report generation encountered an issue")
            # If using a slower model and got timeout, suggest faster model
            if (
                "timeout" in report_content.lower()
                and "gpt-4" in llm_service.model.lower()
                and "mini" not in llm_service.model.lower()
            ):
                report_content += "\n\n**Recommendation**: The model you're using (GPT-4) is very thorough but slower. Try using 'gpt-4o-mini' for faster results while maintaining quality."
        else:
            print(f"✅ PI Report generated ({len(report_content)} chars)")

        # Prepare response
        response_data = {
            "pis": pis,
            "report_content": report_content,
            "all_pi_metrics": all_pi_metrics if is_multi_pi else None,
            "current_metrics": all_pi_metrics.get(pis[0]) if not is_multi_pi else None,
            "previous_metrics": previous_metrics if compare_with_previous else None,
            "generated_at": datetime.now().isoformat(),
        }

        # Add backward compatibility for single PI
        if not is_multi_pi:
            response_data["pi"] = pis[0]

        return response_data

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"❌ PI Report generation error: {str(e)}")
        print(f"Full traceback:\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PI report: {str(e)}",
        )


# Insights Generation Endpoint
@app.post("/api/v1/insights/generate")
async def generate_insights_endpoint(
    scope: str = "portfolio",
    pis: Optional[str] = None,
    art: Optional[str] = None,  # Singular ART for scope selection
    arts: Optional[str] = None,  # Plural ARTs for filtering
    team: Optional[str] = None,  # Team name for team scope
    analysis_level: Optional[str] = None,  # 'feature' or 'story' for team view
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    enhance_with_llm: bool = False,
    use_agent_graph: bool = True,  # Enable agent graph by default for Little's Law insights
    db: Session = Depends(get_db),
):
    """Generate AI-powered insights using expert analysis (LLM)

    This is a separate endpoint to allow on-demand insight generation
    without slowing down the initial dashboard load.

    Args:
        scope: Scope of analysis (portfolio, art, team)
        pis: Comma-separated list of PIs
        art: Single ART for scope-specific analysis
        arts: Comma-separated list of ARTs for filtering
        team: Team name for team scope
        analysis_level: 'feature' or 'story' for team view
        model: LLM model to use (e.g., gpt-4o, gpt-4o-mini)
        temperature: LLM temperature (0.0-2.0)
        use_agent_graph: Use full agent graph workflow (includes Little's Law analysis)
    """
    try:
        # Parse filter parameters
        selected_pis = (
            [pi.strip() for pi in pis.split(",") if pi.strip()] if pis else []
        )
        selected_arts = (
            [art.strip() for art in arts.split(",") if art.strip()] if arts else []
        )

        # Get excluded feature statuses from database
        excluded_statuses = get_excluded_feature_statuses(db)

        # Use agent graph workflow for comprehensive analysis (includes Little's Law)
        # NOTE: Agent graph requires Jira data, so disabled for now with DL Webb App API
        if False and use_agent_graph and scope in ["portfolio", "pi", "art"]:
            print(f"🤖 Using agent graph workflow for {scope} scope")
            from agents.graph import run_evaluation_coach

            # Update LLM service with custom parameters if provided
            if enhance_with_llm:
                if model:
                    llm_service.model = model
                if temperature is not None:
                    llm_service.temperature = temperature
                print(
                    f"🤖 Using LLM: model={llm_service.model}, temperature={llm_service.temperature}"
                )

                # Inject LLM service into Little's Law analyzer for RAG enhancement
                from agents.nodes.littles_law_analyzer import set_llm_service

                set_llm_service(llm_service)
                print("✅ LLM service injected into Little's Law analyzer")
            else:
                print("⚠️  Running without LLM enhancement (RAG disabled)")

            # Run the agent graph workflow
            # For now, use a default time window (last 90 days)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=90)

            # Map scope to scope_type and scope_name
            scope_type = (
                "Portfolio"
                if scope == "portfolio"
                else "PI" if scope == "pi" else "ART"
            )
            scope_name = "Portfolio Analysis"
            scope_id_for_agent = (
                None  # Will be used to pass PI to Little's Law analyzer
            )

            if scope == "art" and art:
                scope_type = "ART"
                scope_name = art
            elif selected_arts and len(selected_arts) == 1:
                scope_type = "ART"
                scope_name = selected_arts[0]
            elif selected_pis:
                scope_type = "PI"
                scope_name = (
                    selected_pis[0] if len(selected_pis) == 1 else "Multiple PIs"
                )
                scope_id_for_agent = selected_pis[0]  # Pass first PI to analyzer

            # Pass PI even for ART scope if PI is selected
            if selected_pis and not scope_id_for_agent:
                scope_id_for_agent = selected_pis[0]

            if scope_id_for_agent:
                print(
                    f"📌 Scope ID set to: {scope_id_for_agent} for Little's Law analysis"
                )

            final_state = run_evaluation_coach(
                scope=scope_name,
                scope_type=scope_type,
                time_window_start=start_time,
                time_window_end=end_time,
                scope_id=scope_id_for_agent,
            )

            # Extract insights from final state
            insights = final_state.get("insights", [])

            # Convert to API response format if needed
            insight_responses = []
            for insight in insights:
                if isinstance(insight, InsightResponse):
                    insight_responses.append(insight)
                elif isinstance(insight, dict):
                    # Already in dict format
                    insight_responses.append(InsightResponse(**insight))

            print(
                f"✅ Generated {len(insight_responses)} insights via agent graph (includes Little's Law)"
            )

            return {
                "status": "success",
                "insights": [insight.dict() for insight in insight_responses],
                "count": len(insight_responses),
                "excluded_statuses": excluded_statuses,
                "filter_info": {
                    "excluded_statuses": excluded_statuses,
                    "selected_pis": selected_pis,
                    "selected_arts": selected_arts,
                },
            }

        # Fall back to direct insights generation (with Little's Law if requested)
        print(
            f"🤖 Using direct insights generation{' + Little\'s Law' if use_agent_graph and selected_pis else ''}"
        )
        from agents.nodes.advanced_insights import generate_advanced_insights

        llm_service_for_insights = llm_service if enhance_with_llm else None

        # Update LLM service with custom parameters if provided
        if enhance_with_llm:
            if model:
                llm_service.model = model
            if temperature is not None:
                llm_service.temperature = temperature

            print(
                f"🤖 Using LLM: model={llm_service.model}, temperature={llm_service.temperature}"
            )
        else:
            print("🤖 Generating insights without LLM enhancement")

        # Get excluded feature statuses from database
        excluded_statuses = get_excluded_feature_statuses(db)

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

                # Add team filter if in team scope
                if scope == "team" and team:
                    params["team"] = team
                    print(f"📊 Filtering insights for team: {team}")

                # Determine which data source to use based on analysis level
                use_story_level = analysis_level == "story"
                data_source_name = "user stories" if use_story_level else "features"

                # Add appropriate threshold from settings (story vs feature)
                if use_story_level:
                    params["threshold_days"] = settings.story_bottleneck_threshold_days
                else:
                    params["threshold_days"] = settings.bottleneck_threshold_days

                # Generate insights based on analysis level
                if use_story_level:
                    print(f"📊 Generating story-level insights for {data_source_name}")

                    try:
                        # Import story insights generator
                        from agents.nodes.story_insights import generate_story_insights

                        # Get story-level analysis data
                        print(f"📡 Fetching story analysis summary from DL Webb App...")
                        story_analysis_summary = (
                            leadtime_service.client.get_story_analysis_summary(**params)
                        )
                        print(f"✅ Received story analysis summary")

                        # Get story planning data if PI is selected
                        story_pip_data = []
                        if selected_pis:
                            pip_params = {}
                            pip_params["pi"] = selected_pis[0]
                            if selected_arts:
                                pip_params["art"] = selected_arts[0]
                            if scope == "team" and team:
                                pip_params["team"] = team

                            try:
                                print(f"📡 Fetching story planning data...")
                                story_pip_data = (
                                    leadtime_service.client.get_story_pip_data(
                                        **pip_params
                                    )
                                )
                                print(
                                    f"✅ Received story planning data: {len(story_pip_data) if isinstance(story_pip_data, list) else 0} records"
                                )
                            except Exception as e:
                                print(f"⚠️  Could not fetch story PIP data: {e}")

                        # Get story waste analysis
                        print(f"📡 Fetching story waste analysis...")
                        story_waste_analysis = (
                            leadtime_service.client.get_story_waste_analysis(**params)
                        )
                        print(f"✅ Received story waste analysis")

                        # Generate story-level insights
                        print(f"🤖 Generating story-level insights...")

                        # Debug: Check data structure
                        print(
                            f"📋 story_analysis_summary keys: {list(story_analysis_summary.keys())}"
                        )
                        if "bottleneck_analysis" in story_analysis_summary:
                            bottleneck = story_analysis_summary["bottleneck_analysis"]
                            print(
                                f"📋 bottleneck_analysis keys: {list(bottleneck.keys())}"
                            )
                            if "stage_analysis" in bottleneck:
                                stage_count = len(bottleneck["stage_analysis"])
                                print(
                                    f"📋 stage_analysis stages: {list(bottleneck['stage_analysis'].keys())} (count: {stage_count})"
                                )
                                if stage_count == 0:
                                    print(
                                        f"⚠️  stage_analysis is EMPTY - no stage-level metrics available"
                                    )
                            else:
                                print(f"⚠️  No 'stage_analysis' in bottleneck_analysis")

                            # Check other data sources
                            stuck_items = bottleneck.get("stuck_items", [])
                            print(f"📋 stuck_items count: {len(stuck_items)}")
                            if stuck_items:
                                print(f"   Sample stuck item: {stuck_items[0]}")

                            wip_stats = bottleneck.get("wip_statistics", {})
                            print(
                                f"📋 wip_statistics keys: {list(wip_stats.keys()) if wip_stats else 'None'}"
                            )

                            flow_dist = bottleneck.get("flow_distribution", {})
                            print(
                                f"📋 flow_distribution keys: {list(flow_dist.keys()) if flow_dist else 'None'}"
                            )
                        else:
                            print(
                                f"⚠️  No 'bottleneck_analysis' in story_analysis_summary"
                            )

                        print(
                            f"📋 story_pip_data count: {len(story_pip_data) if isinstance(story_pip_data, list) else 0}"
                        )
                        print(
                            f"📋 story_waste_analysis keys: {list(story_waste_analysis.keys()) if story_waste_analysis else 'None'}"
                        )

                        insights = generate_story_insights(
                            story_analysis_summary=story_analysis_summary,
                            story_pip_data=story_pip_data,
                            story_waste_analysis=story_waste_analysis,
                            selected_arts=selected_arts,
                            selected_pis=selected_pis,
                            selected_team=team,
                            llm_service=llm_service_for_insights,
                        )
                        print(f"✅ Generated {len(insights)} story-level insights")

                    except Exception as story_error:
                        print(f"❌ Story-level insights failed: {story_error}")
                        print(
                            f"   This likely means the DL Webb App story endpoints are not available"
                        )
                        print(
                            f"   or the story data doesn't exist for the selected filters"
                        )

                        # Create an informational insight about the issue
                        insights = [
                            InsightResponse(
                                id=0,
                                title="Story-Level Insights Not Available",
                                severity="info",
                                confidence=1.0,
                                scope=f"Team: {team}" if team else "Story Level",
                                scope_id=None,
                                observation=f"Story-level insight analysis is not currently available. Error: {str(story_error)[:200]}",
                                interpretation="The DL Webb App backend may not have the story-level API endpoints implemented yet, or there may be no story data for the selected filters (PI: {}, ART: {}, Team: {}).".format(
                                    ", ".join(selected_pis) if selected_pis else "None",
                                    (
                                        ", ".join(selected_arts)
                                        if selected_arts
                                        else "None"
                                    ),
                                    team if team else "None",
                                ),
                                root_causes=[
                                    RootCause(
                                        description="Story-level API endpoints not available in DL Webb App",
                                        evidence=[
                                            f"API Error: {str(story_error)[:100]}",
                                            "Required endpoints: /api/story_analysis_summary, /api/story_pip_data, /api/story_waste_analysis",
                                        ],
                                        confidence=0.9,
                                        reference="DL Webb App API",
                                    )
                                ],
                                recommended_actions=[
                                    Action(
                                        timeframe="immediate",
                                        description="Verify DL Webb App has story-level endpoints implemented (see CHANGELOG_STORY_API.md)",
                                        owner="system_admin",
                                        effort="Check backend logs",
                                        dependencies=["DL Webb App backend access"],
                                        success_signal="Story endpoints return 200 OK",
                                    ),
                                    Action(
                                        timeframe="immediate",
                                        description="Verify story data exists in database for selected PI/Team/ART filters",
                                        owner="system_admin",
                                        effort="Query database",
                                        dependencies=["Database access"],
                                        success_signal="Story records found in story_flow_leadtime table",
                                    ),
                                    Action(
                                        timeframe="short_term",
                                        description="Switch to Feature-Level analysis as a workaround until story endpoints are available",
                                        owner="user",
                                        effort="Change dropdown",
                                        dependencies=[],
                                        success_signal="Feature-level insights displayed",
                                    ),
                                ],
                                expected_outcomes=ExpectedOutcome(
                                    metrics_to_watch=[
                                        "API availability",
                                        "Data completeness",
                                    ],
                                    leading_indicators=[
                                        "Endpoint health checks passing"
                                    ],
                                    lagging_indicators=[
                                        "Story insights generating successfully"
                                    ],
                                    timeline="1-2 days",
                                    risks=["May need DL Webb App backend update"],
                                ),
                                metric_references=[],
                                evidence=[
                                    f"Error type: {type(story_error).__name__}",
                                    f"Error message: {str(story_error)[:200]}",
                                ],
                                status="active",
                                created_at=datetime.utcnow(),
                            )
                        ]
                else:
                    print(
                        f"📊 Generating feature-level insights for {data_source_name}"
                    )

                    # Get feature-level analysis summary
                    analysis_summary = leadtime_service.client.get_analysis_summary(
                        **params
                    )

                    # Also get ART comparison for context, filtered by selected ARTs and PI
                    pip_params = {}
                    if selected_pis:
                        pip_params["pi"] = selected_pis[0]  # Filter by PI
                    if selected_arts:
                        pip_params["art"] = selected_arts[
                            0
                        ]  # Get pip_data for first selected ART

                    # Add team filter for team scope
                    if scope == "team" and team:
                        pip_params["team"] = team

                    pip_data = leadtime_service.client.get_pip_data(**pip_params)

                    if pip_data:
                        art_comparison = [
                            {
                                "art_name": art.get("art_name", "Unknown"),
                                "flow_efficiency": float(
                                    art.get("flow_efficiency_percent", 0)
                                ),
                                "planning_accuracy": float(
                                    art.get("pi_predictability", 0)
                                ),
                                "quality_score": float(art.get("quality_score", 0)),
                                "status": (
                                    "healthy"
                                    if float(art.get("flow_efficiency_percent", 0))
                                    >= 70
                                    else "warning"
                                ),
                            }
                            for art in pip_data
                        ]

                    # Generate feature-level insights with LLM
                    insights = generate_advanced_insights(
                        analysis_summary=analysis_summary,
                        art_comparison=art_comparison,
                        selected_arts=selected_arts,
                        selected_pis=selected_pis,
                        selected_team=team,
                        llm_service=llm_service_for_insights,
                    )

                print(f"✅ Generated {len(insights)} AI-powered insights")

                # Add Little's Law analysis if requested with agent graph
                if use_agent_graph and selected_pis:
                    print(f"🔬 Adding Little's Law analysis for PI: {selected_pis[0]}")
                    try:
                        from agents.nodes.littles_law_analyzer import (
                            littles_law_analyzer_node,
                        )
                        from agents.nodes.littles_law_analyzer import (
                            set_llm_service as set_ll_llm,
                        )

                        # Configure LLM for Little's Law analyzer
                        if llm_service_for_insights:
                            set_ll_llm(llm_service_for_insights)

                        # Create a minimal state for Little's Law analyzer
                        ll_state = {
                            "scope_id": selected_pis[0],
                            "scope_type": (
                                "Team"
                                if scope == "team"
                                else ("ART" if scope == "art" else "Portfolio")
                            ),
                            "scope": (
                                team
                                if team
                                else (
                                    art
                                    if art
                                    else (
                                        selected_arts[0]
                                        if selected_arts
                                        else "Portfolio"
                                    )
                                )
                            ),
                            "selected_art": (
                                art
                                if art
                                else (selected_arts[0] if selected_arts else None)
                            ),
                            "selected_team": team if team else None,
                            "analysis_level": analysis_level,  # Pass analysis level (story vs feature)
                        }

                        # Run Little's Law analyzer
                        ll_result = littles_law_analyzer_node(ll_state)

                        # Extract Little's Law insights
                        ll_insights = ll_result.get("littles_law_insights", [])

                        if ll_insights:
                            print(
                                f"✅ Generated {len(ll_insights)} Little's Law insights"
                            )
                            # Convert to InsightResponse and add required fields
                            import uuid

                            for ll_insight in ll_insights:
                                if isinstance(ll_insight, dict):
                                    # Add required fields
                                    ll_insight["id"] = abs(
                                        hash(ll_insight.get("title", str(uuid.uuid4())))
                                    ) % (10**8)
                                    ll_insight["status"] = "new"
                                    ll_insight["created_at"] = datetime.utcnow()
                                    insights.append(InsightResponse(**ll_insight))
                                else:
                                    insights.append(ll_insight)
                        else:
                            print("⚠️ No Little's Law insights generated")

                    except Exception as ll_error:
                        print(f"⚠️ Little's Law analysis failed: {ll_error}")
                        import traceback

                        traceback.print_exc()

                return {
                    "status": "success",
                    "insights": [insight.dict() for insight in insights],
                    "count": len(insights),
                    "excluded_statuses": excluded_statuses,
                    "filter_info": {
                        "excluded_statuses": excluded_statuses,
                        "selected_pis": selected_pis,
                        "selected_arts": selected_arts,
                        "selected_team": team,
                        "analysis_level": analysis_level,
                    },
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


# Export Executive Summary to Excel
@app.get("/api/v1/insights/export-summary")
async def export_executive_summary(
    pis: Optional[str] = None,
    arts: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Export executive summary data (stuck items, bottlenecks, WIP) to Excel file"""
    try:
        import pandas as pd
        from io import BytesIO
        from fastapi.responses import StreamingResponse

        # Get excluded feature statuses from database
        excluded_statuses = get_excluded_feature_statuses(db)
        print(f"🔍 Excel Export: Excluding feature statuses: {excluded_statuses}")

        # Parse filter parameters
        selected_pis = (
            [pi.strip() for pi in pis.split(",") if pi.strip()] if pis else []
        )
        selected_arts = (
            [art.strip() for art in arts.split(",") if art.strip()] if arts else []
        )

        if leadtime_service and leadtime_service.is_available():
            try:
                params = {}
                if selected_arts:
                    params["arts"] = selected_arts
                if selected_pis:
                    params["pis"] = selected_pis
                params["threshold_days"] = settings.bottleneck_threshold_days

                # Get analysis summary
                analysis_summary = leadtime_service.client.get_analysis_summary(
                    **params
                )

                bottleneck_data = analysis_summary.get("bottleneck_analysis", {})
                wip_stats = bottleneck_data.get("wip_statistics", {})
                stuck_items_from_api = bottleneck_data.get("stuck_items", [])

                # ============================================================
                # ENHANCEMENT: Get ALL features and calculate stuck items for all ARTs
                # The API stuck_items may be limited to certain ARTs, so we calculate our own
                # ============================================================
                threshold_days = settings.bottleneck_threshold_days

                # Get flow_leadtime data for all requested ARTs
                flow_params = {"limit": 50000}
                # Note: We'll filter by ART/PI client-side since the server may have issues with multiple ARTs
                flow_data = leadtime_service.client.get_flow_leadtime(**flow_params)

                # Filter by selected ARTs and PIs
                if selected_arts:
                    flow_data = [f for f in flow_data if f.get("art") in selected_arts]
                if selected_pis:
                    # Helper to calculate PI from resolved date
                    def get_feature_pi(feature):
                        if feature.get("status") == "Done" and feature.get(
                            "resolved_date"
                        ):
                            # For Done features, calculate PI from resolved date
                            try:
                                resolved_dt = datetime.strptime(
                                    feature["resolved_date"][:10], "%Y-%m-%d"
                                )
                                config_entry = (
                                    db.query(RuntimeConfiguration)
                                    .filter(
                                        RuntimeConfiguration.config_key
                                        == "pi_configurations"
                                    )
                                    .first()
                                )
                                if config_entry and config_entry.config_value:
                                    import json

                                    pi_configurations = json.loads(
                                        config_entry.config_value
                                    )
                                    for pi_config in pi_configurations:
                                        start_date = datetime.strptime(
                                            pi_config["start_date"], "%Y-%m-%d"
                                        )
                                        end_date = datetime.strptime(
                                            pi_config["end_date"], "%Y-%m-%d"
                                        )
                                        if start_date <= resolved_dt <= end_date:
                                            return pi_config.get("pi")
                            except:
                                pass
                        # For non-Done features, use stored pi field
                        return feature.get("pi")

                    flow_data = [
                        f for f in flow_data if get_feature_pi(f) in selected_pis
                    ]

                # Filter by excluded statuses
                if excluded_statuses:
                    original_count = len(flow_data)
                    flow_data = [
                        f for f in flow_data if f.get("status") not in excluded_statuses
                    ]
                    filtered_count = original_count - len(flow_data)
                    print(
                        f"🔍 Excel Export: Filtered {filtered_count} features with excluded statuses (showing {len(flow_data)})"
                    )

                # Calculate stuck items from flow_leadtime data
                # A feature is "stuck" if it's currently in a stage for longer than threshold
                stage_columns = [
                    "in_backlog",
                    "in_planned",
                    "in_analysis",
                    "in_progress",
                    "in_reviewing",
                    "in_sit",
                    "ready_for_uat",
                    "in_uat",
                    "ready_for_deployment",
                ]

                stuck_items = []
                seen_issue_keys = set()  # Track seen issue keys to prevent duplicates

                for feature in flow_data:
                    issue_key = feature.get("issue_key", "Unknown")

                    # Skip if we've already processed this issue
                    if issue_key in seen_issue_keys:
                        continue

                    # Only check non-completed features (case-insensitive check)
                    status = feature.get("status", "").upper()
                    if status in ["DONE", "CLOSED", "RESOLVED"]:
                        continue

                    # Find the current stage (last stage with time > 0)
                    current_stage = None
                    current_stage_days = 0

                    for stage in stage_columns:
                        stage_time = feature.get(stage, 0) or 0
                        if stage_time > 0:
                            current_stage = stage
                            current_stage_days = stage_time

                    # If stuck longer than threshold, add to stuck items
                    if current_stage and current_stage_days > threshold_days:
                        seen_issue_keys.add(issue_key)  # Mark as processed

                        # Determine insight category based on days stuck
                        insight_category = "Stuck Item"
                        if current_stage_days > 100:
                            insight_category = "Critical - Severely Stuck"
                        elif current_stage_days > 60:
                            insight_category = "Warning - Long Duration"

                        stuck_items.append(
                            {
                                "issue_key": issue_key,
                                "insight_category": insight_category,
                                "art": feature.get("art", "Unknown"),
                                "team": feature.get("development_team", "Unknown"),
                                "current_stage": current_stage,
                                "days_in_stage": round(current_stage_days, 1),
                                "summary": feature.get("summary", ""),
                                "status": feature.get("status", "Unknown"),
                                "pi": feature.get("pi", "Unknown"),
                                "total_leadtime": feature.get("total_leadtime", 0),
                            }
                        )

                # Sort by days in stage descending
                stuck_items.sort(key=lambda x: x.get("days_in_stage", 0), reverse=True)

                # Log what we found
                arts_in_stuck = set(item.get("art") for item in stuck_items)
                print(
                    f"📊 Excel Export: Found {len(stuck_items)} stuck items across {len(arts_in_stuck)} ARTs: {arts_in_stuck}"
                )

                # Create Excel workbook with multiple sheets
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    # Sheet 1: Stuck Items (ALL items, sorted by days in stage)
                    if stuck_items:
                        stuck_df = pd.DataFrame(stuck_items)
                        # Reorder columns for better readability
                        column_order = [
                            "issue_key",
                            "insight_category",
                            "art",
                            "team",
                            "current_stage",
                            "days_in_stage",
                            "summary",
                            "status",
                            "pi",
                            "total_leadtime",
                        ]
                        # Only include columns that exist
                        column_order = [
                            col for col in column_order if col in stuck_df.columns
                        ]
                        stuck_df = stuck_df[column_order]
                        stuck_df.to_excel(writer, sheet_name="Stuck Items", index=False)
                    else:
                        # Create empty sheet with headers
                        empty_df = pd.DataFrame(
                            columns=[
                                "issue_key",
                                "insight_category",
                                "art",
                                "team",
                                "current_stage",
                                "days_in_stage",
                                "summary",
                                "status",
                                "pi",
                            ]
                        )
                        empty_df.to_excel(writer, sheet_name="Stuck Items", index=False)

                    # Sheet 2: Bottleneck Analysis (ALL stages with scores)
                    bottleneck_list = []
                    for stage, metrics in wip_stats.items():
                        if isinstance(metrics, dict):
                            mean_time = metrics.get("mean", 0)
                            count = metrics.get("count", 0)
                            exceeding = metrics.get("exceeding_threshold", 0)
                            if mean_time > 0 and count > 0:
                                score = (
                                    (mean_time / 10) + (exceeding / count * 100)
                                    if count > 0
                                    else 0
                                )
                                bottleneck_list.append(
                                    {
                                        "Stage": stage.replace("_", " ").title(),
                                        "Bottleneck Score": round(score, 1),
                                        "Mean Time (days)": round(mean_time, 1),
                                        "Total Items": count,
                                        "Items Exceeding Threshold": exceeding,
                                        "Exceeding %": round(
                                            (
                                                (exceeding / count * 100)
                                                if count > 0
                                                else 0
                                            ),
                                            1,
                                        ),
                                    }
                                )

                    if bottleneck_list:
                        bottleneck_df = pd.DataFrame(bottleneck_list)
                        bottleneck_df = bottleneck_df.sort_values(
                            "Bottleneck Score", ascending=False
                        )
                        bottleneck_df.to_excel(
                            writer, sheet_name="Bottleneck Analysis", index=False
                        )

                    # Sheet 3: WIP Statistics (ALL stages with high WIP)
                    wip_list = []
                    for stage, metrics in wip_stats.items():
                        if isinstance(metrics, dict):
                            count = metrics.get("count", 0)
                            mean_time = metrics.get("mean", 0)
                            exceeding = metrics.get("exceeding_threshold", 0)
                            if count > 0:
                                wip_list.append(
                                    {
                                        "Stage": stage.replace("_", " ").title(),
                                        "Total Items (WIP)": count,
                                        "Mean Time (days)": round(mean_time, 1),
                                        "Items Exceeding Threshold": exceeding,
                                        "Exceeding %": round(
                                            (
                                                (exceeding / count * 100)
                                                if count > 0
                                                else 0
                                            ),
                                            1,
                                        ),
                                    }
                                )

                    if wip_list:
                        wip_df = pd.DataFrame(wip_list)
                        wip_df = wip_df.sort_values(
                            "Total Items (WIP)", ascending=False
                        )
                        wip_df.to_excel(
                            writer, sheet_name="WIP Statistics", index=False
                        )

                    # Sheet 4: Summary Statistics
                    summary_stats = {
                        "Metric": [
                            "Total Stuck Items",
                            "Total Workflow Stages",
                            "Stages with High WIP (>1000)",
                            "Highest Bottleneck Score",
                            "Analysis Scope - ARTs",
                            "Analysis Scope - PIs",
                        ],
                        "Value": [
                            len(stuck_items),
                            len(wip_stats),
                            (
                                len(
                                    [
                                        w
                                        for w in wip_list
                                        if w["Total Items (WIP)"] > 1000
                                    ]
                                )
                                if wip_list
                                else 0
                            ),
                            (
                                max([b["Bottleneck Score"] for b in bottleneck_list])
                                if bottleneck_list
                                else 0
                            ),
                            ", ".join(selected_arts) if selected_arts else "All ARTs",
                            ", ".join(selected_pis) if selected_pis else "All PIs",
                        ],
                    }
                    summary_df = pd.DataFrame(summary_stats)
                    summary_df.to_excel(writer, sheet_name="Summary", index=False)

                output.seek(0)

                # Generate filename with timestamp and filters
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                art_filter = (
                    f"_{selected_arts[0]}" if len(selected_arts) == 1 else "_MultiART"
                )
                pi_filter = (
                    f"_{selected_pis[0]}" if len(selected_pis) == 1 else "_MultiPI"
                )
                filename = f"executive_summary{art_filter}{pi_filter}_{timestamp}.xlsx"

                return StreamingResponse(
                    output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )

            except Exception as e:
                print(f"❌ Error exporting executive summary: {e}")
                import traceback

                traceback.print_exc()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to export executive summary: {str(e)}",
                )
        else:
            raise HTTPException(
                status_code=503, detail="Lead-time service not available"
            )
    except Exception as e:
        print(f"❌ Error in export summary endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export Individual Insight to Excel with all related features/stories
@app.post("/api/v1/insights/export")
async def export_insight_to_excel(
    insight_data: Dict[str, Any],
    pis: Optional[str] = None,
    arts: Optional[str] = None,
    team: Optional[str] = None,
    analysis_level: str = "feature",
    db: Session = Depends(get_db),
):
    """
    Export a single insight to Excel with all related features/stories

    Args:
        insight_data: The complete insight object from frontend
        pis: Comma-separated list of PIs
        arts: Comma-separated list of ARTs
        team: Team name filter
        analysis_level: 'feature' or 'story'
    """
    try:
        import pandas as pd
        from io import BytesIO
        from fastapi.responses import StreamingResponse
        import re

        print(f"📊 Exporting insight to Excel: {insight_data.get('title', 'Unknown')}")

        # Parse filter parameters
        selected_pis = (
            [pi.strip() for pi in pis.split(",") if pi.strip()] if pis else []
        )
        selected_arts = (
            [art.strip() for art in arts.split(",") if art.strip()] if arts else []
        )

        # Extract all issue keys mentioned in the insight
        issue_keys = set()

        # Extract from evidence
        evidence_list = insight_data.get("evidence", [])
        for evidence in evidence_list:
            # Match patterns like "UCART-2228", "ACET-1234", etc.
            matches = re.findall(r"[A-Z][A-Z0-9]+-\d+", str(evidence))
            issue_keys.update(matches)

        # Extract from root causes
        root_causes = insight_data.get("root_causes", [])
        for rc in root_causes:
            rc_evidence = rc.get("evidence", [])
            for evidence in rc_evidence:
                matches = re.findall(r"[A-Z][A-Z0-9]+-\d+", str(evidence))
                issue_keys.update(matches)

        print(f"📋 Found {len(issue_keys)} unique issue keys in insight")

        if leadtime_service and leadtime_service.is_available():
            try:
                params = {}
                if selected_arts:
                    params["arts"] = selected_arts
                if selected_pis:
                    params["pis"] = selected_pis
                if team:
                    params["team"] = team
                params["threshold_days"] = settings.bottleneck_threshold_days

                # Get analysis summary based on level
                if analysis_level == "story" and team:
                    # Story-level analysis
                    analysis_summary = (
                        leadtime_service.client.get_story_analysis_summary(**params)
                    )
                else:
                    # Feature-level analysis
                    analysis_summary = leadtime_service.client.get_analysis_summary(
                        **params
                    )

                bottleneck_data = analysis_summary.get("bottleneck_analysis", {})
                stuck_items = bottleneck_data.get("stuck_items", [])

                # Get flow/leadtime data to find additional items
                flow_data = []
                if analysis_level == "story" and team:
                    flow_params = {"limit": 50000}
                    if selected_arts:
                        flow_params["arts"] = selected_arts
                    if selected_pis:
                        flow_params["pis"] = selected_pis
                    if team:
                        flow_params["team"] = team
                    flow_data = leadtime_service.client.get_story_flow_leadtime(
                        **flow_params
                    )
                else:
                    flow_params = {"limit": 50000}
                    if selected_arts:
                        flow_params["arts"] = selected_arts
                    if selected_pis:
                        flow_params["pis"] = selected_pis
                    flow_data = leadtime_service.client.get_flow_leadtime(**flow_params)

                # Filter items that match the issue keys from the insight
                related_items = []

                # Add stuck items that match
                for item in stuck_items:
                    if item.get("issue_key") in issue_keys:
                        related_items.append(
                            {
                                "issue_key": item.get("issue_key"),
                                "category": "Stuck Item",
                                "art": item.get("art"),
                                "team": item.get("team"),
                                "current_stage": item.get("stage", ""),
                                "days_in_stage": item.get("days_in_stage", 0),
                                "summary": item.get("summary", ""),
                                "status": item.get("status", ""),
                                "pi": item.get("pi", ""),
                                "total_leadtime": item.get("age", 0),
                            }
                        )

                # Add flow data items that match
                for item in flow_data:
                    issue_key = item.get("issue_key")
                    if issue_key in issue_keys and not any(
                        ri["issue_key"] == issue_key for ri in related_items
                    ):
                        related_items.append(
                            {
                                "issue_key": issue_key,
                                "category": "Flow Item",
                                "art": item.get("art"),
                                "team": item.get(
                                    "development_team", item.get("team", "")
                                ),
                                "current_stage": item.get("current_status", ""),
                                "days_in_stage": 0,
                                "summary": item.get("summary", ""),
                                "status": item.get(
                                    "final_status", item.get("current_status", "")
                                ),
                                "pi": item.get("pi", ""),
                                "total_leadtime": item.get(
                                    "leadtime_days", item.get("age_days", 0)
                                ),
                            }
                        )

                # If we still don't have all items, add placeholders for missing ones
                for issue_key in issue_keys:
                    if not any(ri["issue_key"] == issue_key for ri in related_items):
                        related_items.append(
                            {
                                "issue_key": issue_key,
                                "category": "Mentioned in Insight",
                                "art": selected_arts[0] if selected_arts else "",
                                "team": team or "",
                                "current_stage": "",
                                "days_in_stage": 0,
                                "summary": "",
                                "status": "",
                                "pi": selected_pis[0] if selected_pis else "",
                                "total_leadtime": 0,
                            }
                        )

                print(f"📊 Found {len(related_items)} total items for export")

                # Create Excel workbook
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    # Sheet 1: Insight Summary
                    insight_summary = {
                        "Field": [
                            "Title",
                            "Severity",
                            "Confidence",
                            "Scope",
                            "Analysis Level",
                            "Total Items",
                            "Created At",
                        ],
                        "Value": [
                            insight_data.get("title", ""),
                            insight_data.get("severity", "").upper(),
                            f"{insight_data.get('confidence', 0) * 100:.0f}%",
                            insight_data.get("scope", ""),
                            analysis_level.title(),
                            len(related_items),
                            insight_data.get("created_at", datetime.now().isoformat()),
                        ],
                    }
                    summary_df = pd.DataFrame(insight_summary)
                    summary_df.to_excel(
                        writer, sheet_name="Insight Summary", index=False
                    )

                    # Sheet 2: Related Items (Features/Stories)
                    if related_items:
                        items_df = pd.DataFrame(related_items)
                        # Reorder columns
                        column_order = [
                            "issue_key",
                            "category",
                            "art",
                            "team",
                            "current_stage",
                            "days_in_stage",
                            "total_leadtime",
                            "summary",
                            "status",
                            "pi",
                        ]
                        column_order = [
                            col for col in column_order if col in items_df.columns
                        ]
                        items_df = items_df[column_order]
                        # Sort by days in stage descending
                        items_df = items_df.sort_values(
                            "days_in_stage", ascending=False
                        )
                        items_df.to_excel(
                            writer,
                            sheet_name=f"Related {analysis_level.title()}s",
                            index=False,
                        )
                    else:
                        # Create empty sheet
                        empty_df = pd.DataFrame(
                            columns=[
                                "issue_key",
                                "category",
                                "art",
                                "team",
                                "current_stage",
                                "days_in_stage",
                                "summary",
                            ]
                        )
                        empty_df.to_excel(
                            writer,
                            sheet_name=f"Related {analysis_level.title()}s",
                            index=False,
                        )

                    # Sheet 3: Observation & Interpretation
                    details = {
                        "Section": ["Observation", "Interpretation"],
                        "Content": [
                            insight_data.get("observation", ""),
                            insight_data.get("interpretation", ""),
                        ],
                    }
                    details_df = pd.DataFrame(details)
                    details_df.to_excel(writer, sheet_name="Details", index=False)

                    # Sheet 4: Root Causes
                    if root_causes:
                        rc_data = []
                        for rc in root_causes:
                            rc_data.append(
                                {
                                    "Description": rc.get("description", ""),
                                    "Confidence": f"{rc.get('confidence', 0) * 100:.0f}%",
                                    "Evidence": "\n".join(rc.get("evidence", [])),
                                    "Reference": rc.get("reference", ""),
                                }
                            )
                        rc_df = pd.DataFrame(rc_data)
                        rc_df.to_excel(writer, sheet_name="Root Causes", index=False)

                    # Sheet 5: Recommended Actions
                    actions = insight_data.get("recommended_actions", [])
                    if actions:
                        action_data = []
                        for action in actions:
                            action_data.append(
                                {
                                    "Timeframe": action.get("timeframe", "")
                                    .replace("_", " ")
                                    .title(),
                                    "Description": action.get("description", ""),
                                    "Owner": action.get("owner", "")
                                    .replace("_", " ")
                                    .title(),
                                    "Effort": action.get("effort", ""),
                                    "Success Signal": action.get("success_signal", ""),
                                }
                            )
                        action_df = pd.DataFrame(action_data)
                        action_df.to_excel(
                            writer, sheet_name="Recommended Actions", index=False
                        )

                output.seek(0)

                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                title_slug = re.sub(
                    r"[^a-z0-9]+", "_", insight_data.get("title", "insight").lower()
                )[:50]
                filename = f"insight_{title_slug}_{timestamp}.xlsx"

                return StreamingResponse(
                    output,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )

            except Exception as e:
                print(f"❌ Error exporting insight: {e}")
                import traceback

                traceback.print_exc()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to export insight: {str(e)}",
                )
        else:
            raise HTTPException(
                status_code=503, detail="Lead-time service not available"
            )
    except Exception as e:
        print(f"❌ Error in export insight endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard Endpoints
@app.get("/api/v1/dashboard", response_model=DashboardData)
async def get_dashboard(
    scope: str = "portfolio",
    time_range: str = "last_pi",
    pis: Optional[str] = None,
    arts: Optional[str] = None,
    team: Optional[str] = None,
    analysis_level: str = "feature",
    generate_insights: bool = False,
    db: Session = Depends(get_db),
):
    """Get dashboard data for specified scope and optional PI/ART/Team filter(s)

    Args:
        pis: Comma-separated list of PIs (e.g., "24Q1,24Q2,25Q1")
        arts: Comma-separated list of ARTs (e.g., "ACEART,C4ART,CIART")
        team: Team name for team-level analysis
        analysis_level: 'feature' or 'story' for team-level analysis (default: feature)
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
                # Fetch features or stories based on analysis level
                # Get excluded statuses from configuration
                excluded_statuses = get_excluded_feature_statuses(db)

                # Determine which data source to use
                use_story_level = analysis_level == "story"
                data_source_name = "user stories" if use_story_level else "features"

                # Log filtering details
                filter_info = f"scope={scope}, level={analysis_level}"
                if selected_arts:
                    filter_info += f", arts={selected_arts}"
                if team:
                    filter_info += f", team={team}"
                print(f"📊 Fetching {data_source_name} with filters: {filter_info}")

                if selected_arts:
                    # Fetch per ART to ensure we get all data
                    all_features = []
                    for art in selected_arts:
                        if use_story_level:
                            art_data = leadtime_service.client.get_story_flow_leadtime(
                                art=art, development_team=team, limit=10000
                            )
                        else:
                            art_data = leadtime_service.client.get_flow_leadtime(
                                art=art, development_team=team, limit=10000
                            )
                        all_features.extend(art_data)
                else:
                    # Get all data when no ART filter
                    if use_story_level:
                        all_features = leadtime_service.client.get_story_flow_leadtime(
                            development_team=team, limit=10000
                        )
                    else:
                        all_features = leadtime_service.client.get_flow_leadtime(
                            development_team=team, limit=10000
                        )

                # Apply status filter
                all_features = filter_features_by_status(
                    all_features, excluded_statuses
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
                        # Calculate value-add time based on data source
                        # For features: in_progress + in_reviewing
                        # For stories: in_development + in_review
                        if use_story_level:
                            value_add = feature.get("in_development", 0) + feature.get(
                                "in_review", 0
                            )
                        else:
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
                            art=art, team=team, limit=10000
                        )
                        all_throughput_features.extend(art_throughput)
                else:
                    # Get all throughput data when no ART filter
                    all_throughput_features = (
                        leadtime_service.client.get_throughput_data(
                            team=team, limit=10000
                        )
                    )

                # Apply status filter to throughput data
                all_throughput_features = filter_features_by_status(
                    all_throughput_features, excluded_statuses
                )

                # Filter by selected PIs
                filtered_throughput = all_throughput_features
                if selected_pis:
                    filtered_throughput = [
                        f for f in filtered_throughput if f.get("pi") in selected_pis
                    ]

                # Count only completed features (those with lead_time_days > 0)
                # Features without lead time are in progress or haven't been properly tracked
                completed_throughput = [
                    f for f in filtered_throughput if f.get("lead_time_days", 0) > 0
                ]
                throughput_count = len(completed_throughput)
                print(
                    f"✅ Features Delivered: {throughput_count} completed (from {len(filtered_throughput)} total in leadtime_thr_data)"
                )

                # Calculate average lead-time from throughput data (completed features only)
                if completed_throughput:
                    leadtimes = [
                        f.get("lead_time_days", 0)
                        for f in completed_throughput
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

                        # Apply status filter
                        features = filter_features_by_status(
                            features, excluded_statuses
                        )

                        # Filter by selected PIs if specified
                        if selected_pis:
                            # Helper to calculate PI from resolved date for Done features
                            def get_feature_pi(feature):
                                if feature.get("status") == "Done" and feature.get(
                                    "resolved_date"
                                ):
                                    try:
                                        resolved_dt = datetime.strptime(
                                            feature["resolved_date"][:10], "%Y-%m-%d"
                                        )
                                        config_entry = (
                                            db.query(RuntimeConfiguration)
                                            .filter(
                                                RuntimeConfiguration.config_key
                                                == "pi_configurations"
                                            )
                                            .first()
                                        )
                                        if config_entry and config_entry.config_value:
                                            import json

                                            pi_configurations = json.loads(
                                                config_entry.config_value
                                            )
                                            for pi_config in pi_configurations:
                                                start_date = datetime.strptime(
                                                    pi_config["start_date"], "%Y-%m-%d"
                                                )
                                                end_date = datetime.strptime(
                                                    pi_config["end_date"], "%Y-%m-%d"
                                                )
                                                if (
                                                    start_date
                                                    <= resolved_dt
                                                    <= end_date
                                                ):
                                                    return pi_config.get("pi")
                                    except:
                                        pass
                                return feature.get("pi")

                            features = [
                                f for f in features if get_feature_pi(f) in selected_pis
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
                            # Note: get_throughput_data only accepts single PI, so we fetch all and filter
                            throughput_features = (
                                leadtime_service.client.get_throughput_data(
                                    art=art_name, limit=10000
                                )
                            )
                            print(
                                f"   📊 {art_name}: Retrieved {len(throughput_features)} total throughput features"
                            )

                            # Apply status filter first
                            throughput_features = filter_features_by_status(
                                throughput_features, excluded_statuses
                            )
                            print(
                                f"   ✅ {art_name}: After status filter: {len(throughput_features)} features"
                            )

                            # Filter by selected PIs if specified (CRITICAL: do this before counting!)
                            if selected_pis:
                                before_pi_filter = len(throughput_features)
                                throughput_features = [
                                    f
                                    for f in throughput_features
                                    if f.get("pi") in selected_pis
                                ]
                                print(
                                    f"   🎯 {art_name}: PI filter {selected_pis} reduced from {before_pi_filter} to {len(throughput_features)} features"
                                )

                            if throughput_features:
                                # Count only completed features (those with lead_time_days > 0)
                                completed_features = [
                                    f
                                    for f in throughput_features
                                    if f.get("lead_time_days", 0) > 0
                                ]

                                thr_leadtimes = [
                                    f.get("lead_time_days", 0)
                                    for f in completed_features
                                ]
                                avg_leadtime_art = (
                                    sum(thr_leadtimes) / len(thr_leadtimes)
                                    if thr_leadtimes
                                    else 0
                                )
                                print(
                                    f"   ✅ {art_name}: {len(completed_features)} completed features (avg lead time: {avg_leadtime_art:.1f} days)"
                                )
                            else:
                                completed_features = []
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
                                    "features_delivered": len(completed_features),
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

        # Filter inactive ARTs based on configuration
        show_inactive_arts = True  # Default
        try:
            config_entry = (
                db.query(RuntimeConfiguration)
                .filter(RuntimeConfiguration.config_key == "show_inactive_arts")
                .first()
            )
            if config_entry and config_entry.config_value:
                show_inactive_arts = config_entry.config_value.lower() == "true"
                print(f"📊 show_inactive_arts config: {show_inactive_arts}")
        except Exception as e:
            print(f"⚠️ Could not load show_inactive_arts config: {e}")

        # Apply filtering if configured to hide inactive ARTs
        if not show_inactive_arts and art_comparison:
            original_count = len(art_comparison)
            art_comparison = [
                art for art in art_comparison if art.get("features_delivered", 0) > 0
            ]
            filtered_count = len(art_comparison)
            if filtered_count < original_count:
                print(
                    f"🔍 Filtered out {original_count - filtered_count} inactive ARTs (showing {filtered_count})"
                )

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
                            f"{art['art_name']}: {art['flow_efficiency']}% flow, {art.get('planning_accuracy', art.get('pi_predictability', 0))}% planning accuracy"
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
        import traceback

        error_details = traceback.format_exc()
        print(f"❌ Dashboard error: {str(e)}")
        print(f"Full traceback:\n{error_details}")
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
# NOTE: Keep this legacy/body-based generator on a distinct path.
# The UI uses the query-param endpoint at POST /api/v1/insights/generate.
@app.post("/api/v1/insights/generate_basic", response_model=List[InsightResponse])
async def generate_insights_basic(
    request: AnalysisRequest, db: Session = Depends(get_db)
):
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

            # Extract current metrics for strategic target comparison
            current_leadtime = None
            current_planning_accuracy = None

            if stats and "average_leadtime_days" in stats:
                current_leadtime = stats["average_leadtime_days"]

            if planning and "predictability_score" in planning:
                current_planning_accuracy = planning["predictability_score"]

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

            # Always add strategic target insights if configured
            strategic_insights = await insights_service.generate_insights(
                scope=request.scope,
                scope_id=request.scope_id,
                time_range=request.time_range,
                db=db,
                current_leadtime=current_leadtime,
                current_planning_accuracy=current_planning_accuracy,
            )

            # Merge leadtime insights with strategic target insights
            if generated_insights:
                # Combine both types of insights
                return generated_insights + strategic_insights

            # Return strategic insights if no leadtime insights
            return strategic_insights

        # Fallback: just strategic/sample insights when leadtime service unavailable
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

        # Build coaching facts to ground the LLM response (avoid hallucinations)
        # Skip expensive fact gathering for simple and generic queries
        facts: Dict[str, Any] = {}
        message_lower = request.message.lower()
        is_simple_query = any(
            word in message_lower
            for word in [
                "hello",
                "hi",
                "help",
                "what can you",
                "explore",
                "analyze",  # Generic "analyze" without specifics
                "identify bottleneck",  # Generic bottleneck query
            ]
        )

        # For generic queries, provide a helpful response without heavy data gathering
        if is_simple_query and any(
            word in message_lower for word in ["analyze", "identify", "bottleneck"]
        ):
            # Return quick response for generic analysis requests
            return ChatResponse(
                message=(
                    "📊 <strong>I can help you analyze specific metrics!</strong><br><br>"
                    "To provide detailed analysis, please be more specific:<br><br>"
                    "🔍 <strong>Try asking:</strong><br>"
                    "• 'What's our current flow efficiency?'<br>"
                    "• 'Show me lead time trends'<br>"
                    "• 'Which teams have high WIP?'<br>"
                    "• 'What's blocking Feature X?'<br>"
                    "• 'Show me planning accuracy for Q4'<br><br>"
                    "Or use the <strong>Insights</strong> tab to generate comprehensive reports."
                ),
                context=request.context or {},
                timestamp=datetime.utcnow(),
            )

        try:
            facts["strategic_targets"] = {
                "leadtime_target_2026": settings.leadtime_target_2026,
                "leadtime_target_2027": settings.leadtime_target_2027,
                "leadtime_target_true_north": settings.leadtime_target_true_north,
                "planning_accuracy_target_2026": settings.planning_accuracy_target_2026,
                "planning_accuracy_target_2027": settings.planning_accuracy_target_2027,
                "planning_accuracy_target_true_north": settings.planning_accuracy_target_true_north,
            }
        except Exception:
            facts["strategic_targets"] = {}

        # Only fetch recent insights for non-simple queries
        if not is_simple_query:
            try:
                from database import Insight

                scope = (request.context or {}).get("scope") or "portfolio"
                scope_id = (request.context or {}).get("scope_id")
                q = db.query(Insight).filter(Insight.scope == scope)
                if scope_id:
                    q = q.filter(Insight.scope_id == scope_id)
                recent = (
                    q.order_by(Insight.created_at.desc()).limit(3).all()
                )  # Reduced from 5 to 3
                facts["recent_insights"] = [
                    {
                        "title": i.title,
                        "severity": i.severity,
                        "confidence": i.confidence,
                    }
                    for i in reversed(recent)
                ]
            except Exception:
                facts["recent_insights"] = []
        else:
            facts["recent_insights"] = []

        # Live metrics from LeadTime service (only for complex queries)
        if not is_simple_query:
            try:
                if leadtime_service and leadtime_service.is_available():
                    ctx = request.context or {}
                    scope = ctx.get("scope") or "portfolio"
                    scope_id = ctx.get("scope_id")

                    selected_arts = (
                        [scope_id] if (scope == "art" and scope_id) else None
                    )

                    facts["leadtime"] = leadtime_service.get_leadtime_statistics(
                        arts=selected_arts
                    )
                    facts["planning"] = leadtime_service.get_planning_accuracy(
                        arts=selected_arts
                    )
                    facts["throughput"] = leadtime_service.get_throughput_metrics(
                        arts=selected_arts
                    )
                    # Skip bottleneck analysis for faster response
                    # facts["bottlenecks"] = leadtime_service.identify_bottlenecks(
                    #     arts=selected_arts
                    # )
            except Exception:
                # If live metrics fail, we still continue with recent insights and targets
                pass

        # Generate AI response
        response = await llm_service.generate_response(
            message=request.message,
            context=request.context,
            facts=facts,
            session_id=request.session_id,
            db=db,
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


@app.get("/api/v1/flow-health-check")
async def get_flow_health_check():
    """Get Flow Health Check framework content from knowledge base"""
    try:
        from pathlib import Path

        kb_path = (
            Path(__file__).parent / "data" / "knowledge_base" / "flow_health_check.txt"
        )

        if not kb_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flow Health Check content not found",
            )

        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the content into structured format
        sections = content.split("---")
        parsed_data = {"quick_test": {}, "categories": [], "flow_smells": {}}

        for section in sections:
            section = section.strip()
            if not section or section.startswith("type:"):
                continue

            lines = [line.strip() for line in section.split("\n") if line.strip()]

            # Parse One-Minute Test
            if "One-Minute Flow Health Test" in section:
                questions = []
                for line in lines:
                    if line.startswith(("1.", "2.", "3.")):
                        questions.append(line[3:].strip())
                parsed_data["quick_test"] = {
                    "title": "One-Minute Flow Health Test",
                    "questions": questions,
                    "warning": "If people can't answer → flow is not under control",
                }

            # Parse Category sections
            elif "Category " in section and "TITLE:" in section:
                category = {}
                current_key = None
                items = []

                for line in lines:
                    if line.startswith("TITLE:"):
                        category["title"] = line.replace("TITLE:", "").strip()
                    elif line.startswith("SUBTITLE:"):
                        category["subtitle"] = line.replace("SUBTITLE:", "").strip()
                    elif line.startswith("PROBING_QUESTIONS:"):
                        current_key = "questions"
                        items = []
                    elif line.startswith("GOOD_FLOW_INDICATORS:"):
                        if current_key == "questions":
                            category["questions"] = items
                        current_key = "good"
                        items = []
                    elif line.startswith("BAD_FLOW_INDICATORS:"):
                        if current_key == "good":
                            category["good"] = " ".join(items)
                        current_key = "bad"
                        items = []
                    elif line.startswith("- "):
                        items.append(line[2:].strip())
                    elif (
                        current_key
                        and line
                        and not line.startswith(("#", "IMPORTANCE"))
                    ):
                        items.append(line)

                if current_key == "bad" and items:
                    category["bad"] = " ".join(items)

                if "title" in category:
                    parsed_data["categories"].append(category)

            # Parse Flow Smell Checklist
            elif "Flow Smell Checklist" in section:
                bad_phrases = []
                good_phrases = []
                current_list = None

                for line in lines:
                    if line.startswith("BAD_FLOW_PHRASES:"):
                        current_list = "bad"
                    elif line.startswith("GOOD_FLOW_PHRASES:"):
                        current_list = "good"
                    elif line.startswith("- "):
                        phrase = line[2:].strip().strip('"')
                        if current_list == "bad":
                            bad_phrases.append(phrase)
                        elif current_list == "good":
                            good_phrases.append(phrase)

                parsed_data["flow_smells"] = {"bad": bad_phrases, "good": good_phrases}

        return parsed_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading Flow Health Check: {str(e)}",
        )


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


@app.get("/api/teams/with-art")
async def get_teams_with_art():
    """Get list of all teams with their ART mapping from DL Webb App server"""
    if not leadtime_service:
        return {"teams": [], "message": "Lead-time service not available"}

    try:
        # Get full team data from DL Webb App which includes ART information
        teams_data = leadtime_service.client.get_teams()

        # Transform to simplified format with team name and ART
        teams_with_art = []
        for team in teams_data:
            art_data = team.get("art", {}) if team.get("art") else {}
            team_info = {
                "team_name": team.get("team_name"),
                "team_id": team.get("team_id"),
                "art_name": art_data.get("art_name"),
                "art_key": art_data.get("art_key_jira"),  # ART key like "UCART"
                "art_id": team.get("art_id"),
            }
            teams_with_art.append(team_info)

        return {
            "teams": teams_with_art,
            "count": len(teams_with_art),
            "source": "DL Webb App",
        }
    except Exception as e:
        logger.error(f"Failed to fetch teams with ART: {e}")
        raise HTTPException(
            status_code=503, detail=f"Could not fetch teams with ART: {str(e)}"
        )


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

        # Get ALL PIs throughput data (unfiltered) for calculating "Avg Last 4 PIs"
        throughput_all_pis = leadtime_service.client.get_throughput_analysis(
            arts=selected_arts, pis=None  # Get all PIs
        )

        # Calculate waste metrics
        waiting_waste = waste_data.get("waiting_time_waste", {})
        removed_work = waste_data.get("removed_work", {})
        total_waste = waste_data.get("total_waste_days", 0)
        waste_categories = waste_data.get("waste_categories", {})

        # Extract throughput trends
        throughput_by_pi = throughput_full.get("by_pi", {})
        overall_throughput = throughput_full.get("overall_statistics", {})

        # Calculate average of 4 PIs BEFORE the selected PI(s)
        # Use ALL PIs data to find the ones before selected
        throughput_all_by_pi = throughput_all_pis.get("by_pi", {})
        avg_last_4_pis = 0
        prev_4_pis_data = {}

        if selected_pis and len(throughput_all_by_pi) > 0:
            # Get all PIs sorted chronologically
            all_pis_sorted = sorted(throughput_all_by_pi.keys())

            # Find the earliest selected PI
            earliest_selected = min(selected_pis) if selected_pis else None

            if earliest_selected and earliest_selected in all_pis_sorted:
                # Get index of earliest selected PI
                selected_index = all_pis_sorted.index(earliest_selected)

                # Get the 4 PIs before the selected one
                prev_4_pis = all_pis_sorted[max(0, selected_index - 4) : selected_index]

                if prev_4_pis:
                    prev_throughputs = [
                        throughput_all_by_pi[pi].get("throughput", 0)
                        for pi in prev_4_pis
                    ]
                    avg_last_4_pis = round(
                        sum(prev_throughputs) / len(prev_throughputs), 1
                    )

                    # Store the previous 4 PIs data for display
                    for pi in prev_4_pis:
                        prev_4_pis_data[pi] = {
                            "throughput": throughput_all_by_pi[pi].get("throughput", 0),
                            "avg_leadtime": round(
                                throughput_all_by_pi[pi].get("average_leadtime", 0), 1
                            ),
                        }
        elif not selected_pis and len(throughput_by_pi) > 0:
            # If no PIs selected, use the last 4 available PIs
            last_4 = sorted(throughput_by_pi.items())[-4:]
            if last_4:
                avg_last_4_pis = round(
                    sum(data.get("throughput", 0) for pi, data in last_4) / len(last_4),
                    1,
                )
                # Store the last 4 PIs data
                for pi, data in last_4:
                    prev_4_pis_data[pi] = {
                        "throughput": data.get("throughput", 0),
                        "avg_leadtime": round(data.get("average_leadtime", 0), 1),
                    }

        # Get raw flow data for proper calculations
        flow_data = leadtime_service.client.get_flow_leadtime(
            arts=selected_arts, pis=selected_pis
        )

        def _norm_str(value: Any) -> Optional[str]:
            if value is None:
                return None
            if isinstance(value, str):
                trimmed = value.strip()
                return trimmed if trimmed else None
            return str(value)

        def _get_art_label(item: Dict[str, Any]) -> Optional[str]:
            return (
                _norm_str(item.get("art"))
                or _norm_str(item.get("art_name"))
                or _norm_str(item.get("art_id"))
            )

        def _get_team_label(item: Dict[str, Any]) -> Optional[str]:
            return (
                _norm_str(item.get("team"))
                or _norm_str(item.get("development_team"))
                or _norm_str(item.get("team_name"))
                or _norm_str(item.get("team_id"))
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

        # =========================
        # Structure Metrics
        # =========================

        # ARTs/Teams lists for topology counts
        all_arts = []
        try:
            all_arts = leadtime_service.client.get_arts() or []
        except Exception:
            all_arts = []

        all_teams = []
        try:
            all_teams = leadtime_service.client.get_teams() or []
        except Exception:
            all_teams = []

        if selected_arts:
            art_count = len(selected_arts)
        else:
            art_names = [
                _norm_str(a.get("art"))
                or _norm_str(a.get("art_name"))
                or _norm_str(a.get("name"))
                for a in all_arts
            ]
            art_count = len({a for a in art_names if a})

        # Prefer team count from feature_data in scope (more reliable than global team list)
        team_labels_in_scope = {_get_team_label(f) for f in feature_data}
        team_labels_in_scope = {t for t in team_labels_in_scope if t}
        team_count = (
            len(team_labels_in_scope) if team_labels_in_scope else len(all_teams)
        )

        # Teams per ART (based on feature_data relationships)
        teams_by_art: Dict[str, set] = {}
        for f in feature_data:
            art_label = _get_art_label(f)
            team_label = _get_team_label(f)
            if not art_label:
                continue
            if art_label not in teams_by_art:
                teams_by_art[art_label] = set()
            if team_label:
                teams_by_art[art_label].add(team_label)

        teams_per_art_counts = {k: len(v) for k, v in teams_by_art.items()}
        teams_per_art_values = list(teams_per_art_counts.values())
        if teams_per_art_values:
            teams_per_art_values_sorted = sorted(teams_per_art_values)
            teams_per_art_min = teams_per_art_values_sorted[0]
            teams_per_art_max = teams_per_art_values_sorted[-1]
            teams_per_art_median = teams_per_art_values_sorted[
                len(teams_per_art_values_sorted) // 2
            ]
            teams_per_art_avg = round(
                sum(teams_per_art_values) / len(teams_per_art_values), 1
            )
        else:
            teams_per_art_min = 0
            teams_per_art_max = 0
            teams_per_art_median = 0
            teams_per_art_avg = 0

        # Ownership coverage (team populated) in current scope
        total_features_in_scope = len(flow_data)
        features_with_team = sum(1 for f in flow_data if _get_team_label(f))
        team_coverage_pct = (
            round((features_with_team / total_features_in_scope) * 100, 1)
            if total_features_in_scope > 0
            else 0
        )

        # Delivery concentration (top 5 teams share of delivered features)
        delivered_features = []
        try:
            if selected_arts:
                for art in selected_arts:
                    delivered_features.extend(
                        leadtime_service.client.get_throughput_data(
                            art=art, limit=10000
                        )
                    )
            else:
                delivered_features = leadtime_service.client.get_throughput_data(
                    limit=10000
                )
        except Exception:
            delivered_features = []

        if selected_pis and delivered_features:
            delivered_features = [
                f
                for f in delivered_features
                if (f.get("pi") in selected_pis)
                or (f.get("program_increment") in selected_pis)
            ]

        delivered_total = len(delivered_features)
        delivered_by_team: Dict[str, int] = {}
        for f in delivered_features:
            team_label = _get_team_label(f) or "Unknown"
            delivered_by_team[team_label] = delivered_by_team.get(team_label, 0) + 1

        top_teams = sorted(
            delivered_by_team.items(), key=lambda kv: kv[1], reverse=True
        )[:5]
        top5_count = sum(count for _, count in top_teams)
        top5_share_pct = (
            round((top5_count / delivered_total) * 100, 1) if delivered_total > 0 else 0
        )
        top5_breakdown = {name: count for name, count in top_teams}

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
                    "avg_last_4_pis": avg_last_4_pis,
                    "prev_4_pis_data": prev_4_pis_data,
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
                    "name": "Velocity (Feature Throughput)",
                    "description": "Features completed per PI - measures team capacity and predictability",
                    "formula": "count(status = 'Done' AND resolved IN pi_timeframe)",
                    "current_value": overall_throughput.get("total_throughput", 0),
                    "unit": "features",
                    "average_per_pi": round(
                        overall_throughput.get("total_throughput", 0)
                        / max(len(throughput_by_pi), 1),
                        1,
                    ),
                    "avg_last_4_pis": avg_last_4_pis,
                    "prev_4_pis_data": prev_4_pis_data,
                    "status": (
                        "good"
                        if overall_throughput.get("total_throughput", 0) > 0
                        else "unknown"
                    ),
                    "target": "Stable Feature throughput per PI",
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
            "structure_metrics": {
                "art_count": {
                    "name": "ART Count",
                    "description": "Number of Agile Release Trains (ARTs) in the current scope.",
                    "formula": "count(distinct ART)",
                    "current_value": art_count,
                    "unit": "ARTs",
                    "status": "good" if art_count > 0 else "unknown",
                    "jira_fields": ["art"],
                },
                "team_count": {
                    "name": "Team Count",
                    "description": "Number of teams represented by feature data in the current scope.",
                    "formula": "count(distinct Team)",
                    "current_value": team_count,
                    "unit": "teams",
                    "status": "good" if team_count > 0 else "unknown",
                    "jira_fields": ["team"],
                },
                "teams_per_art": {
                    "name": "Teams per ART (Distribution)",
                    "description": "Distribution of teams per ART based on feature ownership relationships.",
                    "formula": "count(distinct Team) grouped by ART",
                    "current_value": teams_per_art_median,
                    "unit": "teams/ART (median)",
                    "status": "good" if teams_per_art_median > 0 else "unknown",
                    "jira_fields": ["art", "team"],
                    "min": teams_per_art_min,
                    "max": teams_per_art_max,
                    "avg": teams_per_art_avg,
                    "breakdown_kv": dict(
                        sorted(teams_per_art_counts.items(), key=lambda kv: kv[0])
                    ),
                },
                "team_ownership_coverage": {
                    "name": "Team Ownership Coverage",
                    "description": "Percent of features in scope with a team populated (ownership clarity).",
                    "formula": "count(team != null) / count(features) * 100",
                    "current_value": team_coverage_pct,
                    "unit": "%",
                    "status": (
                        "good"
                        if team_coverage_pct >= 90
                        else "warning" if team_coverage_pct >= 70 else "critical"
                    ),
                    "jira_fields": ["team"],
                },
                "delivery_concentration": {
                    "name": "Delivery Concentration (Top 5 Teams)",
                    "description": "Share of delivered features owned by the top 5 teams (higher = more concentrated risk).",
                    "formula": "sum(top5_team_throughput) / total_throughput * 100",
                    "current_value": top5_share_pct,
                    "unit": "%",
                    "status": (
                        "critical"
                        if top5_share_pct >= 80
                        else "warning" if top5_share_pct >= 60 else "good"
                    ),
                    "jira_fields": ["team", "resolutiondate"],
                    "breakdown_kv": top5_breakdown,
                },
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
async def get_admin_config(db: Session = Depends(get_db)):
    """
    Get current admin configuration including thresholds and settings.

    Returns:
        Current configuration settings
    """
    thresholds = ThresholdConfig(
        # Feature-level thresholds
        bottleneck_threshold_days=settings.bottleneck_threshold_days,
        planning_accuracy_threshold_pct=settings.planning_accuracy_threshold_pct,
        # Story-level thresholds
        story_bottleneck_threshold_days=settings.story_bottleneck_threshold_days,
        # Strategic targets
        leadtime_target_2026=settings.leadtime_target_2026,
        leadtime_target_2027=settings.leadtime_target_2027,
        leadtime_target_true_north=settings.leadtime_target_true_north,
        planning_accuracy_target_2026=settings.planning_accuracy_target_2026,
        planning_accuracy_target_2027=settings.planning_accuracy_target_2027,
        planning_accuracy_target_true_north=settings.planning_accuracy_target_true_north,
        # Feature stage-specific thresholds
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
        # Story stage-specific thresholds
        story_threshold_refinement=settings.story_threshold_refinement,
        story_threshold_ready_for_development=settings.story_threshold_ready_for_development,
        story_threshold_in_development=settings.story_threshold_in_development,
        story_threshold_in_review=settings.story_threshold_in_review,
        story_threshold_ready_for_test=settings.story_threshold_ready_for_test,
        story_threshold_in_testing=settings.story_threshold_in_testing,
        story_threshold_ready_for_deployment=settings.story_threshold_ready_for_deployment,
    )

    # Get show_inactive_arts from database
    show_inactive_arts = True  # Default
    try:
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "show_inactive_arts")
            .first()
        )
        if config_entry and config_entry.config_value:
            show_inactive_arts = config_entry.config_value.lower() == "true"
    except Exception as e:
        print(f"⚠️ Could not load show_inactive_arts config: {e}")

    # Get excluded_feature_statuses from database
    excluded_feature_statuses = []  # Default
    try:
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "excluded_feature_statuses")
            .first()
        )
        if config_entry and config_entry.config_value:
            # Parse comma-separated list
            excluded_feature_statuses = [
                s.strip() for s in config_entry.config_value.split(",") if s.strip()
            ]
    except Exception as e:
        print(f"⚠️ Could not load excluded_feature_statuses config: {e}")

    # Get LLM configuration from database
    llm_model = "llama3.1:latest"  # Default (Ollama - free and local)
    llm_temperature = 0.3  # Default
    try:
        model_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "llm_model")
            .first()
        )
        if model_entry and model_entry.config_value:
            llm_model = model_entry.config_value

        temp_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "llm_temperature")
            .first()
        )
        if temp_entry and temp_entry.config_value:
            llm_temperature = float(temp_entry.config_value)
    except Exception as e:
        print(f"⚠️ Could not load LLM config: {e}")

    return AdminConfigResponse(
        thresholds=thresholds,
        leadtime_server_url=settings.leadtime_server_url,
        leadtime_server_enabled=settings.leadtime_server_enabled,
        show_inactive_arts=show_inactive_arts,
        excluded_feature_statuses=excluded_feature_statuses,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
    )


@app.post("/api/admin/config/thresholds")
async def update_thresholds(thresholds: ThresholdConfig, db: Session = Depends(get_db)):
    """
    Update threshold configuration.

    This now persists configuration to the database, so values will
    survive server restarts and page refreshes.

    Args:
        thresholds: New threshold configuration
        db: Database session

    Returns:
        Updated configuration
    """
    # Define all configuration fields
    config_updates = {
        # Feature-level thresholds
        "bottleneck_threshold_days": thresholds.bottleneck_threshold_days,
        "planning_accuracy_threshold_pct": thresholds.planning_accuracy_threshold_pct,
        # Story-level thresholds
        "story_bottleneck_threshold_days": thresholds.story_bottleneck_threshold_days,
        # Strategic targets
        "leadtime_target_2026": thresholds.leadtime_target_2026,
        "leadtime_target_2027": thresholds.leadtime_target_2027,
        "leadtime_target_true_north": thresholds.leadtime_target_true_north,
        "planning_accuracy_target_2026": thresholds.planning_accuracy_target_2026,
        "planning_accuracy_target_2027": thresholds.planning_accuracy_target_2027,
        "planning_accuracy_target_true_north": thresholds.planning_accuracy_target_true_north,
        # Feature stage-specific thresholds
        "threshold_in_backlog": thresholds.threshold_in_backlog,
        "threshold_in_analysis": thresholds.threshold_in_analysis,
        "threshold_in_planned": thresholds.threshold_in_planned,
        "threshold_in_progress": thresholds.threshold_in_progress,
        "threshold_in_reviewing": thresholds.threshold_in_reviewing,
        "threshold_ready_for_sit": thresholds.threshold_ready_for_sit,
        "threshold_in_sit": thresholds.threshold_in_sit,
        "threshold_ready_for_uat": thresholds.threshold_ready_for_uat,
        "threshold_in_uat": thresholds.threshold_in_uat,
        "threshold_ready_for_deployment": thresholds.threshold_ready_for_deployment,
        # Story stage-specific thresholds
        "story_threshold_refinement": thresholds.story_threshold_refinement,
        "story_threshold_ready_for_development": thresholds.story_threshold_ready_for_development,
        "story_threshold_in_development": thresholds.story_threshold_in_development,
        "story_threshold_in_review": thresholds.story_threshold_in_review,
        "story_threshold_ready_for_test": thresholds.story_threshold_ready_for_test,
        "story_threshold_in_testing": thresholds.story_threshold_in_testing,
        "story_threshold_ready_for_deployment": thresholds.story_threshold_ready_for_deployment,
    }

    try:
        # Update runtime settings AND save to database
        for config_key, config_value in config_updates.items():
            setattr(settings, config_key, config_value)
            save_config_to_db(db, config_key, config_value)

        return {
            "status": "success",
            "message": "Configuration saved successfully and will persist across restarts",
            "thresholds": thresholds,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}",
        )


@app.post("/api/admin/config/display")
async def update_display_options(
    options: Dict[str, Any], db: Session = Depends(get_db)
):
    """
    Update display options configuration.

    Args:
        options: Display options (e.g., show_inactive_arts)
        db: Database session

    Returns:
        Success message
    """
    try:
        show_inactive_arts = options.get("show_inactive_arts", True)
        excluded_feature_statuses = options.get("excluded_feature_statuses", [])

        # Save show_inactive_arts to database
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "show_inactive_arts")
            .first()
        )

        if config_entry:
            config_entry.config_value = "true" if show_inactive_arts else "false"
            config_entry.updated_at = datetime.now(timezone.utc)
        else:
            config_entry = RuntimeConfiguration(
                config_key="show_inactive_arts",
                config_value="true" if show_inactive_arts else "false",
                config_type="bool",
            )
            db.add(config_entry)

        # Save excluded_feature_statuses to database
        excluded_statuses_str = (
            ",".join(excluded_feature_statuses) if excluded_feature_statuses else ""
        )
        config_entry_statuses = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "excluded_feature_statuses")
            .first()
        )

        if config_entry_statuses:
            config_entry_statuses.config_value = excluded_statuses_str
            config_entry_statuses.updated_at = datetime.now(timezone.utc)
        else:
            config_entry_statuses = RuntimeConfiguration(
                config_key="excluded_feature_statuses",
                config_value=excluded_statuses_str,
                config_type="string",
            )
            db.add(config_entry_statuses)

        db.commit()

        print(
            f"✅ Display options saved: show_inactive_arts={show_inactive_arts}, excluded_feature_statuses={excluded_feature_statuses}"
        )

        return {
            "status": "success",
            "message": "Display options saved successfully. Dashboard will update on next load.",
            "show_inactive_arts": show_inactive_arts,
            "excluded_feature_statuses": excluded_feature_statuses,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save display options: {str(e)}",
        )


@app.post("/api/admin/config/llm")
async def update_llm_config(config: LLMConfigUpdate, db: Session = Depends(get_db)):
    """
    Update LLM configuration.

    Args:
        config: LLM configuration (model, temperature)
        db: Database session

    Returns:
        Success message
    """
    try:
        # Save LLM model to database
        model_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "llm_model")
            .first()
        )

        if model_entry:
            model_entry.config_value = config.model
            model_entry.updated_at = datetime.now(timezone.utc)
        else:
            model_entry = RuntimeConfiguration(
                config_key="llm_model",
                config_value=config.model,
                config_type="string",
            )
            db.add(model_entry)

        # Save LLM temperature to database
        temp_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "llm_temperature")
            .first()
        )

        if temp_entry:
            temp_entry.config_value = str(config.temperature)
            temp_entry.updated_at = datetime.now(timezone.utc)
        else:
            temp_entry = RuntimeConfiguration(
                config_key="llm_temperature",
                config_value=str(config.temperature),
                config_type="float",
            )
            db.add(temp_entry)

        db.commit()

        print(
            f"✅ LLM config saved: model={config.model}, temperature={config.temperature}"
        )

        return {
            "status": "success",
            "message": "LLM configuration saved successfully.",
            "model": config.model,
            "temperature": config.temperature,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save LLM configuration: {str(e)}",
        )


@app.get("/api/admin/config/pi")
async def get_pi_config(db: Session = Depends(get_db)):
    """
    Get Program Increment configurations.

    Returns:
        List of PI configurations with dates
    """
    try:
        # Get PI configurations from database
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "pi_configurations")
            .first()
        )

        pi_configurations = []
        if config_entry and config_entry.config_value:
            import json

            pi_configurations = json.loads(config_entry.config_value)

        return {"pi_configurations": pi_configurations}

    except Exception as e:
        print(f"⚠️ Error loading PI configurations: {e}")
        return {"pi_configurations": []}


@app.post("/api/admin/config/pi")
async def update_pi_config(config: dict, db: Session = Depends(get_db)):
    """
    Update Program Increment configurations.

    Args:
        config: Dictionary containing pi_configurations list
        db: Database session

    Returns:
        Success message
    """
    try:
        import json

        pi_configurations = config.get("pi_configurations", [])

        print(f"📥 Received PI config update request with {len(pi_configurations)} PIs")
        print(f"🔍 PI configurations: {json.dumps(pi_configurations, indent=2)}")

        # Validate PI configurations
        for idx, pi_config in enumerate(pi_configurations):
            if (
                not pi_config.get("pi")
                or not pi_config.get("start_date")
                or not pi_config.get("end_date")
            ):
                print(f"❌ Invalid PI config at index {idx}: {pi_config}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PI configuration at index {idx} is invalid: must have pi, start_date, and end_date",
                )

        # Save to database
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "pi_configurations")
            .first()
        )

        json_value = json.dumps(pi_configurations)
        print(f"📊 JSON size: {len(json_value)} characters")

        if config_entry:
            config_entry.config_value = json_value
            config_entry.updated_at = datetime.now(timezone.utc)
            print(f"♻️ Updating existing PI configuration entry")
        else:
            config_entry = RuntimeConfiguration(
                config_key="pi_configurations",
                config_value=json_value,
                config_type="json",
            )
            db.add(config_entry)
            print(f"➕ Creating new PI configuration entry")

        db.commit()

        print(f"✅ PI configurations saved: {len(pi_configurations)} PIs")

        return {
            "status": "success",
            "message": f"PI configurations saved successfully ({len(pi_configurations)} PIs).",
            "pi_configurations": pi_configurations,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save PI configurations: {str(e)}",
        )


# ============================================================================
# RAG Knowledge Base Management API
# ============================================================================


@app.get("/api/admin/rag/stats")
async def get_rag_stats():
    """
    Get RAG knowledge base statistics.

    Returns:
        Statistics about indexed documents and chunks
    """
    try:
        from services.rag_service import get_rag_service

        rag = get_rag_service()
        stats = rag.get_stats()

        return {
            "status": "success",
            "total_chunks": stats["total_chunks"],
            "total_documents": stats["total_documents"],
            "sources": stats["sources"],
            "chunk_size": stats["chunk_size"],
            "chunk_overlap": stats["chunk_overlap"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RAG stats: {str(e)}",
        )


@app.post("/api/admin/rag/reindex")
async def reindex_rag():
    """
    Re-index the RAG knowledge base.

    This will:
    1. Clear the existing ChromaDB collection
    2. Re-scan backend/data/knowledge_base/ directory
    3. Chunk all .txt files
    4. Generate embeddings and store in ChromaDB

    Returns:
        Number of chunks indexed
    """
    try:
        from services.rag_service import get_rag_service

        rag = get_rag_service()

        # Reset collection (clear all existing chunks)
        rag.reset_collection()

        # Re-index all documents
        chunks_indexed = rag.index_knowledge_base()

        return {
            "status": "success",
            "message": "Knowledge base re-indexed successfully",
            "chunks_indexed": chunks_indexed,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-index RAG: {str(e)}",
        )


@app.post("/api/admin/rag/upload")
async def upload_rag_document(file: UploadFile = File(...)):
    """
    Upload a document to the RAG knowledge base.

    This will:
    1. Validate the file (must be .txt)
    2. Save to backend/data/knowledge_base/
    3. Automatically trigger re-indexing

    Returns:
        Upload status and re-indexing results
    """
    try:
        # Validate file type
        if not file.filename.endswith(".txt"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .txt files are supported",
            )

        # Get knowledge base directory (same path as RAG service uses)
        base_dir = Path(__file__).parent
        kb_dir = base_dir / "data" / "knowledge_base"
        kb_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = kb_dir / file.filename

        # Read and save file content
        content = await file.read()

        # Validate UTF-8 encoding
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be UTF-8 encoded",
            )

        # Write file
        with open(file_path, "wb") as f:
            f.write(content)

        # Automatically re-index after upload
        from services.rag_service import get_rag_service

        rag = get_rag_service()
        rag.reset_collection()
        chunks_indexed = rag.index_knowledge_base()

        return {
            "status": "success",
            "message": f"Document '{file.filename}' uploaded and indexed successfully",
            "filename": file.filename,
            "file_size": len(content),
            "chunks_indexed": chunks_indexed,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


# ============================================================================
# PROMPT MANAGEMENT ENDPOINTS
# ============================================================================


@app.get("/api/admin/prompts/stats")
async def get_prompt_stats():
    """
    Get statistics about prompts.

    Returns:
        Statistics including total prompts, active/inactive counts, versions
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()

        stats = prompt_service.get_stats()

        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt stats: {str(e)}",
        )


@app.get("/api/admin/prompts")
async def get_all_prompts():
    """
    Get all prompts with their metadata.

    Returns:
        List of all prompts with versions and status
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()
        prompts = prompt_service.get_all_prompts()
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompts: {str(e)}",
        )


@app.get("/api/admin/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """
    Get a specific prompt by ID.

    Args:
        prompt_id: The unique identifier for the prompt

    Returns:
        Prompt data including current version
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()
        prompt = prompt_service.get_prompt(prompt_id)

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt '{prompt_id}' not found",
            )

        return prompt
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}",
        )


@app.post("/api/admin/prompts")
async def create_prompt(data: Dict[str, Any]):
    """
    Create a new prompt.

    Expected fields:
        - id: Unique identifier
        - name: Display name
        - description: Description of the prompt's purpose
        - prompt: The actual prompt text
        - tags: Optional list of tags

    Returns:
        Created prompt data
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()

        required_fields = ["id", "name", "description", "prompt"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        prompt = prompt_service.create_prompt(
            prompt_id=data["id"],
            name=data["name"],
            description=data["description"],
            prompt=data["prompt"],
            tags=data.get("tags", []),
            created_by=data.get("created_by", "user"),
        )

        return prompt
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}",
        )


@app.put("/api/admin/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, data: Dict[str, Any]):
    """
    Update an existing prompt (creates new version).

    Args:
        prompt_id: The unique identifier for the prompt
        data: Fields to update (name, description, prompt, tags)

    Returns:
        Updated prompt data with new version
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()

        prompt = prompt_service.update_prompt(
            prompt_id=prompt_id,
            name=data.get("name"),
            description=data.get("description"),
            prompt=data.get("prompt"),
            tags=data.get("tags"),
            updated_by=data.get("updated_by", "user"),
        )

        return prompt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt: {str(e)}",
        )


@app.delete("/api/admin/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """
    Delete a prompt.

    Args:
        prompt_id: The unique identifier for the prompt

    Returns:
        Success confirmation
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()

        success = prompt_service.delete_prompt(prompt_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt '{prompt_id}' not found",
            )

        return {"status": "success", "message": f"Prompt '{prompt_id}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt: {str(e)}",
        )


@app.post("/api/admin/prompts/{prompt_id}/toggle")
async def toggle_prompt_active(prompt_id: str):
    """
    Toggle active status of a prompt.

    Args:
        prompt_id: The unique identifier for the prompt

    Returns:
        Updated prompt with new active status
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()

        prompt = prompt_service.toggle_active(prompt_id)

        return prompt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle prompt: {str(e)}",
        )


@app.get("/api/admin/prompts/{prompt_id}/history")
async def get_prompt_history(prompt_id: str):
    """
    Get version history for a prompt.

    Args:
        prompt_id: The unique identifier for the prompt

    Returns:
        List of all versions with metadata
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()

        history = prompt_service.get_prompt_history(prompt_id)

        return {"prompt_id": prompt_id, "history": history}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt history: {str(e)}",
        )


@app.post("/api/admin/prompts/{prompt_id}/restore/{version}")
async def restore_prompt_version(prompt_id: str, version: int):
    """
    Restore a specific version of a prompt.

    Args:
        prompt_id: The unique identifier for the prompt
        version: Version number to restore

    Returns:
        Restored prompt data with new version number
    """
    try:
        from services.prompt_service import PromptService

        prompt_service = PromptService()

        prompt = prompt_service.restore_version(prompt_id, version)

        return prompt
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore prompt version: {str(e)}",
        )


# Mount static frontend files - MUST be after all API routes
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


# Run server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8850, reload=True)
