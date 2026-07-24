"""Corridor segmentation / on-track filtering tests."""

from __future__ import annotations

from app.schemas import BoundingBox
from app.segmentation.corridor import CorridorSegmenter


def test_center_bottom_is_on_track(settings):
    seg = CorridorSegmenter(settings)
    box = BoundingBox(x1=620, y1=400, x2=660, y2=690)  # foot near center-bottom
    assert seg.is_on_track(box, 1280, 720) is True


def test_corner_is_off_track(settings):
    seg = CorridorSegmenter(settings)
    box = BoundingBox(x1=10, y1=10, x2=60, y2=60)  # top-left corner
    assert seg.is_on_track(box, 1280, 720) is False


def test_polygon_cached(settings):
    seg = CorridorSegmenter(settings)
    a = seg.corridor_polygon(1280, 720)
    b = seg.corridor_polygon(1280, 720)
    assert a is b  # cache hit for identical shape
