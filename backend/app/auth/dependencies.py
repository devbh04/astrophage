"""FastAPI dependency for extracting the current user from the JWT cookie
or Authorization header.

Priority:
1. ``astrophage_session`` HttpOnly cookie (set on login — works on same-origin
   and correctly configured cross-origin deployments).
2. ``Authorization: Bearer <token>`` header (fallback for devices where the
   cross-origin cookie is blocked by the browser's third-party-cookie rules).

Both methods validate the same JWT and result in the same user lookup.
"""

from fastapi import Cookie, Header, HTTPException, status
import jwt as pyjwt

from app.auth.service import decode_jwt
from app.db.queries import get_user_by_id


async def get_current_user(
    astrophage_session: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> dict:
    """
    Extract and validate the JWT.

    Tries the HttpOnly cookie first, then falls back to the
    Authorization header so cross-origin clients that can't use
    cookies can still authenticate on all devices.
    """
    token: str | None = astrophage_session

    # Bearer token fallback
    if not token and authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value:
            token = value

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_jwt(token)
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
