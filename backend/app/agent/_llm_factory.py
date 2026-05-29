"""
Centralised Gemini chat LLM factory with retry on transient 429 errors.

Every node in the agent calls a Gemini chat model. A 429 from any single
node aborts the whole turn. Adding LangChain's built-in `with_retry` on
the chat model wraps it with tenacity-style retry that respects the
``RetryInfo`` from Google's response.

Supports two authentication modes (auto-detected from config):
  1. GCP service-account JSON  → Vertex AI  (preferred)
  2. GOOGLE_API_KEY            → Gemini Developer API (fallback)
"""

from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings


def make_chat(*, temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """Create a Gemini chat model with quota-aware retry baked in."""
    settings = get_settings()

    if settings.use_vertex:
        # Vertex AI via GCP service-account credentials
        base = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            credentials=settings.google_credentials(),
            project=settings.gcp_project,
            location=settings.gcp_location,
            temperature=temperature,
        )
    else:
        # Gemini Developer API via API key
        base = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )

    # Retry up to 3 times on transient errors. LangChain's `with_retry`
    # uses exponential backoff — exactly what we need for a 429.
    return base.with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
        retry_if_exception_type=(Exception,),
    )


__all__ = ["make_chat"]

