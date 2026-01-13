"""
Application settings and configuration.

Loads configuration from environment variables using Pydantic Settings.

Current Data Sources:
- DL Webb App API (localhost:8000): Primary source for all metrics
- Jira: Optional, not currently used (can be added via MCP later)
"""

from typing import Dict, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Jira Configuration (OPTIONAL - not currently required)
    # Can be configured later for direct Jira access via MCP
    jira_base_url: str = "https://your-jira.atlassian.net"
    jira_email: str = "your-email@company.com"
    jira_api_token: str = "optional-token"
    jira_verify_ssl: bool = True

    # LLM Configuration
    openai_api_key: str = ""  # Can be empty, set via .env file
    openai_model: str = "gpt-4-turbo-preview"
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./data/evaluation_coach.db"

    # Lead-Time Data Server (DL Webb App)
    leadtime_server_url: str = "http://localhost:8000"
    leadtime_server_enabled: bool = True
    leadtime_server_timeout: int = 30

    # Vector Store
    vector_store_path: str = "./data/vector_store"
    embedding_model: str = "text-embedding-3-small"

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    enable_cors: bool = True

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "evaluation-coach"

    # Custom Field Mapping
    jira_custom_field_story_points: str = "customfield_10016"
    jira_custom_field_sprint: str = "customfield_10020"
    jira_custom_field_epic_link: str = "customfield_10014"
    jira_custom_field_team: Optional[str] = "customfield_10030"
    jira_custom_field_art: Optional[str] = "customfield_10031"
    jira_custom_field_pi: Optional[str] = "customfield_10032"

    # Cache Configuration
    cache_ttl_seconds: int = 3600
    enable_cache: bool = True

    # Analysis Thresholds (configurable per organization)
    # These thresholds determine what counts as "exceeding threshold" in bottleneck analysis

    # Feature-level thresholds
    bottleneck_threshold_days: float = 7.0  # Default: 7 days for all feature stages
    planning_accuracy_threshold_pct: float = 70.0  # Default: 70% planning accuracy

    # Story-level thresholds
    story_bottleneck_threshold_days: float = 3.0  # Default: 3 days for all story stages

    # Strategic Targets for Feature Lead-Time (days)
    leadtime_target_2026: Optional[float] = None  # Target for 2026
    leadtime_target_2027: Optional[float] = None  # Target for 2027
    leadtime_target_true_north: Optional[float] = None  # True North (long-term goal)

    # Strategic Targets for Planning Accuracy (%)
    planning_accuracy_target_2026: Optional[float] = None  # Target for 2026
    planning_accuracy_target_2027: Optional[float] = None  # Target for 2027
    planning_accuracy_target_true_north: Optional[float] = None  # True North

    # Feature stage-specific thresholds (optional overrides)
    # If not set, uses bottleneck_threshold_days for all feature stages
    threshold_in_backlog: Optional[float] = None
    threshold_in_analysis: Optional[float] = None
    threshold_in_planned: Optional[float] = None
    threshold_in_progress: Optional[float] = None
    threshold_in_reviewing: Optional[float] = None
    threshold_ready_for_sit: Optional[float] = None
    threshold_in_sit: Optional[float] = None
    threshold_ready_for_uat: Optional[float] = None
    threshold_in_uat: Optional[float] = None
    threshold_ready_for_deployment: Optional[float] = None

    # Story stage-specific thresholds (optional overrides)
    # If not set, uses story_bottleneck_threshold_days for all story stages
    story_threshold_refinement: Optional[float] = None
    story_threshold_ready_for_development: Optional[float] = None
    story_threshold_in_development: Optional[float] = None
    story_threshold_in_review: Optional[float] = None
    story_threshold_ready_for_test: Optional[float] = None
    story_threshold_in_testing: Optional[float] = None
    story_threshold_ready_for_deployment: Optional[float] = None

    # Feature Status Filtering
    # List of feature statuses to exclude from analysis (e.g., ['Cancelled', 'On Hold'])
    excluded_feature_statuses: str = ""  # Comma-separated list

    @property
    def custom_field_mapping(self) -> Dict[str, str]:
        """Get custom field mapping dictionary."""
        mapping = {
            "story_points": self.jira_custom_field_story_points,
            "sprint": self.jira_custom_field_sprint,
            "epic_link": self.jira_custom_field_epic_link,
        }

        if self.jira_custom_field_team:
            mapping["team"] = self.jira_custom_field_team
        if self.jira_custom_field_art:
            mapping["art"] = self.jira_custom_field_art
        if self.jira_custom_field_pi:
            mapping["pi"] = self.jira_custom_field_pi

        return mapping

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"

    def get_stage_threshold(self, stage: str) -> float:
        """
        Get threshold for a specific feature stage.

        Returns stage-specific threshold if configured, otherwise returns default.

        Args:
            stage: Stage name (e.g., 'in_progress', 'in_backlog')

        Returns:
            Threshold in days for the specified feature stage
        """
        threshold_attr = f"threshold_{stage}"
        stage_threshold = getattr(self, threshold_attr, None)
        return (
            stage_threshold
            if stage_threshold is not None
            else self.bottleneck_threshold_days
        )

    def get_story_stage_threshold(self, stage: str) -> float:
        """
        Get threshold for a specific story stage.

        Returns stage-specific threshold if configured, otherwise returns default.

        Args:
            stage: Stage name (e.g., 'in_development', 'refinement')

        Returns:
            Threshold in days for the specified story stage
        """
        threshold_attr = f"story_threshold_{stage}"
        stage_threshold = getattr(self, threshold_attr, None)
        return (
            stage_threshold
            if stage_threshold is not None
            else self.story_bottleneck_threshold_days
        )


# Global settings instance
settings = Settings()
