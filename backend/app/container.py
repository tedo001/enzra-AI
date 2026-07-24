"""Composition root — builds and wires all collaborators.

Centralising object construction here (rather than scattering `new` calls)
keeps dependency wiring explicit and testable, and gives FastAPI a single
lifespan-scoped container to attach to ``app.state``.
"""

from __future__ import annotations

import time

from app.ai.factory import build_detector
from app.alerts.alert_manager import AlertManager
from app.analytics.incident_recorder import IncidentRecorder
from app.analytics.reporter import AnalyticsService
from app.config import Settings, get_settings
from app.database.repository import IncidentRepository, StatsRepository
from app.database.session import Database, get_database
from app.depth.distance import DistanceEstimator
from app.detection.pipeline import RailVisionPipeline
from app.detection.risk import CollisionRiskEngine
from app.logging_config import get_logger
from app.segmentation.corridor import CorridorSegmenter
from app.tracking.tracker import ObjectTracker

log = get_logger(__name__)


class Container:
    """Holds long-lived singletons for the application lifespan."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.started_at = time.monotonic()

        # AI + pipeline stages.
        self.detector = build_detector(self.settings)
        self.pipeline = RailVisionPipeline(
            settings=self.settings,
            detector=self.detector,
            tracker=ObjectTracker(),
            segmenter=CorridorSegmenter(self.settings),
            distance=DistanceEstimator(self.settings),
            risk=CollisionRiskEngine(self.settings),
            alerts=AlertManager(self.settings),
        )
        self.alerts = AlertManager(self.settings)

        # Persistence + analytics.
        self.db: Database = get_database(self.settings)
        self.incident_repo = IncidentRepository(self.db)
        self.stats_repo = StatsRepository(self.db)
        self.analytics = AnalyticsService(self.incident_repo, self.stats_repo)
        self.recorder = IncidentRecorder(
            self.settings, self.incident_repo, self.stats_repo
        )

    async def startup(self) -> None:
        await self.db.create_all()
        log.info(
            "container ready",
            detector=self.detector.backend_name,
            device=self.detector.device,
        )

    async def shutdown(self) -> None:
        await self.db.dispose()

    @property
    def uptime_s(self) -> float:
        return time.monotonic() - self.started_at
