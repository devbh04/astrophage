"""
get_family_profile — fetch a saved family member's birth details + computed
chart by relationship (spouse, mother, son…) or by name.

User scoping: the active user is bound at request time in
``app.agent._user_context``; this tool will only ever return rows belonging
to that user, so the LLM cannot accidentally surface another account's
data even if it hallucinates a name.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agent._user_context import get_current_user_id
from app.db.queries import get_profiles_by_user

logger = logging.getLogger(__name__)


def _normalize(s: Any) -> str:
    return (s or "").strip().lower()


def _profile_payload(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "relationship": row.get("relationship"),
        "birth_date": row.get("birth_date"),
        "birth_time": row.get("birth_time"),
        "place_name": row.get("place_name"),
        "lat": row.get("lat"),
        "lng": row.get("lng"),
        "timezone": row.get("timezone"),
        "natal_chart": row.get("computed_chart"),
        "active_dashas": row.get("computed_dashas"),
    }


async def get_family_profile(
    relationship: str | None = None,
    name: str | None = None,
) -> dict:
    """
    Look up one of the user's saved family-vault profiles.

    Match priority:
      1. exact relationship match (case-insensitive)
      2. exact name match (case-insensitive)
      3. substring match on name
      4. substring match on relationship

    Returns ``{found: bool, profile?: dict, candidates?: [...]}`` so the
    LLM can re-ask if there's ambiguity instead of guessing.
    """
    user_id = get_current_user_id()
    if not user_id:
        logger.warning("get_family_profile called without active user context")
        return {"found": False, "error": "No active user."}

    if not relationship and not name:
        return {"found": False, "error": "Provide a relationship or a name."}

    try:
        profiles = await get_profiles_by_user(user_id)
    except Exception as exc:
        logger.warning("get_family_profile: failed to load profiles: %s", exc)
        return {"found": False, "error": "Could not load family vault."}

    rel = _normalize(relationship)
    nm = _normalize(name)

    # 1. exact relationship
    if rel:
        for row in profiles:
            if _normalize(row.get("relationship")) == rel:
                return {"found": True, "profile": _profile_payload(row)}

    # 2. exact name
    if nm:
        for row in profiles:
            if _normalize(row.get("name")) == nm:
                return {"found": True, "profile": _profile_payload(row)}

    # 3 & 4. substring
    matches: list[dict] = []
    for row in profiles:
        rname = _normalize(row.get("name"))
        rrel = _normalize(row.get("relationship"))
        if nm and nm in rname:
            matches.append(row)
            continue
        if rel and rel in rrel:
            matches.append(row)

    if len(matches) == 1:
        return {"found": True, "profile": _profile_payload(matches[0])}
    if len(matches) > 1:
        return {
            "found": False,
            "ambiguous": True,
            "candidates": [
                {
                    "name": r.get("name"),
                    "relationship": r.get("relationship"),
                    "birth_date": r.get("birth_date"),
                }
                for r in matches[:8]
            ],
        }

    return {
        "found": False,
        "candidates": [
            {
                "name": r.get("name"),
                "relationship": r.get("relationship"),
            }
            for r in profiles[:30]
        ],
    }


__all__ = ["get_family_profile"]
