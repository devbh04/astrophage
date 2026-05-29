"""
Knowledge lookup tool — vector search over Qdrant ``astrophage_knowledge``.

Embeds the query with ``text-embedding-004`` and searches the cosine-distance
collection. Returns up to ``top_k`` ``{text, source, score, chunk_id}`` records.
On any Qdrant error or unreachable network the function logs a warning and
returns ``[]`` (per design E3) — knowledge retrieval must never break the
agent.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


COLLECTION_NAME = "astrophage_knowledge"
DEFAULT_TOP_K = 5


_google_client_singleton: Any = None
_qdrant_client_singleton: Any = None


def _get_google_client() -> Any:
    global _google_client_singleton
    if _google_client_singleton is None:
        from google import genai  # type: ignore
        settings = get_settings()
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY", "")
        _google_client_singleton = genai.Client(api_key=api_key)
    return _google_client_singleton


def _get_qdrant_client() -> Any:
    global _qdrant_client_singleton
    if _qdrant_client_singleton is None:
        from qdrant_client import AsyncQdrantClient  # type: ignore
        settings = get_settings()
        url = settings.qdrant_url or os.environ.get("QDRANT_URL", "")
        api_key = settings.qdrant_api_key or os.environ.get("QDRANT_API_KEY", "")
        _qdrant_client_singleton = AsyncQdrantClient(url=url, api_key=api_key)
    return _qdrant_client_singleton


async def _embed_query(client: Any, query: str) -> list[float]:
    resp = client.models.embed_content(model="text-embedding-004", contents=[query])
    if hasattr(resp, "embeddings") and resp.embeddings:
        return list(resp.embeddings[0].values)
    if isinstance(resp, dict) and "embeddings" in resp:
        return list(resp["embeddings"][0]["values"])
    raise RuntimeError("Unexpected embed_content response shape")


def _to_qdrant_filter(filters: dict | None):
    """Build a Qdrant `Filter` object from a flat key→value mapping."""
    if not filters:
        return None
    try:
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue  # type: ignore
    except Exception:
        return None
    must = []
    for key, value in filters.items():
        must.append(FieldCondition(key=key, match=MatchValue(value=value)))
    return Filter(must=must)


async def knowledge_lookup(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    filters: dict | None = None,
    *,
    google_client: Any = None,
    qdrant_client: Any = None,
) -> list[dict]:
    """
    Embed `query`, search Qdrant, return up to `top_k` records.

    Each record has keys ``text``, ``source``, ``score``, ``chunk_id``.

    On any error (unreachable Qdrant, auth failure, malformed response) the
    function logs a warning and returns an empty list rather than raising.
    """
    if not query or not query.strip():
        return []

    try:
        gc = google_client or _get_google_client()
        vector = await _embed_query(gc, query)
    except Exception as exc:  # pragma: no cover - network path
        logger.warning("knowledge_lookup: embedding failed: %s", exc)
        return []

    try:
        qc = qdrant_client or _get_qdrant_client()
        qfilter = _to_qdrant_filter(filters)
        results = await qc.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=top_k,
            query_filter=qfilter,
        )
    except Exception as exc:
        logger.warning("knowledge_lookup: Qdrant search failed: %s", exc)
        return []

    out: list[dict] = []
    for hit in results or []:
        # Qdrant returns ScoredPoint with `id`, `score`, `payload`.
        payload = getattr(hit, "payload", None) or (hit.get("payload") if isinstance(hit, dict) else {}) or {}
        score = getattr(hit, "score", None)
        if score is None and isinstance(hit, dict):
            score = hit.get("score")
        chunk_id = getattr(hit, "id", None)
        if chunk_id is None and isinstance(hit, dict):
            chunk_id = hit.get("id")
        out.append({
            "text": payload.get("text", ""),
            "source": payload.get("source", ""),
            "score": float(score) if score is not None else 0.0,
            "chunk_id": str(chunk_id) if chunk_id is not None else "",
        })
    return out[:top_k]


__all__ = ["knowledge_lookup", "COLLECTION_NAME"]
