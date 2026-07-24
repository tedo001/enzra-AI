"""Detector factory — selects and constructs the best available backend.

Composition strategy:

1. If a **specialist** model is configured, build an :class:`EnsembleDetector`
   fusing the general YOLO26 model with the specialist (general + domain
   hazards), merged via cross-model NMS.
2. Otherwise build the single general YOLO26 detector.
3. If the YOLO26 stack is unavailable (no ``[ai]`` extra / weights / GPU),
   transparently degrade to :class:`MockDetector` so the service always boots.

Keeping this wiring in one place is the *composition root* for detection.
"""

from __future__ import annotations

from app.ai.base import BaseDetector
from app.ai.ensemble_detector import EnsembleDetector
from app.ai.mock_detector import MockDetector
from app.ai.yolo26_detector import DetectorUnavailable, Yolo26Detector
from app.config import Settings
from app.logging_config import get_logger

log = get_logger(__name__)


def _build_yolo(settings: Settings) -> BaseDetector:
    general = Yolo26Detector(settings, backend_name="yolo26-general")
    if not settings.specialist_model_path:
        general.load()
        return general

    specialist = Yolo26Detector(
        settings,
        weights_override=settings.specialist_model_path,
        backend_name="specialist",
    )
    ensemble = EnsembleDetector(
        [general, specialist],
        iou_threshold=settings.ensemble_iou_threshold,
        specialist_bonus=settings.specialist_conf_bonus,
    )
    ensemble.load()
    return ensemble


def build_detector(settings: Settings, *, allow_fallback: bool = True) -> BaseDetector:
    """Construct a loaded detector (ensemble or single), with mock fallback."""
    try:
        return _build_yolo(settings)
    except DetectorUnavailable as exc:
        if not allow_fallback:
            raise
        log.warning("falling back to mock detector", reason=str(exc))
        mock = MockDetector()
        mock.load()
        return mock
