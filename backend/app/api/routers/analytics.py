"""Analytics & incident-history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.analytics.reporter import AnalyticsService
from app.api.dependencies import get_analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/daily")
async def daily_report(
    day: str | None = Query(None, description="YYYY-MM-DD; defaults to today"),
    analytics: AnalyticsService = Depends(get_analytics),
) -> dict:
    return await analytics.daily_report(day)


@router.get("/stats")
async def statistics(analytics: AnalyticsService = Depends(get_analytics)) -> dict:
    return await analytics.statistics()


@router.get("/incidents")
async def incidents(
    limit: int = Query(50, ge=1, le=500),
    analytics: AnalyticsService = Depends(get_analytics),
) -> list[dict]:
    return await analytics.incident_history(limit)
