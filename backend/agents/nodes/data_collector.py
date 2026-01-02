"""
Data Collector Node (Node 1)

Responsibilities:
- Fetch data from Jira REST API
- Normalize Jira data into our domain models
- Cache data for efficiency
- Validate data quality
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from ..state import AgentState

logger = logging.getLogger(__name__)


def data_collector_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Data Collection from Jira.

    This node:
    1. Constructs JQL queries based on scope and time window
    2. Fetches issues, sprints, and program increments from Jira
    3. Normalizes data into our domain models
    4. Assesses data quality

    Args:
        state: Current agent state

    Returns:
        Dictionary with updates to state
    """
    logger.info(f"Starting data collection for {state['scope_type']}: {state['scope']}")

    try:
        # TODO: Import actual Jira client
        # from backend.integrations.jira_client import JiraClient
        # from backend.integrations.data_normalizer import DataNormalizer

        # Initialize updates dictionary
        updates = {
            "data_collection_timestamp": datetime.utcnow(),
        }

        # Step 1: Build JQL query based on scope
        jql_query = _build_jql_query(state)
        logger.debug(f"JQL Query: {jql_query}")

        # Step 2: Fetch issues from Jira
        # jira_client = JiraClient()
        # raw_issues = jira_client.search_issues(jql_query)

        # PLACEHOLDER: For now, return empty data
        # In real implementation, this would fetch from Jira
        raw_issues = []

        updates["raw_issues"] = raw_issues

        # Step 3: Normalize issues
        # normalizer = DataNormalizer()
        # normalized_issues = [normalizer.normalize_issue(issue) for issue in raw_issues]

        # PLACEHOLDER
        normalized_issues = []

        updates["normalized_issues"] = normalized_issues

        # Step 4: Fetch sprints if scope is Team or ART
        if state["scope_type"] in ["Team", "ART"]:
            # sprints = jira_client.get_sprints_for_board(board_id)
            # normalized_sprints = [normalizer.normalize_sprint(sprint) for sprint in sprints]

            # PLACEHOLDER
            normalized_sprints = []
            updates["sprints"] = normalized_sprints

        # Step 5: Fetch program increments if scope is ART or Portfolio
        if state["scope_type"] in ["ART", "Portfolio"]:
            # pi_data = jira_client.get_program_increments(art_name)
            # normalized_pis = [normalizer.normalize_pi(pi) for pi in pi_data]

            # PLACEHOLDER
            normalized_pis = []
            updates["program_increments"] = normalized_pis

        # Step 6: Assess data quality
        data_quality_score = _assess_data_quality(normalized_issues, state)
        updates["data_quality_score"] = data_quality_score

        if data_quality_score < 0.5:
            updates["warnings"] = [
                f"Data quality score is low ({data_quality_score:.2f}). "
                "Results may be less reliable."
            ]

        logger.info(
            f"Data collection complete. "
            f"Collected {len(normalized_issues)} issues. "
            f"Data quality: {data_quality_score:.2f}"
        )

        return updates

    except Exception as e:
        logger.error(f"Error in data collection: {e}", exc_info=True)
        return {
            "errors": [f"Data collection failed: {str(e)}"],
            "data_collection_timestamp": datetime.utcnow(),
            "data_quality_score": 0.0,
        }


def _build_jql_query(state: AgentState) -> str:
    """
    Build a JQL query based on the analysis scope and parameters.

    Args:
        state: Current agent state

    Returns:
        JQL query string
    """
    scope_type = state["scope_type"]
    scope = state["scope"]
    time_start = state["time_window_start"]
    time_end = state["time_window_end"]

    # Base query components
    query_parts = []

    # Add project filter if specified
    if state.get("jira_project_keys"):
        projects = ", ".join(state["jira_project_keys"])
        query_parts.append(f"project in ({projects})")

    # Add scope filter
    if scope_type == "Team":
        # Assuming a custom field "Team" exists in Jira
        query_parts.append(f'Team = "{scope}"')
    elif scope_type == "ART":
        # Assuming a custom field "ART" exists in Jira
        query_parts.append(f'ART = "{scope}"')
    elif scope_type == "Portfolio":
        # For portfolio, might need to query by ART membership
        query_parts.append(f'Portfolio = "{scope}"')

    # Add time window filter
    # Use updated date to capture all relevant activity
    query_parts.append(
        f'updated >= "{time_start.strftime("%Y-%m-%d")}" '
        f'AND updated <= "{time_end.strftime("%Y-%m-%d")}"'
    )

    # Add issue type filter if specified
    if state.get("include_issue_types"):
        types = ", ".join(state["include_issue_types"])
        query_parts.append(f"issuetype in ({types})")

    # Order by created date
    jql = " AND ".join(query_parts) + " ORDER BY created DESC"

    return jql


def _assess_data_quality(issues: List[Any], state: AgentState) -> float:
    """
    Assess the quality of collected data.

    Checks for:
    - Sufficient volume of issues
    - Presence of key fields (status transitions, estimates, etc.)
    - Data completeness

    Args:
        issues: List of normalized Issue objects
        state: Current agent state

    Returns:
        Quality score from 0.0 to 1.0
    """
    if not issues:
        return 0.0

    score_components = []

    # 1. Volume check (at least 10 issues for meaningful analysis)
    volume_score = min(len(issues) / 10, 1.0)
    score_components.append(volume_score)

    # 2. Field completeness
    required_fields = ["status", "created_at", "issue_type"]
    optional_but_important = [
        "story_points",
        "resolved_at",
        "status_transitions",
        "team",
    ]

    field_completeness_scores = []
    for issue in issues:
        # Check required fields
        required_present = sum(
            1 for field in required_fields if getattr(issue, field, None)
        )

        # Check optional fields
        optional_present = sum(
            1 for field in optional_but_important if getattr(issue, field, None)
        )

        issue_score = (required_present / len(required_fields)) * 0.7 + (
            optional_present / len(optional_but_important)
        ) * 0.3

        field_completeness_scores.append(issue_score)

    avg_field_completeness = sum(field_completeness_scores) / len(
        field_completeness_scores
    )
    score_components.append(avg_field_completeness)

    # 3. Status transition data (important for flow metrics)
    issues_with_transitions = sum(
        1
        for issue in issues
        if getattr(issue, "status_transitions", None)
        and len(issue.status_transitions) > 0
    )
    transition_score = issues_with_transitions / len(issues) if issues else 0
    score_components.append(transition_score)

    # Overall score (weighted average)
    weights = [0.2, 0.5, 0.3]  # Volume, field completeness, transitions
    overall_score = sum(s * w for s, w in zip(score_components, weights))

    return overall_score
