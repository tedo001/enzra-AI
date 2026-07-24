"""The RailVision inference pipeline (composition of stages).

Orchestrates one frame through the full safety pipeline:

    detect → track → corridor filter → distance → risk → alerts

Each stage is an injected collaborator (Dependency Injection), so any stage can
be swapped or mocked. The pipeline is deliberately stateful only where physics
demands it (tracker + risk engine keep per-track history); everything else is a
pure transform of the incoming frame.
"""

from __future__ import annotations

import time

import numpy as np

from app.ai.base import BaseDetector
from app.alerts.alert_manager import AlertManager
from app.config import Settings
from app.depth.distance import DistanceEstimator
from app.detection.risk import CollisionRiskEngine
from app.logging_config import get_logger
from app.schemas import FrameResult
from app.segmentation.corridor import CorridorSegmenter
from app.tracking.tracker import ObjectTracker

log = get_logger(__name__)


class RailVisionPipeline:
    def __init__(
        self,
        *,
        settings: Settings,
        detector: BaseDetector,
        tracker: ObjectTracker,
        segmenter: CorridorSegmenter,
        distance: DistanceEstimator,
        risk: CollisionRiskEngine,
        alerts: AlertManager,
    ) -> None:
        self._settings = settings
        self._detector = detector
        self._tracker = tracker
        self._segmenter = segmenter
        self._distance = distance
        self._risk = risk
        self._alerts = alerts
        self._frame_id = 0
        self._last_ts = time.monotonic()
        self._fps = 0.0

    @property
    def detector_backend(self) -> str:
        return self._detector.backend_name

    def reset(self) -> None:
        self._tracker.reset()
        self._risk.reset()
        self._frame_id = 0

    def process(self, frame: np.ndarray) -> FrameResult:
        """Run the full pipeline on a single BGR frame."""
        start = time.perf_counter()
        h, w = frame.shape[:2]
        self._frame_id += 1
        now_s = time.monotonic()

        # 1. Detection
        raw = self._detector.predict(frame)

        # 2. Tracking (persistent IDs)
        tracked = self._tracker.update(raw)

        # 3. Corridor filter + 4. Distance + 5. Risk
        enriched = []
        for det in tracked:
            on_track = self._segmenter.is_on_track(det.box, w, h)
            dist = (
                self._distance.estimate(det.box, det.label, h) if on_track else None
            )
            det = det.model_copy(update={"on_track": on_track, "distance_m": dist})
            det = self._risk.assess(det, now_s)
            enriched.append(det)

        # 6. Alerts
        overall = self._alerts.overall_level(enriched)
        recommendation = self._alerts.recommendation(overall, enriched)

        inference_ms = (time.perf_counter() - start) * 1000.0
        self._update_fps(now_s)

        return FrameResult(
            frame_id=self._frame_id,
            width=w,
            height=h,
            fps=round(self._fps, 1),
            inference_ms=round(inference_ms, 2),
            detections=enriched,
            corridor_polygon=self._segmenter.corridor_polygon(w, h).tolist(),
            overall_alert=overall,
            recommendation=recommendation,
        )

    def _update_fps(self, now_s: float) -> None:
        dt = now_s - self._last_ts
        self._last_ts = now_s
        if dt > 0:
            inst = 1.0 / dt
            # Exponential moving average smooths jitter.
            self._fps = 0.9 * self._fps + 0.1 * inst if self._fps else inst
