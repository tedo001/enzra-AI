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


def test_fallen_tree_across_corridor_is_on_track(settings):
    # A tree lying across the rails: foot point (bottom-center) sits off to the
    # left of the corridor, but the box spans the corridor -> overlap catches it.
    seg = CorridorSegmenter(settings)
    box = BoundingBox(x1=120, y1=560, x2=760, y2=610)
    assert seg.is_on_track(box, 1280, 720) is True


def test_overlap_ratio_bounds(settings):
    seg = CorridorSegmenter(settings)
    inside = BoundingBox(x1=600, y1=600, x2=680, y2=700)
    outside = BoundingBox(x1=0, y1=0, x2=40, y2=40)
    assert seg.overlap_ratio(inside, 1280, 720) > 0.5
    assert seg.overlap_ratio(outside, 1280, 720) == 0.0


def test_model_polygon_ema_smoothing(settings):
    settings.corridor_mode = "model"
    seg = CorridorSegmenter(settings)
    poly_a = [[600, 300], [680, 300], [1100, 720], [180, 720]]
    seg.update_model_polygon(poly_a)
    first = seg.corridor_polygon(1280, 720)
    # A jumpy second polygon should be damped by EMA, not adopted verbatim.
    poly_b = [[500, 300], [780, 300], [1200, 720], [80, 720]]
    seg.update_model_polygon(poly_b)
    second = seg.corridor_polygon(1280, 720)
    assert not (first == second).all()  # it moved
    assert second[0][0] > 500  # but stayed closer to the previous value
