"""Detector factory — selects and constructs the best available backend.

Implements a small strategy/factory: try the requested high-performance
backend (YOLO26), and transparently degrade to the mock detector so the
service is always operational. This keeps the *composition root* (dependency
wiring) in one place.
"""

from __future__ import annotations

from app.ai.base import BaseDetector
from app.ai.mock_detector import MockDetector
from app.ai.yolo26_detector import DetectorUnavailable, Yolo26Detector
from app.config import Settings
from app.logging_config import get_logger

log = get_logger(__name__)


def build_detector(settings: Settings, *, allow_fallback: bool = True) -> BaseDetector:
    """Construct a loaded detector.

    Parameters
    ----------
    settings:
        Application settings.
    allow_fallback:
        If ``True`` (default) fall back to :class:`MockDetector` when YOLO26 is
        unavailable. Set ``False`` in benchmarking to fail fast.
    """
    detector: BaseDetector = Yolo26Detector(settings)
    try:
        detector.load()
        return detector
    except DetectorUnavailable as exc:
        if not allow_fallback:
            raise
        log.warning("falling back to mock detector", reason=str(exc))
        mock = MockDetector()
        mock.load()
        return mock
