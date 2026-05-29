"""CRUD operations for all database tables using supabase-py."""

from app.db.client import get_supabase


# ── Users ───────────────────────────────────────────────────────

async def create_user(
    email: str,
    password_hash: str,
    name: str,
    default_language: str = "en",
) -> dict:
    """Insert a new user and return the created row."""
    sb = get_supabase()
    result = (
        sb.table("users")
        .insert(
            {
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "default_language": default_language,
            }
        )
        .execute()
    )
    return result.data[0] if result.data else {}


async def get_user_by_email(email: str) -> dict | None:
    """Find a user by email. Returns None if not found."""
    sb = get_supabase()
    result = (
        sb.table("users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_user_by_id(user_id: str) -> dict | None:
    """Find a user by ID. Returns None if not found."""
    sb = get_supabase()
    result = (
        sb.table("users")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def update_user(user_id: str, updates: dict) -> dict | None:
    """Update user fields. Returns updated row."""
    sb = get_supabase()
    result = (
        sb.table("users")
        .update(updates)
        .eq("id", user_id)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Birth Profiles (Family Vault) ──────────────────────────────

async def create_profile(user_id: str, profile_data: dict) -> dict:
    """Insert a new birth profile for a user."""
    sb = get_supabase()
    profile_data["user_id"] = user_id
    result = sb.table("birth_profiles").insert(profile_data).execute()
    return result.data[0] if result.data else {}


async def get_profiles_by_user(user_id: str) -> list[dict]:
    """Get all birth profiles for a user."""
    sb = get_supabase()
    result = (
        sb.table("birth_profiles")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


async def get_profile_by_id(profile_id: str) -> dict | None:
    """Get a single birth profile by ID."""
    sb = get_supabase()
    result = (
        sb.table("birth_profiles")
        .select("*")
        .eq("id", profile_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def update_profile_chart(
    profile_id: str,
    computed_chart: dict,
    computed_dashas: dict | None = None,
) -> dict | None:
    """Store computed chart (and optionally dashas) on a profile."""
    sb = get_supabase()
    updates: dict = {"computed_chart": computed_chart}
    if computed_dashas is not None:
        updates["computed_dashas"] = computed_dashas
    result = (
        sb.table("birth_profiles")
        .update(updates)
        .eq("id", profile_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def delete_profile(profile_id: str) -> bool:
    """Delete a birth profile. Returns True if deleted."""
    sb = get_supabase()
    result = (
        sb.table("birth_profiles")
        .delete()
        .eq("id", profile_id)
        .execute()
    )
    return bool(result.data)


# ── Conversations ───────────────────────────────────────────────

async def create_conversation(
    user_id: str,
    profile_id: str | None = None,
    title: str | None = None,
) -> dict:
    """Create a new conversation."""
    sb = get_supabase()
    data: dict = {"user_id": user_id}
    if profile_id:
        data["profile_id"] = profile_id
    if title:
        data["title"] = title
    result = sb.table("conversations").insert(data).execute()
    return result.data[0] if result.data else {}


async def get_conversations_by_user(user_id: str) -> list[dict]:
    """Get all conversations for a user, newest first."""
    sb = get_supabase()
    result = (
        sb.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


async def get_conversation_messages(
    conversation_id: str, limit: int = 50
) -> list[dict]:
    """Get messages for a conversation, ordered chronologically."""
    sb = get_supabase()
    result = (
        sb.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return result.data or []


# ── Messages ────────────────────────────────────────────────────

async def create_message(
    conversation_id: str,
    role: str,
    content: str,
    language: str | None = None,
    tool_calls: dict | None = None,
) -> dict:
    """Insert a new message into a conversation."""
    sb = get_supabase()
    data: dict = {
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
    }
    if language:
        data["language"] = language
    if tool_calls:
        data["tool_calls"] = tool_calls
    result = sb.table("messages").insert(data).execute()
    return result.data[0] if result.data else {}


# ── Self profile loader (Phase 4) ──────────────────────────────


async def get_self_profile(user_id: str) -> dict | None:
    """
    Return the user's `relationship = "self"` birth profile or None.
    Used by the WebSocket handler to pre-load `natal_chart` and
    `computed_dashas` before the agent graph runs.
    """
    sb = get_supabase()
    result = (
        sb.table("birth_profiles")
        .select("*")
        .eq("user_id", user_id)
        .eq("relationship", "self")
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Profile updates (Phase 4+) ─────────────────────────────────


async def update_profile(profile_id: str, updates: dict) -> dict | None:
    """Generic profile update — used to refresh place, birth time, etc."""
    sb = get_supabase()
    result = (
        sb.table("birth_profiles")
        .update(updates)
        .eq("id", profile_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def update_conversation_title(conversation_id: str, title: str) -> dict | None:
    sb = get_supabase()
    result = (
        sb.table("conversations")
        .update({"title": title})
        .eq("id", conversation_id)
        .execute()
    )
    return result.data[0] if result.data else None


async def delete_conversation(conversation_id: str) -> bool:
    sb = get_supabase()
    result = (
        sb.table("conversations")
        .delete()
        .eq("id", conversation_id)
        .execute()
    )
    return bool(result.data)
