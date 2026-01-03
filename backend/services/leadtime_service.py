"""
Lead-Time Data Service

Provides a high-level interface for accessing and analyzing lead-time data
from the external DL Webb App server.
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add backend to path for imports
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from config.settings import settings
from integrations.leadtime_client import LeadTimeClient

logger = logging.getLogger(__name__)


class LeadTimeService:
    """
    Service for accessing and enriching lead-time data.

    This service acts as a facade to the LeadTimeClient, providing
    higher-level operations and caching if needed.
    """

    def __init__(self):
        """Initialize the lead-time service."""
        self.client = LeadTimeClient(
            base_url=settings.leadtime_server_url,
            timeout=settings.leadtime_server_timeout,
        )
        self._enabled = settings.leadtime_server_enabled

    def is_available(self) -> bool:
        """
        Check if the lead-time server is available.

        Returns:
            True if server is enabled and responding
        """
        if not self._enabled:
            logger.debug("Lead-time server is disabled in settings")
            return False

        return self.client.health_check()

    # === Core Lead-Time Data ===

    def get_feature_leadtime_data(
        self,
        art: Optional[str] = None,
        pi: Optional[str] = None,
        team: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get detailed lead-time data for features.

        Args:
            art: Filter by ART
            pi: Filter by PI
            team: Filter by development team

        Returns:
            List of features with stage-by-stage lead-time breakdown
        """
        if not self._enabled:
            logger.warning("Lead-time service is disabled")
            return []

        try:
            return self.client.get_flow_leadtime(art=art, pi=pi, development_team=team)
        except Exception as e:
            logger.error(f"Failed to fetch lead-time data: {e}")
            return []

    def get_leadtime_statistics(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
        teams: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get statistical analysis of lead-time.

        Returns comprehensive statistics including mean, median, percentiles
        for each workflow stage.

        Args:
            arts: Filter by ARTs
            pis: Filter by PIs
            teams: Filter by teams

        Returns:
            Statistical analysis of lead-time data
        """
        if not self._enabled:
            logger.warning("Lead-time service is disabled")
            return {}

        try:
            return self.client.get_leadtime_analysis(arts=arts, pis=pis, teams=teams)
        except Exception as e:
            logger.error(f"Failed to fetch lead-time statistics: {e}")
            return {}

    def get_comprehensive_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive analysis including lead-time, bottlenecks, and waste.

        Args:
            arts: Filter by ARTs
            pis: Filter by PIs

        Returns:
            Comprehensive analysis summary
        """
        if not self._enabled:
            logger.warning("Lead-time service is disabled")
            return {}

        try:
            return self.client.get_analysis_summary(arts=arts, pis=pis)
        except Exception as e:
            logger.error(f"Failed to fetch comprehensive analysis: {e}")
            return {}

    # === Bottleneck Analysis ===

    def identify_bottlenecks(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Identify workflow bottlenecks.

        Analyzes which stages have the highest delays and impact on total lead-time.

        Args:
            arts: Filter by ARTs
            pis: Filter by PIs

        Returns:
            Bottleneck analysis with recommendations
        """
        if not self._enabled:
            return {"bottlenecks": [], "message": "Lead-time service is disabled"}

        try:
            return self.client.get_bottleneck_analysis(arts=arts, pis=pis)
        except Exception as e:
            logger.error(f"Failed to identify bottlenecks: {e}")
            return {"bottlenecks": [], "error": str(e)}

    def get_planning_accuracy(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get planning accuracy metrics.

        Shows commitment vs delivery, including:
        - Overall planning accuracy
        - Revised planning accuracy (with scope changes)
        - PI-by-PI breakdown
        - Predictability score

        Args:
            arts: Filter by ARTs
            pis: Filter by PIs

        Returns:
            Planning accuracy analysis
        """
        if not self._enabled:
            return {
                "planning_accuracy": 0,
                "message": "Lead-time service is disabled",
            }

        try:
            return self.client.get_planning_accuracy_analysis(arts=arts, pis=pis)
        except Exception as e:
            logger.error(f"Failed to get planning accuracy: {e}")
            return {"planning_accuracy": 0, "error": str(e)}

    def analyze_waste(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze waste in the development process.

        Args:
            arts: Filter by ARTs
            pis: Filter by PIs

        Returns:
            Waste analysis data
        """
        if not self._enabled:
            return {"waste": [], "message": "Lead-time service is disabled"}

        try:
            return self.client.get_waste_analysis(arts=arts, pis=pis)
        except Exception as e:
            logger.error(f"Failed to analyze waste: {e}")
            return {"waste": [], "error": str(e)}

    # === Throughput and Trends ===

    def get_throughput_metrics(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get throughput metrics showing delivery rate.

        Args:
            arts: Filter by ARTs
            pis: Filter by PIs

        Returns:
            Throughput metrics
        """
        if not self._enabled:
            return {}

        try:
            return self.client.get_throughput_analysis(arts=arts, pis=pis)
        except Exception as e:
            logger.error(f"Failed to get throughput metrics: {e}")
            return {}

    def get_trend_analysis(
        self,
        arts: Optional[List[str]] = None,
        pis: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get trend analysis over time.

        Args:
            arts: Filter by ARTs
            pis: Filter by PIs

        Returns:
            Trend analysis data
        """
        if not self._enabled:
            return {}

        try:
            return self.client.get_trends_analysis(arts=arts, pis=pis)
        except Exception as e:
            logger.error(f"Failed to get trend analysis: {e}")
            return {}

    # === Filter Options ===

    def get_available_filters(self) -> Dict[str, List[str]]:
        """
        Get all available filter values from the lead-time system.

        Returns:
            Dictionary with available ARTs, PIs, Teams, etc.
        """
        if not self._enabled:
            return {}

        try:
            return self.client.get_available_filters()
        except Exception as e:
            logger.error(f"Failed to get available filters: {e}")
            return {}

    # === Enrichment Methods ===

    def enrich_jira_issues_with_leadtime(
        self, issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich Jira issues with lead-time data from external server.

        Matches issues by key and adds lead-time metrics.

        Args:
            issues: List of Jira issues

        Returns:
            Issues enriched with lead-time data
        """
        if not self._enabled or not issues:
            return issues

        try:
            # Get all lead-time data
            leadtime_data = self.client.get_flow_leadtime()

            # Create lookup dictionary by issue key
            leadtime_by_key = {item["issue_key"]: item for item in leadtime_data}

            # Enrich issues
            enriched_issues = []
            for issue in issues:
                enriched_issue = issue.copy()
                issue_key = issue.get("issue_key") or issue.get("key")

                if issue_key and issue_key in leadtime_by_key:
                    leadtime_info = leadtime_by_key[issue_key]
                    enriched_issue["leadtime"] = {
                        "total": leadtime_info.get("total_leadtime"),
                        "in_backlog": leadtime_info.get("in_backlog"),
                        "in_planned": leadtime_info.get("in_planned"),
                        "in_analysis": leadtime_info.get("in_analysis"),
                        "in_progress": leadtime_info.get("in_progress"),
                        "in_reviewing": leadtime_info.get("in_reviewing"),
                        "in_sit": leadtime_info.get("in_sit"),
                        "in_uat": leadtime_info.get("in_uat"),
                        "ready_for_deployment": leadtime_info.get(
                            "ready_for_deployment"
                        ),
                        "deployed": leadtime_info.get("deployed"),
                    }

                enriched_issues.append(enriched_issue)

            logger.info(
                f"Enriched {len([i for i in enriched_issues if 'leadtime' in i])} "
                f"issues with lead-time data"
            )
            return enriched_issues

        except Exception as e:
            logger.error(f"Failed to enrich issues with lead-time: {e}")
            return issues

    def get_summary_for_coaching(
        self, art: Optional[str] = None, pi: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a coaching-friendly summary of lead-time data.

        Combines multiple analyses into actionable insights for coaching.

        Args:
            art: Focus on specific ART
            pi: Focus on specific PI

        Returns:
            Coaching summary with key insights
        """
        if not self._enabled:
            return {
                "available": False,
                "message": "Lead-time data service is not available",
            }

        try:
            arts = [art] if art else None
            pis = [pi] if pi else None

            # Gather multiple analyses
            leadtime_stats = self.get_leadtime_statistics(arts=arts, pis=pis)
            bottlenecks = self.identify_bottlenecks(arts=arts, pis=pis)
            waste = self.analyze_waste(arts=arts, pis=pis)
            throughput = self.get_throughput_metrics(arts=arts, pis=pis)

            return {
                "available": True,
                "scope": {"art": art, "pi": pi},
                "leadtime_statistics": leadtime_stats,
                "bottlenecks": bottlenecks,
                "waste_analysis": waste,
                "throughput": throughput,
                "data_source": "DL Webb App Lead-Time Server",
            }
        except Exception as e:
            logger.error(f"Failed to generate coaching summary: {e}")
            return {
                "available": False,
                "error": str(e),
            }


# Global service instance
leadtime_service = LeadTimeService()
