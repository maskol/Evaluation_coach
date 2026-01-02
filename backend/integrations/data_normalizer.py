"""
Data Normalizer

Transforms raw Jira API responses into our domain models.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.models.jira_models import (
    Issue,
    IssueStatus,
    IssueType,
    Priority,
    Sprint,
    StatusTransition,
)

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Normalizes Jira API responses into domain models.

    Handles:
    - Custom field mapping
    - Date parsing
    - Status transitions extraction
    - Hierarchy relationships
    """

    def __init__(self, custom_field_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize the normalizer.

        Args:
            custom_field_mapping: Mapping of semantic names to custom field IDs
                Example: {
                    'story_points': 'customfield_10016',
                    'team': 'customfield_10020',
                    'art': 'customfield_10021',
                    'pi': 'customfield_10022',
                }
        """
        self.custom_field_mapping = (
            custom_field_mapping or self._default_field_mapping()
        )

    def _default_field_mapping(self) -> Dict[str, str]:
        """
        Default custom field mapping.

        Note: These IDs vary by Jira instance! Must be configured per deployment.
        """
        return {
            "story_points": "customfield_10016",  # Story Points (common default)
            "sprint": "customfield_10020",  # Sprint field
            "team": "customfield_10030",  # Team (custom field - example)
            "art": "customfield_10031",  # ART (custom field - example)
            "pi": "customfield_10032",  # Program Increment (custom field - example)
            "epic_link": "customfield_10014",  # Epic Link (common default)
        }

    def normalize_issue(self, raw_issue: Dict[str, Any]) -> Issue:
        """
        Normalize a raw Jira issue into our Issue model.

        Args:
            raw_issue: Raw issue dict from Jira API

        Returns:
            Normalized Issue object
        """
        fields = raw_issue.get("fields", {})

        # Extract basic fields
        key = raw_issue["key"]
        issue_id = raw_issue["id"]
        summary = fields.get("summary", "")
        description = fields.get("description")

        # Issue type
        issue_type_data = fields.get("issuetype", {})
        issue_type_name = issue_type_data.get("name", "Story")
        issue_type = self._map_issue_type(issue_type_name)

        # Status
        status_data = fields.get("status", {})
        status = status_data.get("name", "Unknown")

        # Priority
        priority_data = fields.get("priority")
        priority = self._map_priority(
            priority_data.get("name") if priority_data else None
        )

        # Hierarchy
        parent_data = fields.get("parent")
        parent_key = parent_data["key"] if parent_data else None

        epic_link_field = self.custom_field_mapping.get("epic_link")
        epic_key = fields.get(epic_link_field) if epic_link_field else None

        # People
        assignee_data = fields.get("assignee")
        assignee = assignee_data["emailAddress"] if assignee_data else None

        reporter_data = fields.get("reporter", {})
        reporter = reporter_data.get("emailAddress", "unknown")

        # Custom fields
        team_field = self.custom_field_mapping.get("team")
        team = fields.get(team_field) if team_field else None
        if team and isinstance(team, dict):
            team = team.get("value", team.get("name"))

        art_field = self.custom_field_mapping.get("art")
        art = fields.get(art_field) if art_field else None
        if art and isinstance(art, dict):
            art = art.get("value", art.get("name"))

        # Dates
        created_at = self._parse_datetime(fields.get("created"))
        updated_at = self._parse_datetime(fields.get("updated"))
        resolved_at = self._parse_datetime(fields.get("resolutiondate"))

        # Estimation
        story_points_field = self.custom_field_mapping.get("story_points")
        story_points = fields.get(story_points_field)

        original_estimate = fields.get("timeoriginalestimate")
        if original_estimate:
            original_estimate = original_estimate / 3600  # Convert seconds to hours

        time_spent = fields.get("timespent")
        if time_spent:
            time_spent = time_spent / 3600

        remaining_estimate = fields.get("timeestimate")
        if remaining_estimate:
            remaining_estimate = remaining_estimate / 3600

        # Sprint
        sprint_field = self.custom_field_mapping.get("sprint")
        sprint_data = fields.get(sprint_field)
        sprint = None
        sprint_id = None
        if sprint_data:
            # Sprint field can be a list or single value
            if isinstance(sprint_data, list) and sprint_data:
                sprint_data = sprint_data[-1]  # Get latest sprint
            if isinstance(sprint_data, dict):
                sprint = sprint_data.get("name")
                sprint_id = sprint_data.get("id")

        # PI
        pi_field = self.custom_field_mapping.get("pi")
        pi = fields.get(pi_field) if pi_field else None
        if pi and isinstance(pi, dict):
            pi = pi.get("value", pi.get("name"))

        # Status transitions (from changelog)
        status_transitions = self._extract_status_transitions(raw_issue)

        # Blocked state
        is_blocked = "blocked" in status.lower()
        blocked_reason = None
        blocked_since = None

        if is_blocked and status_transitions:
            # Find when it became blocked
            for transition in reversed(status_transitions):
                if "blocked" in transition.to_status.lower():
                    blocked_since = transition.transitioned_at
                    break

        # Dependencies (from issue links)
        blocks_issues = []
        blocked_by_issues = []

        issue_links = fields.get("issuelinks", [])
        for link in issue_links:
            link_type = link.get("type", {}).get("name", "")

            if link_type == "Blocks":
                if "outwardIssue" in link:
                    blocks_issues.append(link["outwardIssue"]["key"])
                if "inwardIssue" in link:
                    blocked_by_issues.append(link["inwardIssue"]["key"])

        # Labels and components
        labels = fields.get("labels", [])
        components = [c["name"] for c in fields.get("components", [])]
        fix_versions = [v["name"] for v in fields.get("fixVersions", [])]

        # Create Issue object
        issue = Issue(
            key=key,
            id=issue_id,
            issue_type=issue_type,
            summary=summary,
            description=description,
            status=status,
            priority=priority,
            parent_key=parent_key,
            epic_key=epic_key,
            assignee=assignee,
            reporter=reporter,
            team=team,
            art=art,
            created_at=created_at,
            updated_at=updated_at,
            resolved_at=resolved_at,
            story_points=story_points,
            original_estimate_hours=original_estimate,
            time_spent_hours=time_spent,
            remaining_estimate_hours=remaining_estimate,
            sprint=sprint,
            sprint_id=sprint_id,
            pi=pi,
            status_transitions=status_transitions,
            is_blocked=is_blocked,
            blocked_reason=blocked_reason,
            blocked_since=blocked_since,
            blocks_issues=blocks_issues,
            blocked_by_issues=blocked_by_issues,
            labels=labels,
            components=components,
            fix_versions=fix_versions,
            raw_data=raw_issue,  # Keep for debugging
        )

        return issue

    def _map_issue_type(self, jira_issue_type: str) -> IssueType:
        """Map Jira issue type name to our enum."""
        mapping = {
            "epic": IssueType.EPIC,
            "feature": IssueType.FEATURE,
            "story": IssueType.STORY,
            "user story": IssueType.STORY,
            "enabler": IssueType.ENABLER,
            "bug": IssueType.BUG,
            "task": IssueType.TASK,
            "spike": IssueType.SPIKE,
        }
        return mapping.get(jira_issue_type.lower(), IssueType.STORY)

    def _map_priority(self, jira_priority: Optional[str]) -> Optional[Priority]:
        """Map Jira priority to our enum."""
        if not jira_priority:
            return None

        mapping = {
            "highest": Priority.CRITICAL,
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
            "lowest": Priority.LOW,
        }
        return mapping.get(jira_priority.lower(), Priority.MEDIUM)

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira datetime string."""
        if not date_str:
            return None

        try:
            # Jira format: 2024-01-15T10:30:00.000+0000
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{date_str}': {e}")
            return None

    def _extract_status_transitions(
        self, raw_issue: Dict[str, Any]
    ) -> List[StatusTransition]:
        """Extract status change history from changelog."""
        transitions = []

        changelog = raw_issue.get("changelog", {})
        histories = changelog.get("histories", [])

        for history in histories:
            created = self._parse_datetime(history.get("created"))
            author = history.get("author", {}).get("emailAddress", "unknown")

            for item in history.get("items", []):
                if item.get("field") == "status":
                    from_status = item.get("fromString", "Unknown")
                    to_status = item.get("toString", "Unknown")

                    transition = StatusTransition(
                        from_status=from_status,
                        to_status=to_status,
                        transitioned_at=created,
                        transitioned_by=author,
                    )
                    transitions.append(transition)

        # Calculate duration in each status
        for i in range(len(transitions) - 1):
            current = transitions[i]
            next_transition = transitions[i + 1]

            duration = (
                next_transition.transitioned_at - current.transitioned_at
            ).total_seconds() / 3600
            current.duration_in_previous_status_hours = duration

        return transitions

    def normalize_sprint(self, raw_sprint: Dict[str, Any]) -> Sprint:
        """Normalize a sprint from Jira Agile API."""
        # TODO: Implement sprint normalization
        raise NotImplementedError("Sprint normalization not yet implemented")
