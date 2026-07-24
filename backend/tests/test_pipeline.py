"""End-to-end pipeline test using the mock detector."""

from __future__ import annotations

from app.ai.mock_detector import MockDetector
from app.alerts.alert_manager import AlertManager
from app.depth.distance import DistanceEstimator
from app.detection.pipeline import RailVisionPipeline
from app.detection.risk import CollisionRiskEngine
from app.segmentation.corridor import CorridorSegmenter
from app.tracking.tracker import ObjectTracker


def _pipeline(settings) -> RailVisionPipeline:
    detector = MockDetector()
    detector.load()
    return RailVisionPipeline(
        settings=settings,
        detector=detector,
        tracker=ObjectTracker(min_hits=1),
        segmenter=CorridorSegmenter(settings),
        distance=DistanceEstimator(settings),
        risk=CollisionRiskEngine(settings),
        alerts=AlertManager(settings),
    )


def test_pipeline_produces_results(settings, blank_frame):
    pipe = _pipeline(settings)
    result = pipe.process(blank_frame)
    assert result.width == 1280
    assert result.height == 720
    assert result.frame_id == 1
    assert len(result.corridor_polygon) == 4


def test_pipeline_detects_and_scores(settings, blank_frame):
    pipe = _pipeline(settings)
    last = None
    for _ in range(40):  # let the mock person approach
        last = pipe.process(blank_frame)
    assert last is not None
    assert len(last.detections) >= 1
    # At least one detection should be evaluated for on-track risk.
    assert any(d.on_track for d in last.detections)
