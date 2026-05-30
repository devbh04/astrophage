"""
Centralised Gemini chat LLM factory.

Two backends are supported:
- **Vertex AI** via GCP service account — used when ``GCP_CREDENTIALS_PATH``
  and ``GCP_PROJECT`` are set. Quotas live with the GCP project, no daily
  free-tier cap. Production-grade.
- **Gemini Developer API** via API key — used when ``GOOGLE_API_KEY`` is
  set and Vertex isn't. Free-tier with daily request caps.

Returns a raw chat-model instance so callers can ``bind_tools(...)`` first
and then ``with_retry(...)``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from app.config import get_settings


logger = logging.getLogger(__name__)


def _resolve_credentials_path(raw: str) -> str:
    """Allow relative paths in .env (resolved against backend/)."""
    if not raw:
        return ""
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    backend_root = Path(__file__).resolve().parents[2]
    return str((backend_root / raw).resolve())


def _make_vertex_chat(*, temperature: float):
    from langchain_google_vertexai import ChatVertexAI  # type: ignore
    from google.oauth2 import service_account  # type: ignore

    settings = get_settings()
    creds_path = _resolve_credentials_path(settings.gcp_credentials_path)
    if not Path(creds_path).is_file():
        raise RuntimeError(
            f"GCP_CREDENTIALS_PATH points to a missing file: {creds_path!r}"
        )
    if not settings.gcp_project:
        raise RuntimeError("GCP_PROJECT is empty in backend/.env")

    credentials = service_account.Credentials.from_service_account_file(
        creds_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    logger.info(
        "LLM: Vertex AI · project=%s location=%s model=%s",
        settings.gcp_project,
        settings.gcp_location,
        settings.llm_model,
    )

    return ChatVertexAI(
        model=settings.llm_model,
        project=settings.gcp_project,
        location=settings.gcp_location,
        credentials=credentials,
        temperature=temperature,
    )


def _make_genai_chat(*, temperature: float):
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore

    settings = get_settings()
    api_key = (settings.google_api_key or "").strip()
    if not api_key:
        api_key = (os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not api_key:
        api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "No Gemini credentials found. Set either GCP_CREDENTIALS_PATH + "
            "GCP_PROJECT (Vertex AI) or GOOGLE_API_KEY (developer API) in "
            "backend/.env."
        )

    logger.info("LLM: Gemini Developer API · model=%s", settings.llm_model)

    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        api_key=api_key,
        temperature=temperature,
    )


def make_chat(*, temperature: float = 0.7):
    """
    Create a chat model. Caller may ``bind_tools(...)`` /
    ``with_retry(...)`` / pipe further. Order matters because
    ``RunnableRetry`` doesn't expose ``bind_tools``.
    """
    settings = get_settings()
    use_vertex = bool(
        settings.gcp_credentials_path
        and Path(_resolve_credentials_path(settings.gcp_credentials_path)).is_file()
    )
    if use_vertex:
        return _make_vertex_chat(temperature=temperature)
    return _make_genai_chat(temperature=temperature)


__all__ = ["make_chat"]
