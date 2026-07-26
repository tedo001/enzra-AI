"""Construct a ready-to-run RailVision pipeline for the desktop app.

This is the desktop composition root. It builds the same
:class:`RailVisionPipeline` used by the API server, wiring the detector
(YOLO26 ensemble → single → mock fallback) and every downstream stage. Keeping
this separate from the Qt code means the inference core stays UI-agnostic and
unit-testable.
"""

from __future__ import annotations

from app.ai.base import BaseDetector
from app.ai.factory import build_detector
from app.alerts.alert_manager import AlertManager
from app.config import Settings
from app.depth.distance import DistanceEstimator
from app.detection.pipeline import RailVisionPipeline
from app.detection.risk import CollisionRiskEngine
from app.segmentation.corridor import CorridorSegmenter
from app.tracking.tracker import ObjectTracker

import desktop  # noqa: F401  (package import extends sys.path for `app`)


class PipelineBundle:
    """Holds the pipeline plus references needed for live tuning/status."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.detector: BaseDetector = build_detector(settings)
        self.segmenter = CorridorSegmenter(settings)
        self.alerts = AlertManager(settings)
        self.pipeline = RailVisionPipeline(
            settings=settings,
            detector=self.detector,
            tracker=ObjectTracker(min_hits=2),
            segmenter=self.segmenter,
            distance=DistanceEstimator(settings),
            risk=CollisionRiskEngine(settings),
            alerts=AlertManager(settings),
        )

    # -- live tuning --------------------------------------------------------
    def set_confidence(self, value: float) -> None:
        self.settings.conf_threshold = max(0.05, min(0.95, value))

    def set_overlap_ratio(self, value: float) -> None:
        self.segmenter.set_overlap_ratio(value)

    def reset(self) -> None:
        self.pipeline.reset()

    # -- status -------------------------------------------------------------
    @property
    def backend_name(self) -> str:
        return self.detector.backend_name

    @property
    def device(self) -> str:
        return self.detector.device

    @property
    def model_loaded(self) -> bool:
        return self.detector.is_loaded


def build_bundle(settings: Settings | None = None) -> PipelineBundle:
    return PipelineBundle(settings or Settings())
