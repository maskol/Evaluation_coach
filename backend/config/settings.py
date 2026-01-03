"""
Application settings and configuration.

Loads configuration from environment variables using Pydantic Settings.
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

    # Jira Configuration
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_verify_ssl: bool = True

    # LLM Configuration
    openai_api_key: str
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


# Global settings instance
settings = Settings()
