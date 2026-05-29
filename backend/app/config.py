"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration for the AstroAgent backend."""

    # Google AI — prefer GCP service-account auth, fall back to API key
    google_api_key: str = ""
    gcp_credentials_path: str = ""
    gcp_project: str = ""
    gcp_location: str = "us-central1"
    llm_model: str = "gemini-3-flash-preview"
    embedding_model: str = "gemini-embedding-001"

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

    @property
    def use_vertex(self) -> bool:
        """True when a GCP service-account JSON is configured."""
        return bool(self.gcp_credentials_path and Path(self.gcp_credentials_path).is_file())

    def google_credentials(self) -> Any:
        """Load google.oauth2 Credentials from the service-account JSON."""
        if not self.use_vertex:
            return None
        from google.oauth2 import service_account  # type: ignore
        return service_account.Credentials.from_service_account_file(
            self.gcp_credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for app settings."""
    return Settings()
