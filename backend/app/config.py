"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All configuration for the AstroAgent backend."""

    # Google AI
    google_api_key: str = ""
    llm_model: str = "gemini-3-flash-preview"
    embedding_model: str = "text-embedding-004"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""

    # Qdrant Cloud
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "astrophage_knowledge"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_expiry_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Server
    host: str = "0.0.0.0"
    port: int = 7860

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for app settings."""
    return Settings()
