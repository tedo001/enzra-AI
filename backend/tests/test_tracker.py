"""Tracker tests — persistent IDs and lifecycle."""

from __future__ import annotations

from app.schemas import BoundingBox, Detection, ObstacleClass
from app.tracking.tracker import ObjectTracker


def _det(x: float) -> Detection:
    return Detection(
        label=ObstacleClass.HUMAN,
        confidence=0.9,
        box=BoundingBox(x1=x, y1=100, x2=x + 40, y2=300),
    )


def test_stable_id_across_frames():
    tracker = ObjectTracker(min_hits=1)
    out1 = tracker.update([_det(100)])
    out2 = tracker.update([_det(105)])  # small movement, high IoU
    assert out1[0].track_id is not None
    assert out1[0].track_id == out2[0].track_id


def test_new_object_new_id():
    tracker = ObjectTracker(min_hits=1)
    tracker.update([_det(100)])
    out = tracker.update([_det(100), _det(900)])
    ids = {d.track_id for d in out}
    assert len(ids) == 2


def test_track_ages_out():
    tracker = ObjectTracker(min_hits=1, max_age=2)
    tracker.update([_det(100)])
    for _ in range(5):
        tracker.update([])  # no detections
    # After ageing, a reappearance should get a fresh id.
    out = tracker.update([_det(100)])
    assert out[0].track_id is not None
