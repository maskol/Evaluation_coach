"""
Metrics calculation and scorecard generation service
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from api_models import HealthScorecard, MetricValue, ScopeType, TimeRange
from sqlalchemy.orm import Session


class MetricsService:
    """Service for calculating metrics and generating scorecards"""

    def generate_scorecard(
        self,
        scope: ScopeType,
        scope_id: Optional[str],
        time_range: TimeRange,
        db: Session,
    ) -> HealthScorecard:
        """
        Generate health scorecard for specified scope

        Args:
            scope: Analysis scope (portfolio, art, team)
            scope_id: Identifier for ART or team
            time_range: Time period for analysis
            db: Database session

        Returns:
            HealthScorecard with metrics and scores
        """

        # Calculate time period
        end_date = datetime.utcnow()
        if time_range == TimeRange.LAST_PI:
            start_date = end_date - timedelta(weeks=10)  # Typical PI length
        elif time_range == TimeRange.LAST_QUARTER:
            start_date = end_date - timedelta(weeks=13)
        elif time_range == TimeRange.LAST_6_MONTHS:
            start_date = end_date - timedelta(days=180)
        elif time_range == TimeRange.LAST_YEAR:
            start_date = end_date - timedelta(days=365)
        else:  # current_pi
            start_date = end_date - timedelta(weeks=5)

        # Calculate metrics based on scope
        metrics = self._calculate_metrics(scope, scope_id, start_date, end_date, db)

        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(metrics)

        # Calculate overall score
        overall_score = sum(dimension_scores.values()) / len(dimension_scores)

        # Save scorecard to database
        from database import Scorecard

        scorecard = Scorecard(
            scope=scope.value,
            scope_id=scope_id,
            time_period_start=start_date,
            time_period_end=end_date,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            metric_values={m.name: m.value for m in metrics},
        )
        db.add(scorecard)
        db.commit()
        db.refresh(scorecard)

        return HealthScorecard(
            id=scorecard.id,
            scope=scope.value,
            scope_id=scope_id,
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            metrics=metrics,
            time_period_start=start_date,
            time_period_end=end_date,
            created_at=scorecard.created_at,
        )

    def _calculate_metrics(
        self,
        scope: ScopeType,
        scope_id: Optional[str],
        start_date: datetime,
        end_date: datetime,
        db: Session,
    ) -> List[MetricValue]:
        """Calculate all relevant metrics for the scope"""

        # TODO: Implement actual metric calculations from Jira data
        # For now, return demo data

        metrics = [
            MetricValue(
                name="Flow Efficiency",
                value=67.0,
                unit="%",
                status="healthy",
                trend="up",
                benchmark={"industry": 15.0, "high_performer": 40.0},
            ),
            MetricValue(
                name="Lead Time (P50)",
                value=8.0,
                unit="days",
                status="healthy",
                trend="down",
                benchmark={"industry": 12.0, "high_performer": 6.0},
            ),
            MetricValue(
                name="WIP Ratio",
                value=1.3,
                unit="x",
                status="healthy",
                trend="stable",
                benchmark={"target": 1.5},
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

        return metrics

    def _calculate_dimension_scores(
        self, metrics: List[MetricValue]
    ) -> Dict[str, float]:
        """Calculate 5-dimension health scores"""

        # Map metrics to dimensions
        # TODO: Implement proper scoring algorithm based on metrics

        return {
            "flow": 82.0,
            "predictability": 85.0,
            "quality": 78.0,
            "stability": 89.0,
            "efficiency": 75.0,
        }
