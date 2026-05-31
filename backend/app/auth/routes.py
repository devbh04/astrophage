"""Auth routes — register, login, logout, me, update preferences."""

from fastapi import APIRouter, HTTPException, Response, Depends, status
from pydantic import BaseModel

from app.auth.service import hash_password, verify_password, create_jwt
from app.auth.dependencies import get_current_user
from app.db.models import RegisterRequest, LoginRequest, UserResponse
from app.db.queries import create_user, get_user_by_email, update_user

router = APIRouter(prefix="/auth", tags=["auth"])


class UpdatePreferencesBody(BaseModel):
    name: str | None = None
    default_language: str | None = None
    chart_format: str | None = None
    residence_place_name: str | None = None
    residence_lat: float | None = None
    residence_lng: float | None = None
    residence_timezone: str | None = None


def _set_auth_cookie(response: Response, token: str) -> None:
    """Set the JWT as an HTTP-only cookie with 7-day expiry."""
    response.set_cookie(
        key="astrophage_session",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 3600,
        path="/",
    )


def _user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        default_language=user.get("default_language", "en"),
        chart_format=user.get("chart_format", "south_indian"),
        residence_place_name=user.get("residence_place_name"),
        residence_lat=user.get("residence_lat"),
        residence_lng=user.get("residence_lng"),
        residence_timezone=user.get("residence_timezone"),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response):
    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    hashed = hash_password(body.password)
    user = await create_user(
        email=body.email,
        password_hash=hashed,
        name=body.name,
        default_language=body.default_language,
    )
    token = create_jwt(user["id"], user["email"])
    _set_auth_cookie(response, token)
    return _user_response(user)


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    user = await get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_jwt(user["id"], user["email"])
    _set_auth_cookie(response, token)
    return _user_response(user)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="astrophage_session",
        path="/",
        secure=True,
        samesite="none",
    )
    return {"message": "Logged out"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return _user_response(user)


@router.patch("/me")
async def update_preferences(
    body: UpdatePreferencesBody,
    user: dict = Depends(get_current_user),
):
    """Update name, default_language, or chart_format."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "default_language" in updates:
        if updates["default_language"] not in {"en", "hi", "mr", "gu", "ta", "kn"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported language",
            )
    if "chart_format" in updates:
        if updates["chart_format"] not in {"south_indian", "north_indian"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported chart format",
            )
    if not updates:
        return _user_response(user)
    updated = await update_user(user["id"], updates)
    return _user_response(updated or user)
