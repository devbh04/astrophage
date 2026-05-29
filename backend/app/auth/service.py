"""Authentication service — password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_jwt(user_id: str, email: str) -> str:
    """Create a JWT token with user_id and email, valid for configured days."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)
        + timedelta(days=settings.jwt_expiry_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt(token: str) -> dict:
    """
    Decode and validate a JWT token.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
