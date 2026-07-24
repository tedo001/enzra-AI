"""Cross-model NMS tests."""

from __future__ import annotations

from app.ai.nms import cross_model_nms, iou
from app.schemas import BoundingBox, Detection, ObstacleClass


def _det(x1, y1, x2, y2, conf, raw="person") -> Detection:
    return Detection(
        label=ObstacleClass.HUMAN,
        raw_label=raw,
        confidence=conf,
        box=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
    )


def test_iou_identical_boxes():
    b = BoundingBox(x1=0, y1=0, x2=10, y2=10)
    assert iou(b, b) == 1.0


def test_iou_disjoint_boxes():
    a = BoundingBox(x1=0, y1=0, x2=10, y2=10)
    b = BoundingBox(x1=20, y1=20, x2=30, y2=30)
    assert iou(a, b) == 0.0


def test_duplicate_suppressed_highest_conf_kept():
    a = _det(0, 0, 100, 100, 0.9)
    b = _det(5, 5, 100, 100, 0.6)  # heavy overlap with a
    kept = cross_model_nms([b, a], iou_threshold=0.5)
    assert len(kept) == 1
    assert kept[0].confidence == 0.9


def test_distinct_boxes_both_kept():
    a = _det(0, 0, 50, 50, 0.8)
    b = _det(200, 200, 260, 260, 0.7)
    kept = cross_model_nms([a, b], iou_threshold=0.5)
    assert len(kept) == 2


def test_specialist_priority_wins_tie():
    general = _det(0, 0, 100, 100, 0.70, raw="tree")
    specialist = _det(3, 3, 100, 100, 0.68, raw="fallen_tree")
    # Without a bonus the general box would win; a specialist bonus flips it.
    kept = cross_model_nms(
        [general, specialist],
        iou_threshold=0.5,
        source_priority={"fallen_tree": 0.1},
    )
    assert len(kept) == 1
    assert kept[0].raw_label == "fallen_tree"
