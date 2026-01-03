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
        development_team: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get detailed flow lead-time data for individual issues.

        Returns lead-time broken down by workflow stages:
        - in_backlog, in_planned, in_analysis, in_progress
        - in_reviewing, in_sit, in_uat, ready_for_deployment
        - deployed, total_leadtime

        Args:
            art: Filter by ART (Agile Release Train)
            pi: Filter by PI (Program Increment)
            development_team: Filter by development team
            status: Filter by issue status

        Returns:
            List of issues with detailed lead-time metrics
        """
        params = {}
        if art:
            params["art"] = art
        if pi:
            params["pi"] = pi
        if development_team:
            params["development_team"] = development_team
        if status:
            params["status"] = status

        return self._get("/api/flow_leadtime", params=params if params else None)

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
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)
        if teams:
            params["teams"] = ",".join(teams)

        return self._get("/api/analysis/leadtime", params=params if params else None)

    def get_bottleneck_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Identify bottlenecks in the flow.

        Returns analysis showing which stages have the highest delays
        and contribute most to total lead-time.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze

        Returns:
            Bottleneck analysis data
        """
        params = {}
        if arts:
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)

        return self._get("/api/analysis/bottlenecks", params=params if params else None)

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
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)

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
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)

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
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)

        return self._get("/api/analysis/trends", params=params if params else None)

    def get_analysis_summary(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary of all analyses.

        Combines lead-time, bottlenecks, waste, throughput in one response.

        Args:
            arts: List of ARTs to analyze
            pis: List of PIs to analyze

        Returns:
            Comprehensive analysis summary
        """
        params = {}
        if arts:
            params["arts"] = ",".join(arts)
        if pis:
            params["pis"] = ",".join(pis)

        return self._get("/api/analysis/summary", params=params if params else None)

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

    def get_pip_data(self) -> List[Dict[str, Any]]:
        """
        Get PI Planning data.

        Returns:
            List of PI planning items
        """
        return self._get("/api/pip_data")

    # === Health Check ===

    def health_check(self) -> bool:
        """
        Check if the lead-time server is accessible.

        Returns:
            True if server responds, False otherwise
        """
        try:
            # Try to get filters as a health check
            self._get("/api/analysis/filters")
            return True
        except Exception as e:
            logger.warning(f"Lead-time server health check failed: {e}")
            return False
