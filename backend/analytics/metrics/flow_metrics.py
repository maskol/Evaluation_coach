"""
Flow Metrics Calculator

Calculates throughput, WIP, lead time, and cycle time.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from backend.models.jira_models import Issue
from backend.models.metrics_models import FlowMetrics, TimeWindow

logger = logging.getLogger(__name__)


class FlowMetricsCalculator:
    """
    Calculates flow-based metrics following principles from:
    - Kanban
    - Theory of Constraints
    - "Actionable Agile Metrics" by Daniel Vacanti

    Key metrics:
    - Throughput: Items completed per time unit
    - WIP: Average work in progress
    - Lead Time: From creation to completion
    - Cycle Time: From start to completion
    """

    def calculate(
        self,
        issues: List[Issue],
        time_window: TimeWindow,
        scope: str,
        scope_type: str,
    ) -> FlowMetrics:
        """
        Calculate flow metrics for the given issues and time window.

        Args:
            issues: List of normalized issues
            time_window: Time window for analysis
            scope: Scope name (team, ART, portfolio)
            scope_type: Type of scope

        Returns:
            FlowMetrics object with all calculated metrics
        """
        logger.info(f"Calculating flow metrics for {scope} ({len(issues)} issues)")

        # Filter issues relevant to this time window
        completed_issues = self._filter_completed_in_window(issues, time_window)

        # Calculate throughput
        throughput = (
            len(completed_issues) / time_window.duration_days
            if time_window.duration_days > 0
            else 0
        )

        # Calculate WIP (average)
        wip = self._calculate_average_wip(issues, time_window)

        # Calculate lead time metrics
        lead_times = [
            issue.lead_time_hours
            for issue in completed_issues
            if issue.lead_time_hours is not None
        ]

        lead_time_avg = statistics.mean(lead_times) if lead_times else None
        lead_time_p50 = statistics.median(lead_times) if lead_times else None
        lead_time_p85 = self._percentile(lead_times, 0.85) if lead_times else None
        lead_time_p95 = self._percentile(lead_times, 0.95) if lead_times else None
        lead_time_std_dev = (
            statistics.stdev(lead_times) if len(lead_times) > 1 else None
        )

        # Calculate cycle time metrics
        cycle_times = [
            issue.cycle_time_hours
            for issue in completed_issues
            if issue.cycle_time_hours is not None
        ]

        cycle_time_avg = statistics.mean(cycle_times) if cycle_times else None
        cycle_time_p50 = statistics.median(cycle_times) if cycle_times else None
        cycle_time_p85 = self._percentile(cycle_times, 0.85) if cycle_times else None
        cycle_time_std_dev = (
            statistics.stdev(cycle_times) if len(cycle_times) > 1 else None
        )

        # Calculate throughput by issue type
        throughput_by_type = self._calculate_throughput_by_type(completed_issues)

        # Calculate lead time by issue type
        lead_time_by_type = self._calculate_lead_time_by_type(completed_issues)

        # Create FlowMetrics object
        flow_metrics = FlowMetrics(
            scope=scope,
            scope_type=scope_type,
            time_window=time_window,
            throughput=throughput,
            wip=wip,
            lead_time_avg_hours=lead_time_avg,
            lead_time_p50_hours=lead_time_p50,
            lead_time_p85_hours=lead_time_p85,
            lead_time_p95_hours=lead_time_p95,
            lead_time_std_dev=lead_time_std_dev,
            cycle_time_avg_hours=cycle_time_avg,
            cycle_time_p50_hours=cycle_time_p50,
            cycle_time_p85_hours=cycle_time_p85,
            cycle_time_std_dev=cycle_time_std_dev,
            throughput_by_type=throughput_by_type,
            lead_time_by_type=lead_time_by_type,
        )

        logger.info(
            f"Flow metrics calculated: "
            f"Throughput={throughput:.2f} items/day, "
            f"WIP={wip:.1f}, "
            f"Lead Time P50={lead_time_p50:.1f}h, "
            f"Cycle Time P50={cycle_time_p50:.1f}h"
        )

        return flow_metrics

    def _filter_completed_in_window(
        self,
        issues: List[Issue],
        time_window: TimeWindow,
    ) -> List[Issue]:
        """
        Filter issues that were completed within the time window.

        An issue is "completed" if it has a resolved_at date.
        """
        completed = []

        for issue in issues:
            if not issue.resolved_at:
                continue

            if time_window.start_date <= issue.resolved_at <= time_window.end_date:
                completed.append(issue)

        return completed

    def _calculate_average_wip(
        self,
        issues: List[Issue],
        time_window: TimeWindow,
    ) -> Optional[float]:
        """
        Calculate average WIP (Work In Progress) over the time window.

        This uses a daily sampling approach:
        - For each day in the window, count how many issues were "in progress"
        - Average these daily counts

        An issue is "in progress" on a day if:
        - It was created before or on that day
        - It was not resolved before that day (or not resolved at all)
        """
        # Sample WIP daily
        daily_wip = []

        current_date = time_window.start_date
        while current_date <= time_window.end_date:
            wip_count = 0

            for issue in issues:
                # Was it created by this date?
                if issue.created_at > current_date:
                    continue

                # Was it already resolved before this date?
                if issue.resolved_at and issue.resolved_at < current_date:
                    continue

                # It's in progress on this date
                wip_count += 1

            daily_wip.append(wip_count)
            current_date += timedelta(days=1)

        return statistics.mean(daily_wip) if daily_wip else None

    def _percentile(self, data: List[float], percentile: float) -> Optional[float]:
        """Calculate percentile of a list of numbers."""
        if not data:
            return None

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        index = min(index, len(sorted_data) - 1)

        return sorted_data[index]

    def _calculate_throughput_by_type(
        self,
        completed_issues: List[Issue],
    ) -> Dict[str, float]:
        """Calculate throughput broken down by issue type."""
        throughput_by_type = {}

        for issue in completed_issues:
            issue_type = issue.issue_type.value
            throughput_by_type[issue_type] = throughput_by_type.get(issue_type, 0) + 1

        return throughput_by_type

    def _calculate_lead_time_by_type(
        self,
        completed_issues: List[Issue],
    ) -> Dict[str, float]:
        """Calculate average lead time by issue type."""
        lead_times_by_type: Dict[str, List[float]] = {}

        for issue in completed_issues:
            if issue.lead_time_hours is None:
                continue

            issue_type = issue.issue_type.value
            if issue_type not in lead_times_by_type:
                lead_times_by_type[issue_type] = []

            lead_times_by_type[issue_type].append(issue.lead_time_hours)

        # Calculate averages
        avg_lead_times = {}
        for issue_type, times in lead_times_by_type.items():
            avg_lead_times[issue_type] = statistics.mean(times)

        return avg_lead_times


# Example usage and demonstration
if __name__ == "__main__":
    """
    Demonstration of flow metrics calculation.

    This example shows how metrics would be calculated for a sample team.
    """
    from datetime import datetime, timedelta

    from backend.models.jira_models import IssueType, StatusTransition

    # Create sample issues
    now = datetime.utcnow()
    two_weeks_ago = now - timedelta(days=14)

    # Create 10 sample completed issues
    sample_issues = []

    for i in range(10):
        created = two_weeks_ago + timedelta(days=i * 0.5)
        resolved = created + timedelta(hours=48 + (i * 12))  # Varying lead times

        # Simulate first "In Progress" transition
        in_progress_time = created + timedelta(hours=24)

        issue = Issue(
            key=f"DEMO-{i+1}",
            id=str(i + 1),
            issue_type=IssueType.STORY if i % 3 != 0 else IssueType.BUG,
            summary=f"Sample issue {i+1}",
            status="Done",
            reporter="demo@example.com",
            created_at=created,
            updated_at=resolved,
            resolved_at=resolved,
            status_transitions=[
                StatusTransition(
                    from_status="To Do",
                    to_status="In Progress",
                    transitioned_at=in_progress_time,
                    transitioned_by="demo@example.com",
                ),
                StatusTransition(
                    from_status="In Progress",
                    to_status="Done",
                    transitioned_at=resolved,
                    transitioned_by="demo@example.com",
                ),
            ],
        )
        sample_issues.append(issue)

    # Create time window
    time_window = TimeWindow(
        start_date=two_weeks_ago, end_date=now, label="Last 2 weeks"
    )

    # Calculate metrics
    calculator = FlowMetricsCalculator()
    metrics = calculator.calculate(
        issues=sample_issues,
        time_window=time_window,
        scope="Demo Team",
        scope_type="Team",
    )

    # Print results
    print("\n" + "=" * 60)
    print("FLOW METRICS EXAMPLE")
    print("=" * 60)
    print(f"Scope: {metrics.scope}")
    print(f"Time Window: {metrics.time_window.label}")
    print(f"Duration: {metrics.time_window.duration_days:.1f} days")
    print("\n--- Throughput ---")
    print(f"Items per day: {metrics.throughput:.2f}")
    print(f"Total completed: {sum(metrics.throughput_by_type.values())}")
    print(f"By type: {metrics.throughput_by_type}")
    print("\n--- Work In Progress ---")
    print(f"Average WIP: {metrics.wip:.1f} items")
    print("\n--- Lead Time (Creation to Done) ---")
    print(f"Average: {metrics.lead_time_avg_hours:.1f} hours")
    print(f"Median (P50): {metrics.lead_time_p50_hours:.1f} hours")
    print(f"P85: {metrics.lead_time_p85_hours:.1f} hours")
    print(f"P95: {metrics.lead_time_p95_hours:.1f} hours")
    print(f"Std Dev: {metrics.lead_time_std_dev:.1f} hours")
    print("\n--- Cycle Time (Start to Done) ---")
    print(f"Average: {metrics.cycle_time_avg_hours:.1f} hours")
    print(f"Median (P50): {metrics.cycle_time_p50_hours:.1f} hours")
    print(f"P85: {metrics.cycle_time_p85_hours:.1f} hours")
    print("=" * 60)
