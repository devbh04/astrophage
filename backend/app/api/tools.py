"""
Tools REST router.

Wraps a curated set of tools as HTTP endpoints so the frontend can render
deterministic data (panchang, muhurta, current sky, etc.) without round-
tripping through the agent. The endpoints are thin — they just unpack the
JSON body, call the tool, and return the result.
"""

from __future__ import annotations

from typing import Any
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.tools.birth_chart import compute_birth_chart
from app.tools.geocode import geocode_place
from app.tools.dasha import compute_dasha_periods
from app.tools.nakshatra import compute_nakshatra_details
from app.tools.sade_sati import check_sade_sati
from app.tools.panchang import get_panchang
from app.tools.kundali_milan import kundali_milan
from app.tools.chart_svg import render_chart_svg
from app.tools.muhurta import compute_muhurta
from app.tools.daily_transits import get_daily_transits
from app.tools.current_sky import get_current_sky
from app.tools.knowledge_lookup import knowledge_lookup


router = APIRouter(prefix="/api/tools", tags=["tools"])


# ── Schemas ─────────────────────────────────────────────────────


class GeocodeRequest(BaseModel):
    place_name: str


class BirthChartRequest(BaseModel):
    birth_date: str
    birth_time: str | None = None
    lat: float
    lng: float
    timezone: str


class DashaRequest(BaseModel):
    natal_chart: dict[str, Any]
    birth_date: str
    birth_time: str | None = None
    timezone: str
    levels: int = 2
    as_of: str | None = None


class NakshatraRequest(BaseModel):
    natal_chart: dict[str, Any]


class SadeSatiRequest(BaseModel):
    natal_chart: dict[str, Any]
    as_of: str | None = None


class PanchangRequest(BaseModel):
    date: str
    lat: float
    lng: float
    timezone: str


class MuhurtaRequest(BaseModel):
    purpose: str = Field(default="general")
    start_date: str
    end_date: str
    lat: float
    lng: float
    timezone: str


class DailyTransitsRequest(BaseModel):
    natal_chart: dict[str, Any]
    as_of: str | None = None
    lat: float | None = None
    lng: float | None = None


class CurrentSkyRequest(BaseModel):
    as_of: str | None = None
    lat: float | None = None
    lng: float | None = None


class ChartSvgRequest(BaseModel):
    natal_chart: dict[str, Any]
    style: str = "south_indian"


class KundaliMilanRequest(BaseModel):
    boy_chart: dict[str, Any]
    girl_chart: dict[str, Any]


class KnowledgeRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: dict[str, Any] | None = None


# ── Endpoints ───────────────────────────────────────────────────


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


@router.post("/geocode")
async def geocode(body: GeocodeRequest, _user: dict = Depends(get_current_user)):
    try:
        return await geocode_place(body.place_name)
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/birth-chart")
async def birth_chart(body: BirthChartRequest, _user: dict = Depends(get_current_user)):
    try:
        return compute_birth_chart(
            body.birth_date, body.birth_time, body.lat, body.lng, body.timezone
        )
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/dasha")
async def dasha(body: DashaRequest, _user: dict = Depends(get_current_user)):
    try:
        return compute_dasha_periods(
            body.natal_chart,
            body.birth_date,
            body.birth_time,
            body.timezone,
            levels=body.levels,
            as_of=body.as_of,
        )
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/nakshatra")
async def nakshatra(body: NakshatraRequest, _user: dict = Depends(get_current_user)):
    try:
        return compute_nakshatra_details(body.natal_chart)
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/sade-sati")
async def sade_sati(body: SadeSatiRequest, _user: dict = Depends(get_current_user)):
    try:
        return check_sade_sati(body.natal_chart, as_of=body.as_of)
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/panchang")
async def panchang(body: PanchangRequest, _user: dict = Depends(get_current_user)):
    try:
        return get_panchang(body.date, body.lat, body.lng, body.timezone)
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/muhurta")
async def muhurta(body: MuhurtaRequest, _user: dict = Depends(get_current_user)):
    try:
        return compute_muhurta(
            body.purpose, body.start_date, body.end_date, body.lat, body.lng, body.timezone
        )
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/daily-transits")
async def daily_transits(body: DailyTransitsRequest, _user: dict = Depends(get_current_user)):
    try:
        return get_daily_transits(
            body.natal_chart, as_of=body.as_of, lat=body.lat, lng=body.lng
        )
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/current-sky")
async def current_sky(body: CurrentSkyRequest, _user: dict = Depends(get_current_user)):
    try:
        return get_current_sky(as_of=body.as_of, lat=body.lat, lng=body.lng)
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/chart-svg")
async def chart_svg_endpoint(body: ChartSvgRequest, _user: dict = Depends(get_current_user)):
    try:
        return {"svg": render_chart_svg(body.natal_chart, body.style)}
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/kundali-milan")
async def kundali_milan_endpoint(body: KundaliMilanRequest, _user: dict = Depends(get_current_user)):
    try:
        return kundali_milan(body.boy_chart, body.girl_chart)
    except ValueError as exc:
        raise _bad_request(exc)


@router.post("/knowledge")
async def knowledge(body: KnowledgeRequest, _user: dict = Depends(get_current_user)):
    return await knowledge_lookup(body.query, top_k=body.top_k, filters=body.filters)
