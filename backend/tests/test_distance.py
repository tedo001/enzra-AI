"""Distance estimation tests."""

from __future__ import annotations

from app.depth.distance import DistanceEstimator
from app.schemas import BoundingBox, ObstacleClass


def test_closer_object_smaller_distance(settings):
    est = DistanceEstimator(settings)
    near = BoundingBox(x1=600, y1=300, x2=700, y2=700)  # big, low foot point
    far = BoundingBox(x1=630, y1=330, x2=650, y2=360)   # small, high foot point
    d_near = est.estimate(near, ObstacleClass.HUMAN, 720)
    d_far = est.estimate(far, ObstacleClass.HUMAN, 720)
    assert d_near < d_far


def test_distance_positive_and_bounded(settings):
    est = DistanceEstimator(settings)
    box = BoundingBox(x1=620, y1=400, x2=660, y2=680)
    d = est.estimate(box, ObstacleClass.COW, 720)
    assert 1.0 <= d <= 2000.0
