"""Auth routes — register, login, logout, me."""

from fastapi import APIRouter, HTTPException, Response, Depends, status

from app.auth.service import hash_password, verify_password, create_jwt
from app.auth.dependencies import get_current_user
from app.db.models import RegisterRequest, LoginRequest, UserResponse
from app.db.queries import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set the JWT as an HTTP-only cookie with 7-day expiry."""
    response.set_cookie(
        key="astrophage_session",
        value=token,
        httponly=True,
        secure=False,  # Set True in production (HTTPS)
        samesite="lax",
        max_age=7 * 24 * 3600,  # 7 days
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response):
    """Create a new user account and set session cookie."""
    # Check if email already exists
    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    hashed = hash_password(body.password)
    user = await create_user(
        email=body.email,
        password_hash=hashed,
        name=body.name,
        default_language=body.default_language,
    )

    # Set cookie
    token = create_jwt(user["id"], user["email"])
    _set_auth_cookie(response, token)

    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        default_language=user["default_language"],
        chart_format=user.get("chart_format", "south_indian"),
    )


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    """Authenticate and set session cookie."""
    user = await get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_jwt(user["id"], user["email"])
    _set_auth_cookie(response, token)

    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        default_language=user["default_language"],
        chart_format=user.get("chart_format", "south_indian"),
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(
        key="astrophage_session",
        path="/",
    )
    return {"message": "Logged out"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """Return the current authenticated user."""
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        default_language=user["default_language"],
        chart_format=user.get("chart_format", "south_indian"),
    )
