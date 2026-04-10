"""Configuration management for PRTG MCP server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """PRTG API settings."""

    base_url: str = "https://your-instance.my-prtg.com"
    api_token: str = ""
    timeout: float = 30.0
    max_results: int = 500

    model_config = SettingsConfigDict(
        env_prefix="PRTG_",
        env_file=".env"
    )

    def is_configured(self) -> bool:
        """Check if required credentials are set."""
        return bool(self.base_url and self.api_token)


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings for testing."""
    global _settings
    _settings = None
