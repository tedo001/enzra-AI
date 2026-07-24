"""Analytics service — daily reports and detection statistics.

Aggregates persisted incidents and per-class counters into the payloads the
dashboard's analytics view consumes. Pure read model over the repositories.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from app.database.repository import IncidentRepository, StatsRepository
from app.schemas import AlertLevel


class AnalyticsService:
    def __init__(self, incidents: IncidentRepository, stats: StatsRepository) -> None:
        self._incidents = incidents
        self._stats = stats

    async def daily_report(self, day: str | None = None) -> dict:
        day = day or datetime.utcnow().strftime("%Y-%m-%d")
        frequency = await self._stats.frequency(day)
        recent = await self._incidents.list_recent(limit=200)
        todays = [i for i in recent if i.created_at.strftime("%Y-%m-%d") == day]

        by_level = Counter(i.alert_level.value for i in todays)
        critical = [i for i in todays if i.alert_level == AlertLevel.CRITICAL]
        distances = [i.min_distance_m for i in todays if i.min_distance_m is not None]

        return {
            "day": day,
            "total_detections": sum(frequency.values()),
            "total_incidents": len(todays),
            "critical_incidents": len(critical),
            "obstacle_frequency": frequency,
            "incidents_by_level": dict(by_level),
            "closest_obstacle_m": min(distances) if distances else None,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def statistics(self) -> dict:
        frequency = await self._stats.frequency()
        recent = await self._incidents.list_recent(limit=500)
        return {
            "obstacle_frequency": frequency,
            "total_incidents": len(recent),
            "most_common_obstacle": (
                max(frequency, key=frequency.get) if frequency else None
            ),
            "incidents_by_level": dict(
                Counter(i.alert_level.value for i in recent)
            ),
        }

    async def incident_history(self, limit: int = 50) -> list[dict]:
        records = await self._incidents.list_recent(limit=limit)
        return [r.model_dump(mode="json") for r in records]
