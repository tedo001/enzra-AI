"""SQLAlchemy ORM models (persistence layer).

Kept independent of the domain schemas in :mod:`app.schemas`; repositories map
between the two so the domain never leaks ORM details (Clean Architecture).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IncidentORM(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), default="cam-0", index=True)
    alert_level: Mapped[str] = mapped_column(String(16), index=True)
    frame_id: Mapped[int] = mapped_column(Integer)
    obstacle_classes: Mapped[list] = mapped_column(JSON, default=list)
    min_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    clip_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_path: Mapped[str | None] = mapped_column(String(512), nullable=True)


class DetectionStatORM(Base):
    """Aggregated per-class detection counters for analytics dashboards."""

    __tablename__ = "detection_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    obstacle_class: Mapped[str] = mapped_column(String(32), index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    camera_id: Mapped[str] = mapped_column(String(64), default="cam-0")
