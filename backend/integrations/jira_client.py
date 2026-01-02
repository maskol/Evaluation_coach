"""
Jira REST API Client

Handles all communication with Jira Cloud/Server REST API.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Client for Jira REST API.

    Supports both Jira Cloud and Jira Server/Data Center.

    Example usage:
        >>> from backend.config.settings import Settings
        >>> settings = Settings()
        >>> client = JiraClient(
        ...     base_url=settings.jira_base_url,
        ...     email=settings.jira_email,
        ...     api_token=settings.jira_api_token
        ... )
        >>> issues = client.search_issues('project = PROJ AND updated >= "2026-01-01"')
    """

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize Jira client.

        Args:
            base_url: Jira instance URL (e.g., 'https://company.atlassian.net')
            email: User email for authentication
            api_token: API token (get from https://id.atlassian.com/manage/api-tokens)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Create httpx client with auth
        self.client = httpx.Client(
            auth=(email, api_token),
            verify=verify_ssl,
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    def search_issues(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        expand: Optional[List[str]] = None,
        max_results: int = 100,
        start_at: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search for issues using JQL (Jira Query Language).

        This method handles pagination automatically to fetch all results.

        Args:
            jql: JQL query string
            fields: List of fields to return (None = all fields)
            expand: List of fields to expand (e.g., 'changelog', 'renderedFields')
            max_results: Number of results per page (max 100)
            start_at: Starting index for pagination

        Returns:
            List of issue dictionaries

        Example:
            >>> issues = client.search_issues(
            ...     jql='project = PROJ AND status = "In Progress"',
            ...     fields=['key', 'summary', 'status', 'assignee'],
            ...     expand=['changelog']
            ... )
        """
        all_issues = []

        # Default fields if none specified
        if fields is None:
            fields = [
                "key",
                "id",
                "summary",
                "description",
                "issuetype",
                "status",
                "priority",
                "created",
                "updated",
                "resolved",
                "assignee",
                "reporter",
                "labels",
                "components",
                "customfield_*",  # All custom fields
            ]

        if expand is None:
            expand = ["changelog"]  # Always get status history

        while True:
            # Build request payload
            payload = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": min(max_results, 100),  # Jira max is 100
                "fields": fields,
                "expand": expand,
            }

            logger.debug(f"Searching issues: {jql} (startAt={start_at})")

            # Make request
            response = self.client.post(
                f"{self.base_url}/rest/api/3/search",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            # Check if there are more results
            total = data.get("total", 0)
            start_at += len(issues)

            logger.info(f"Fetched {len(all_issues)}/{total} issues")

            if start_at >= total:
                break

        return all_issues

    def get_issue(
        self, issue_key: str, expand: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get a single issue by key.

        Args:
            issue_key: Issue key (e.g., 'PROJ-123')
            expand: Fields to expand

        Returns:
            Issue dictionary
        """
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        response = self.client.get(
            f"{self.base_url}/rest/api/3/issue/{issue_key}",
            params=params,
        )
        response.raise_for_status()

        return response.json()

    def get_sprints_for_board(
        self,
        board_id: str,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get sprints for a board.

        Args:
            board_id: Board ID
            state: Filter by state ('active', 'closed', 'future')

        Returns:
            List of sprint dictionaries
        """
        params = {}
        if state:
            params["state"] = state

        all_sprints = []
        start_at = 0

        while True:
            params["startAt"] = start_at
            params["maxResults"] = 50

            response = self.client.get(
                f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            sprints = data.get("values", [])
            all_sprints.extend(sprints)

            if data.get("isLast", True):
                break

            start_at += len(sprints)

        return all_sprints

    def get_issues_for_sprint(
        self,
        sprint_id: str,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all issues for a specific sprint.

        Args:
            sprint_id: Sprint ID
            fields: Fields to return

        Returns:
            List of issue dictionaries
        """
        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        all_issues = []
        start_at = 0

        while True:
            params["startAt"] = start_at
            params["maxResults"] = 100

            response = self.client.get(
                f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            total = data.get("total", 0)
            start_at += len(issues)

            if start_at >= total:
                break

        return all_issues

    def get_board_configuration(self, board_id: str) -> Dict[str, Any]:
        """Get board configuration including columns and workflow."""
        response = self.client.get(
            f"{self.base_url}/rest/agile/1.0/board/{board_id}/configuration"
        )
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    """
    Example of how to use the Jira client.

    Before running, set environment variables:
    - JIRA_BASE_URL
    - JIRA_EMAIL
    - JIRA_API_TOKEN
    """
    import os

    # Load from environment
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")

    if not all([base_url, email, api_token]):
        print(
            "Please set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN environment variables"
        )
        exit(1)

    # Example: Search for recent issues
    with JiraClient(base_url, email, api_token) as client:
        # Search for issues updated in the last 30 days
        jql = "updated >= -30d ORDER BY updated DESC"

        issues = client.search_issues(
            jql=jql,
            fields=["key", "summary", "status", "updated"],
            max_results=10,  # Just first 10 for demo
        )

        print(f"Found {len(issues)} issues:")
        for issue in issues:
            key = issue["key"]
            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]
            print(f"  {key}: {summary} [{status}]")
