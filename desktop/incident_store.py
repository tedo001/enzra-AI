"""Synchronous incident store for the desktop app.

The API server persists incidents through an async SQLAlchemy repository. In a
single-process Qt app we want zero async plumbing, so this is a compact
synchronous store built on the stdlib ``sqlite3`` plus file writes. It mirrors
the same evidence bundle (annotated snapshot, short clip, JSON metadata) and
powers the in-app analytics/incident-history panel.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from collections import Counter, deque
from datetime import datetime
from pathlib import Path

import numpy as np
from app.schemas import AlertLevel, FrameResult
from app.utils.drawing import draw_frame

import desktop  # noqa: F401  (package import extends sys.path for `app`)

try:  # pragma: no cover
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


class IncidentStore:
    def __init__(
        self,
        storage_dir: str | Path = "storage",
        *,
        trigger_level: AlertLevel = AlertLevel.HIGH,
        cooldown_s: float = 8.0,
        clip_seconds: float = 4.0,
        fps: int = 15,
    ) -> None:
        self._dir = Path(storage_dir) / "incidents"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._trigger = trigger_level
        self._cooldown = cooldown_s
        self._last_record = 0.0
        self._fps = fps
        self._buffer: deque[np.ndarray] = deque(maxlen=int(clip_seconds * fps))
        self._session_counts: Counter[str] = Counter()
        self._db = sqlite3.connect(
            str(Path(storage_dir) / "railvision_desktop.db"), check_same_thread=False
        )
        self._init_db()

    def _init_db(self) -> None:
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                alert_level TEXT,
                frame_id INTEGER,
                obstacle_classes TEXT,
                min_distance_m REAL,
                max_risk_score REAL,
                image_path TEXT,
                clip_path TEXT,
                metadata_path TEXT
            )
            """
        )
        self._db.commit()

    # -- ingest -------------------------------------------------------------
    def observe(self, frame: np.ndarray, result: FrameResult) -> None:
        """Feed the ring buffer and update per-session obstacle counts."""
        self._buffer.append(frame.copy())
        for det in result.detections:
            if det.on_track:
                self._session_counts[det.label.value] += 1

    def maybe_record(self, frame: np.ndarray, result: FrameResult) -> str | None:
        """Persist an evidence bundle if the alert threshold is crossed."""
        if result.overall_alert.rank < self._trigger.rank:
            return None
        now = time.monotonic()
        if now - self._last_record < self._cooldown:
            return None
        self._last_record = now
        return self._record(frame, result)

    def _record(self, frame: np.ndarray, result: FrameResult) -> str:
        incident_id = uuid.uuid4().hex[:12]
        stamp = datetime.utcnow()
        base = self._dir / f"{stamp:%Y%m%d}" / incident_id
        base.mkdir(parents=True, exist_ok=True)

        on_track = [d for d in result.detections if d.on_track]
        classes = [d.label.value for d in on_track]
        distances = [d.distance_m for d in on_track if d.distance_m is not None]
        max_risk = max((d.risk_score for d in on_track), default=0.0)

        image_path = self._save_snapshot(base, frame, result)
        clip_path = self._save_clip(base)
        meta_path = self._save_metadata(base, result)

        self._db.execute(
            "INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                incident_id,
                stamp.isoformat(),
                result.overall_alert.value,
                result.frame_id,
                json.dumps(classes),
                min(distances) if distances else None,
                max_risk,
                image_path,
                clip_path,
                meta_path,
            ),
        )
        self._db.commit()
        return incident_id

    # -- persistence helpers ------------------------------------------------
    def _save_snapshot(self, base: Path, frame: np.ndarray, result: FrameResult) -> str | None:
        if cv2 is None:
            return None
        path = base / "snapshot.jpg"
        cv2.imwrite(str(path), draw_frame(frame, result))
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

    def _save_metadata(self, base: Path, result: FrameResult) -> str:
        path = base / "metadata.json"
        path.write_text(json.dumps(result.model_dump(mode="json"), indent=2))
        return str(path)

    # -- analytics read model ----------------------------------------------
    def frequency(self) -> dict[str, int]:
        return dict(self._session_counts)

    def recent_incidents(self, limit: int = 50) -> list[dict]:
        cur = self._db.execute(
            "SELECT id, created_at, alert_level, obstacle_classes, "
            "min_distance_m, max_risk_score FROM incidents "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = []
        for r in cur.fetchall():
            rows.append(
                {
                    "id": r[0],
                    "created_at": r[1],
                    "alert_level": r[2],
                    "obstacle_classes": json.loads(r[3]) if r[3] else [],
                    "min_distance_m": r[4],
                    "max_risk_score": r[5],
                }
            )
        return rows

    def incident_count(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0])

    def close(self) -> None:
        self._db.close()
