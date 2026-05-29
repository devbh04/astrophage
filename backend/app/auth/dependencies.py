"""FastAPI dependency for extracting the current user from the JWT cookie."""

from fastapi import Cookie, HTTPException, status
import jwt as pyjwt

from app.auth.service import decode_jwt
from app.db.queries import get_user_by_id


async def get_current_user(
    astrophage_session: str | None = Cookie(default=None),
) -> dict:
    """
    Extract and validate the JWT from the astrophage_session cookie.
    Returns the user dict from the database.
    Raises 401 if cookie is missing, expired, or invalid.
    """
    if not astrophage_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_jwt(astrophage_session)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    user = await get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
