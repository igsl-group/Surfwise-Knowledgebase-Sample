from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment (prefix ``KB_``)."""

    model_config = SettingsConfigDict(env_prefix="KB_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://kb:kb@db:5432/kb"
    app_name: str = "SurfWise-Compatible Knowledge Base"
    # Human-facing base URL of this KB (used to render absolute page links).
    public_base_url: str = "http://localhost:8080"
    # Default API token seeded on first startup (BookStack-style id:secret).
    default_token_id: str = "kb_demo_token_id"
    default_token_secret: str = "kb_demo_token_secret"
    default_token_name: str = "default-demo-token"
    seed_on_startup: bool = True
    max_upload_mb: int = 50
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
