"""
Lead-Time Data Server Client

Handles communication with the external lead-time analysis server.
This client fetches flow metrics and lead-time data from the DL Webb App backend.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class LeadTimeClient:
    """
    Client for accessing lead-time and flow metrics from external server.

    The external server (DL Webb App) contains comprehensive feature lead-time data
    including stage-by-stage metrics, bottleneck analysis, and throughput data.

    Example usage:
        >>> client = LeadTimeClient(base_url="http://localhost:8000")
        >>> leadtime_data = client.get_flow_leadtime(art="ACEART", pi="21Q4")
        >>> analysis = client.get_leadtime_analysis(arts=["ACEART"])
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """
        Initialize lead-time client.

        Args:
            base_url: Base URL of the lead-time server (default: http://localhost:8000)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._client = httpx.Client(
            timeout=timeout,
            verify=verify_ssl,
            follow_redirects=True,
        )

    def __del__(self):
        """Close the HTTP client on cleanup."""
        if hasattr(self, "_client"):
            self._client.close()

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make a GET request to the lead-time server.

        Args:
            endpoint: API endpoint path (e.g., '/api/flow_leadtime')
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        try:
            logger.debug(f"GET {url} with params: {params}")
            response = self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Request failed to {url}: {e}")
            raise

    # === Flow Lead-Time Data ===

    def get_flow_leadtime(
        self,
        art: Optional[str] = None,
        pi: Optional[str] = None,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        development_team: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get detailed flow lead-time data for individual issues.

        Returns lead-time broken down by workflow stages:
        - in_backlog, in_planned, in_analysis, in_progress
        - in_reviewing, in_sit, in_uat, ready_for_deployment
        - deployed, total_leadtime

        Args:
            art: Filter by ART (Agile Release Train) - single value
            pi: Filter by PI (Program Increment) - single value
            arts: Filter by multiple ARTs - list
            pis: Filter by multiple PIs - list
            development_team: Filter by development team
            status: Filter by issue status
            limit: Maximum number of records to return

        Returns:
            List of issues with detailed lead-time metrics
        """
        params = {}
        if arts:
            params["art"] = arts
        elif art:
            params["art"] = art
        if pis:
            params["pi"] = pis
        elif pi:
            params["pi"] = pi
        if development_team:
            params["development_team"] = development_team
        if status:
            params["status"] = status
        if limit:
            params["limit"] = str(limit)

        return self._get("/api/flow_leadtime", params=params if params else None)

    def get_story_flow_leadtime(
        self,
        art: Optional[str] = None,
        pi: Optional[str] = None,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        development_team: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get detailed flow lead-time data for user stories.

        Returns lead-time broken down by workflow stages:
        - refinement, ready_for_development, in_development
        - in_review, ready_for_test, in_testing
        - ready_for_deployment, deployed, total_leadtime

        Args:
            art: Filter by ART (Agile Release Train) - single value
            pi: Filter by PI (Program Increment) - single value
            arts: Filter by multiple ARTs - list
            pis: Filter by multiple PIs - list
            development_team: Filter by development team
            status: Filter by issue status
            limit: Maximum number of records to return

        Returns:
            List of user stories with detailed lead-time metrics
        """
        params = {}
        if arts:
            params["art"] = arts
        elif art:
            params["art"] = art
        if pis:
            params["pi"] = pis
        elif pi:
            params["pi"] = pi
        if development_team:
            params["development_team"] = development_team
        if status:
            params["status"] = status
        if limit:
            params["limit"] = str(limit)

        return self._get("/api/story_flow_leadtime", params=params if params else None)

    def get_pip_data(
        self,
        art: Optional[str] = None,
        pi: Optional[str] = None,
        team: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get PI planning data (commitment vs delivery).

        Returns planning data showing:
        - planned_committed: Features planned and committed
        - planned_uncommitted: Features planned but not committed
        - plc_delivery: Planned committed delivered (1=yes, 0=no)
        - Issue keys and ARTs

        Args:
            art: Filter by ART
            pi: Filter by PI
            team: Filter by team name
            limit: Maximum number of records to return

        Returns:
            List of planning/delivery records
        """
        params = {}
        if art:
            params["art"] = art
        if pi:
            params["pi"] = pi
        if team:
            params["development_team"] = team
        if limit:
            params["limit"] = str(limit)

        return self._get("/api/pip_data", params=params if params else None)

    def get_leadtime_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        teams: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get statistical analysis of lead-time across stages.

        Returns comprehensive statistics including:
        - Mean, median, min, max for each workflow stage
        - Standard deviation and percentiles (p85, p95)
        - Counts of items per stage

        Args:
            arts: List of ARTs to include
            pis: List of PIs to include
            teams: List of teams to include

        Returns:
            Dictionary with stage_statistics and overall metrics
        """
        params = {}
        if arts:
            params["art"] = ",".join(arts)
        if pis:
            params["pi"] = ",".join(pis)
        if teams:
            params["team"] = ",".join(teams)

        return self._get("/api/analysis/leadtime", params=params if params else None)

    def get_bottleneck_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        threshold_days: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Identify bottlenecks in the flow.

        Returns analysis showing which stages have the highest delays
        and contribute most to total lead-time.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze
            threshold_days: Threshold in days for identifying items exceeding limit

        Returns:
            Bottleneck analysis data
        """
        params = {}
        if arts:
            params["art"] = ",".join(arts)
        if pis:
            params["pi"] = ",".join(pis)
        if threshold_days is not None:
            params["threshold_days"] = str(threshold_days)

        return self._get("/api/analysis/bottlenecks", params=params if params else None)

    def get_planning_accuracy_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get planning accuracy metrics showing commitment vs delivery.

        Returns comprehensive planning accuracy analysis including:
        - Overall planning accuracy (committed items delivered)
        - Revised planning accuracy (including scope changes)
        - PI-by-PI breakdown
        - Predictability score

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze

        Returns:
            Planning accuracy analysis data
        """
        params = {}
        if arts:
            params["art"] = arts  # Pass as list for repeated params
        if pis:
            params["pi"] = pis  # Pass as list for repeated params

        return self._get(
            "/api/analysis/planning-accuracy", params=params if params else None
        )

    def get_waste_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze waste in the development process.

        Identifies time spent in non-value-adding activities.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze

        Returns:
            Waste analysis data
        """
        params = {}
        if arts:
            params["art"] = arts  # Pass as list for repeated params
        if pis:
            params["pi"] = pis  # Pass as list for repeated params

        return self._get("/api/analysis/waste", params=params if params else None)

    def get_throughput_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get throughput metrics showing delivery rate.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze

        Returns:
            Throughput analysis data
        """
        params = {}
        if arts:
            params["art"] = arts  # Pass as list for repeated params
        if pis:
            params["pi"] = pis  # Pass as list for repeated params

        return self._get("/api/analysis/throughput", params=params if params else None)

    def get_trends_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get trend analysis over time.

        Shows how metrics are changing across PIs.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze

        Returns:
            Trend analysis data
        """
        params = {}
        if arts:
            params["art"] = arts  # Pass as list for repeated params
        if pis:
            params["pi"] = pis  # Pass as list for repeated params

        return self._get("/api/analysis/trends", params=params if params else None)

    def get_analysis_summary(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        team: Optional[str] = None,
        threshold_days: Optional[float] = None,
        include_completed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary of all analyses.

        Combines lead-time, bottlenecks, waste, throughput in one response.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze
            team: Team name to filter by
            threshold_days: Threshold in days for identifying items exceeding limit
            include_completed: Include completed/done items in stuck_items (for historical analysis)

        Returns:
            Comprehensive analysis summary
        """
        params = {}
        if arts:
            params["art"] = arts  # Pass as list for repeated params
        if pis:
            params["pi"] = pis  # Pass as list for repeated params
        if team:
            params["development_team"] = team
        if threshold_days is not None:
            params["threshold_days"] = str(threshold_days)
        if include_completed is not None:
            params["include_completed"] = "true" if include_completed else "false"

        return self._get("/api/analysis/summary", params=params if params else None)

    # === Story-Level Analysis ===

    def get_story_analysis_summary(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        team: Optional[str] = None,
        threshold_days: Optional[float] = None,
        include_completed: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive bottleneck analysis summary for user stories.

        Returns story-level bottleneck analysis including:
        - Stage analysis for 8 story workflow stages
        - Stuck items at story level
        - WIP statistics for stories
        - Flow distribution

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze
            team: Team name to filter by
            threshold_days: Threshold in days for identifying stuck stories
            include_completed: Include completed/done items in stuck_items (for historical analysis)

        Returns:
            Story-level bottleneck analysis summary
        """
        params = {}
        if arts:
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)
        if team:
            params["team"] = team
        if threshold_days is not None:
            params["threshold_days"] = str(threshold_days)
        if include_completed is not None:
            params["include_completed"] = "true" if include_completed else "false"

        return self._get(
            "/api/story_analysis_summary", params=params if params else None
        )

    def get_story_pip_data(
        self,
        pi: str,
        art: Optional[str] = None,
        team: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get planning accuracy data for user stories.

        Returns story-level planning metrics including:
        - Planned and completed story counts
        - Story completion rate
        - Story predictability
        - Average and median story lead time
        - Story flow efficiency

        Args:
            pi: PI to analyze (required)
            art: Filter by ART
            team: Filter by team name

        Returns:
            List of story planning accuracy records
        """
        params = {"pi": pi}
        if art:
            params["art"] = art
        if team:
            params["team"] = team

        return self._get("/api/story_pip_data", params=params)

    def get_story_waste_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        team: Optional[str] = None,
        threshold_days: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze waste in story-level development process.

        Returns waste metrics including:
        - Waiting time waste for each story stage
        - Blocked stories count and duration
        - Stories exceeding threshold

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze
            team: Team name to filter by
            threshold_days: Threshold in days for identifying waste

        Returns:
            Story-level waste analysis data
        """
        params = {}
        if arts:
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)
        if team:
            params["team"] = team
        if threshold_days is not None:
            params["threshold_days"] = str(threshold_days)

        return self._get("/api/story_waste_analysis", params=params if params else None)

    def get_throughput_data(
        self,
        art: Optional[str] = None,
        pi: Optional[str] = None,
        team: Optional[str] = None,
        limit: int = 10000,
    ) -> List[Dict[str, Any]]:
        """
        Get throughput data - features with status DONE (delivered features).

        Args:
            art: Optional ART filter
            pi: Optional PI filter
            team: Optional team filter
            limit: Maximum number of records to return

        Returns:
            List of delivered features with throughput=1
        """
        params = {"limit": limit}
        if art:
            params["art"] = art
        if pi:
            params["pi"] = pi
        if team:
            params["team"] = team

        return self._get("/api/leadtime_thr_data", params=params if params else None)

    def get_available_filters(self) -> Dict[str, List[str]]:
        """
        Get all available filter values (ARTs, PIs, Teams, etc.).

        Returns:
            Dictionary with lists of available values for filtering
        """
        return self._get("/api/analysis/filters")

    # === Portfolio and Team Data ===

    def get_arts(self) -> List[Dict[str, Any]]:
        """
        Get all Agile Release Trains (ARTs) from the system.

        Returns:
            List of ART definitions
        """
        return self._get("/api/arts/")

    def get_teams(self) -> List[Dict[str, Any]]:
        """
        Get all teams from the system.

        Returns:
            List of team definitions
        """
        return self._get("/api/teams/")

    def get_feature_data(self) -> List[Dict[str, Any]]:
        """
        Get all feature data.

        Returns:
            List of features with their data
        """
        return self._get("/api/feature_data")

    def get_feature_wip_statistics(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate WIP statistics for Features only (excludes Stories/Tasks).

        Uses the flow_leadtime table which contains only Feature-level items.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze

        Returns:
            WIP statistics by stage for Features only
        """
        params = {}
        if arts:
            params["art"] = arts
        if pis:
            params["pi"] = pis

        features = self._get("/api/flow_leadtime", params=params if params else None)

        # Define active stages (exclude backlog, analysis, planned)
        active_stages = {
            "In Progress": "in_progress",
            "Reviewing": "in_reviewing",
            "Ready for SIT": "ready_for_sit",
            "In SIT": "in_sit",
            "Ready for UAT": "ready_for_uat",
            "In UAT": "in_uat",
            "Ready for Deployment": "ready_for_deployment",
        }

        # Count features by status
        wip_by_stage = {}
        for stage_name, stage_key in active_stages.items():
            count = sum(1 for f in features if f.get("status") == stage_name)
            if count > 0:
                wip_by_stage[stage_key] = {"total_items": count}

        return wip_by_stage

    # === Health Check ===

    def health_check(self) -> bool:
        """
        Check if the lead-time server is accessible.

        Returns:
            True if server responds, False otherwise
        """
        try:
            # Use a known endpoint to check connectivity
            response = self._client.get(f"{self.base_url}/api/arts/", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
