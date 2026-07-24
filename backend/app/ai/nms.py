"""Cross-model Non-Maximum Suppression for detection ensembles.

When several detectors run on the same frame (e.g. a general YOLO26 model plus
a domain specialist), their outputs overlap. This module merges them with a
greedy IoU suppression, keeping the highest-confidence box in each cluster and
optionally boosting a trusted source so a specialist wins ties in its domain.

Generalises the two-model merge idea from the reference project to an arbitrary
number of sources, operating on the typed :class:`~app.schemas.Detection`
contract rather than raw tuples.
"""

from __future__ import annotations

from collections.abc import Mapping

from app.schemas import BoundingBox, Detection


def iou(a: BoundingBox, b: BoundingBox) -> float:
    """Intersection-over-Union of two boxes."""
    ix1, iy1 = max(a.x1, b.x1), max(a.y1, b.y1)
    ix2, iy2 = min(a.x2, b.x2), min(a.y2, b.y2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = a.area + b.area - inter
    return inter / union if union > 0 else 0.0


def cross_model_nms(
    detections: list[Detection],
    *,
    iou_threshold: float = 0.5,
    source_priority: Mapping[str, float] | None = None,
) -> list[Detection]:
    """Greedy cross-model NMS.

    Parameters
    ----------
    detections:
        Combined detections from all sources.
    iou_threshold:
        Boxes overlapping a kept box by more than this are suppressed.
    source_priority:
        Optional per-source confidence bonus (keyed by ``Detection.raw_label``
        prefix or a source tag carried in ``raw_label``). Lets a trusted
        specialist outrank the general model on ties without mutating the
        reported confidence.

    Returns
    -------
    A deduplicated list, ordered by (boosted) confidence descending.
    """
    if not detections:
        return []

    source_priority = source_priority or {}

    def rank(det: Detection) -> float:
        bonus = source_priority.get(det.raw_label, 0.0)
        return det.confidence + bonus

    ordered = sorted(detections, key=rank, reverse=True)
    kept: list[Detection] = []
    suppressed = [False] * len(ordered)

    for i, det_i in enumerate(ordered):
        if suppressed[i]:
            continue
        kept.append(det_i)
        for j in range(i + 1, len(ordered)):
            if suppressed[j]:
                continue
            if iou(det_i.box, ordered[j].box) > iou_threshold:
                suppressed[j] = True
    return kept
