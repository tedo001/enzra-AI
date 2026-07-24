"""Repository pattern — data access decoupled from ORM/domain.

Repositories translate between domain schemas (:mod:`app.schemas`) and ORM
models (:mod:`app.database.models`). The API and services depend on these
interfaces, not on SQLAlchemy, so storage can evolve independently.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from sqlalchemy import func, select

from app.database.models import DetectionStatORM, IncidentORM
from app.database.session import Database
from app.schemas import AlertLevel, IncidentRecord, ObstacleClass


class IncidentRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(self, record: IncidentRecord) -> None:
        async with self._db.session() as session:
            session.add(
                IncidentORM(
                    id=record.id,
                    created_at=record.created_at,
                    camera_id=record.camera_id,
                    alert_level=record.alert_level.value,
                    frame_id=record.frame_id,
                    obstacle_classes=[c.value for c in record.obstacle_classes],
                    min_distance_m=record.min_distance_m,
                    max_risk_score=record.max_risk_score,
                    image_path=record.image_path,
                    clip_path=record.clip_path,
                    metadata_path=record.metadata_path,
                )
            )

    async def list_recent(self, limit: int = 50) -> list[IncidentRecord]:
        async with self._db.session() as session:
            rows = (
                await session.execute(
                    select(IncidentORM).order_by(IncidentORM.created_at.desc()).limit(limit)
                )
            ).scalars().all()
            return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row: IncidentORM) -> IncidentRecord:
        return IncidentRecord(
            id=row.id,
            created_at=row.created_at,
            camera_id=row.camera_id,
            alert_level=AlertLevel(row.alert_level),
            frame_id=row.frame_id,
            obstacle_classes=[ObstacleClass(c) for c in row.obstacle_classes],
            min_distance_m=row.min_distance_m,
            max_risk_score=row.max_risk_score,
            image_path=row.image_path,
            clip_path=row.clip_path,
            metadata_path=row.metadata_path,
        )


class StatsRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def increment(self, classes: list[ObstacleClass], camera_id: str = "cam-0") -> None:
        if not classes:
            return
        day = datetime.utcnow().strftime("%Y-%m-%d")
        counts = Counter(c.value for c in classes)
        async with self._db.session() as session:
            for cls, n in counts.items():
                existing = (
                    await session.execute(
                        select(DetectionStatORM).where(
                            DetectionStatORM.day == day,
                            DetectionStatORM.obstacle_class == cls,
                            DetectionStatORM.camera_id == camera_id,
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    existing.count += n
                else:
                    session.add(
                        DetectionStatORM(
                            day=day, obstacle_class=cls, count=n, camera_id=camera_id
                        )
                    )

    async def frequency(self, day: str | None = None) -> dict[str, int]:
        async with self._db.session() as session:
            stmt = select(
                DetectionStatORM.obstacle_class, func.sum(DetectionStatORM.count)
            ).group_by(DetectionStatORM.obstacle_class)
            if day:
                stmt = stmt.where(DetectionStatORM.day == day)
            rows = (await session.execute(stmt)).all()
            return {cls: int(total) for cls, total in rows}
