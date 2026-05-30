"""Pydantic models for database entities and API request/response schemas."""

from datetime import date, time, datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ── Request models ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Registration request with birth details."""
    email: str
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    default_language: str = "en"


class LoginRequest(BaseModel):
    """Login request."""
    email: str
    password: str


class BirthDetailsInput(BaseModel):
    """Input for birth details — used when creating/updating profiles."""
    name: str
    relationship: str = "self"
    birth_date: date
    birth_time: Optional[time] = None
    place_name: str
    lat: float
    lng: float
    timezone: str


# ── Database entity models ──────────────────────────────────────

class User(BaseModel):
    """User entity from the users table."""
    id: str
    email: str
    name: str
    default_language: str = "en"
    chart_format: str = "south_indian"
    created_at: Optional[datetime] = None


class BirthProfile(BaseModel):
    """Birth profile entity from the birth_profiles table."""
    id: str
    user_id: str
    name: str
    relationship: Optional[str] = None
    birth_date: date
    birth_time: Optional[time] = None
    lat: float
    lng: float
    timezone: str
    place_name: Optional[str] = None
    computed_chart: Optional[dict] = None
    computed_dashas: Optional[dict] = None
    created_at: Optional[datetime] = None


class Conversation(BaseModel):
    """Conversation entity."""
    id: str
    user_id: str
    profile_id: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None


class Message(BaseModel):
    """Message entity."""
    id: str
    conversation_id: str
    role: str
    content: str
    language: Optional[str] = None
    tool_calls: Optional[dict] = None
    created_at: Optional[datetime] = None


# ── Response models ─────────────────────────────────────────────

class UserResponse(BaseModel):
    """Safe user response (no password hash)."""
    id: str
    email: str
    name: str
    default_language: str
    chart_format: str
    residence_place_name: Optional[str] = None
    residence_lat: Optional[float] = None
    residence_lng: Optional[float] = None
    residence_timezone: Optional[str] = None


class ProfileResponse(BaseModel):
    """Birth profile response."""
    id: str
    name: str
    relationship: Optional[str] = None
    birth_date: date
    birth_time: Optional[time] = None
    place_name: Optional[str] = None
    computed_chart: Optional[dict] = None
    computed_dashas: Optional[dict] = None
