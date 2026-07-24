"""Incident recorder — snapshots, clips, logs and JSON metadata.

When the overall alert crosses a configurable threshold (default: HIGH), the
recorder persists an evidence bundle: an annotated snapshot, a short pre/post
video clip (ring buffer), a detection log line, and a JSON metadata sidecar,
then registers the incident in the database. A cooldown prevents duplicate
records for the same ongoing event.
"""

from __future__ import annotations

import json
import time
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np

from app.config import Settings
from app.database.repository import IncidentRepository, StatsRepository
from app.logging_config import get_logger
from app.schemas import AlertLevel, FrameResult, IncidentRecord
from app.utils.drawing import draw_frame

log = get_logger(__name__)

try:  # pragma: no cover
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


class IncidentRecorder:
    def __init__(
        self,
        settings: Settings,
        incidents: IncidentRepository,
        stats: StatsRepository,
        *,
        trigger_level: AlertLevel = AlertLevel.HIGH,
        clip_seconds: float = 4.0,
        fps: int = 15,
    ) -> None:
        self._settings = settings
        self._incidents = incidents
        self._stats = stats
        self._trigger = trigger_level
        self._clip_frames = int(clip_seconds * fps)
        self._fps = fps
        self._buffer: deque[np.ndarray] = deque(maxlen=self._clip_frames)
        self._last_record_at = 0.0
        self._cooldown = 8.0
        self._dir = settings.storage_path / "incidents"
        self._dir.mkdir(parents=True, exist_ok=True)

    def observe(self, frame: np.ndarray, result: FrameResult) -> None:
        """Feed the ring buffer; call once per processed frame."""
        self._buffer.append(frame.copy())

    async def maybe_record(
        self, frame: np.ndarray, result: FrameResult, camera_id: str = "cam-0"
    ) -> IncidentRecord | None:
        """Persist an incident bundle if the alert threshold is crossed."""
        if result.overall_alert.rank < self._trigger.rank:
            return None
        now = time.monotonic()
        if now - self._last_record_at < self._cooldown:
            return None
        self._last_record_at = now

        incident_id = uuid.uuid4().hex[:12]
        stamp = datetime.utcnow()
        base = self._dir / f"{stamp:%Y%m%d}" / incident_id
        base.mkdir(parents=True, exist_ok=True)

        on_track = [d for d in result.detections if d.on_track]
        classes = [d.label for d in on_track]
        distances = [d.distance_m for d in on_track if d.distance_m is not None]
        max_risk = max((d.risk_score for d in on_track), default=0.0)

        image_path = self._save_snapshot(base, frame, result)
        clip_path = self._save_clip(base)
        meta_path = self._save_metadata(base, result, camera_id)

        record = IncidentRecord(
            id=incident_id,
            created_at=stamp,
            camera_id=camera_id,
            alert_level=result.overall_alert,
            frame_id=result.frame_id,
            obstacle_classes=classes,
            min_distance_m=min(distances) if distances else None,
            max_risk_score=max_risk,
            image_path=image_path,
            clip_path=clip_path,
            metadata_path=meta_path,
        )
        await self._incidents.add(record)
        await self._stats.increment(classes, camera_id)
        log.warning(
            "incident recorded",
            id=incident_id,
            level=result.overall_alert.value,
            classes=[c.value for c in classes],
        )
        return record

    # -- persistence helpers ------------------------------------------------
    def _save_snapshot(self, base: Path, frame: np.ndarray, result: FrameResult) -> str | None:
        if cv2 is None:
            return None
        annotated = draw_frame(frame, result)
        path = base / "snapshot.jpg"
        cv2.imwrite(str(path), annotated)
        return str(path)

    def _save_clip(self, base: Path) -> str | None:
        if cv2 is None or not self._buffer:
            return None
        h, w = self._buffer[0].shape[:2]
        path = base / "clip.mp4"
        writer = cv2.VideoWriter(
            str(path), cv2.VideoWriter_fourcc(*"mp4v"), self._fps, (w, h)
        )
        for f in self._buffer:
            writer.write(f)
        writer.release()
        return str(path)

    def _save_metadata(self, base: Path, result: FrameResult, camera_id: str) -> str:
        path = base / "metadata.json"
        payload = result.model_dump(mode="json")
        payload["camera_id"] = camera_id
        path.write_text(json.dumps(payload, indent=2))
        # Append to a rolling detection log.
        log_line = (
            f"{datetime.utcnow().isoformat()} {camera_id} "
            f"{result.overall_alert.value} frame={result.frame_id} "
            f"obstacles={result.obstacle_count}\n"
        )
        (self._dir / "detections.log").open("a").write(log_line)
        return str(path)
