"""Railway corridor segmentation & on-track filtering.

Strategies, selectable via ``RV_CORRIDOR_MODE``:

* ``geometric`` — a trapezoidal region-of-interest anchored to the vanishing
  point. Zero-config, robust, and fully deterministic. Good default.
* ``model`` — a semantic-segmentation network (YOLO26-seg) predicts the rail
  bed polygon; feed it via :meth:`update_model_polygon` (EMA-smoothed).
* ``hybrid`` — intersect the model polygon with the geometric prior to suppress
  false positives (recommended in production).

On-track decision
-----------------
A detection is ``on_track`` when **either**:

1. its ground-contact foot point falls inside the corridor polygon (robust for
   upright obstacles like people/animals), **or**
2. a sufficient fraction of its bounding box overlaps the corridor mask
   (catches obstacles lying *across* the rails — e.g. a fallen tree — whose
   foot point is off to the side).

The overlap-ratio threshold (``RV_CORRIDOR_OVERLAP_RATIO``) is a deliberate
improvement over an "any single pixel overlaps" rule, which over-triggers on
tall trackside objects.
"""

from __future__ import annotations

import numpy as np

from app.config import Settings
from app.schemas import BoundingBox


class CorridorSegmenter:
    """Estimates the railway corridor polygon and classifies obstacles."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._overlap_ratio = settings.corridor_overlap_ratio
        self._alpha = settings.corridor_smoothing_alpha
        self._cached_shape: tuple[int, int] | None = None
        self._cached_polygon: np.ndarray | None = None
        self._cached_mask: np.ndarray | None = None
        # Optional EMA-smoothed polygon supplied by a segmentation model.
        self._model_polygon: np.ndarray | None = None
        self._smoothed: np.ndarray | None = None

    # -- polygon ------------------------------------------------------------
    def _geometric_polygon(self, width: int, height: int) -> np.ndarray:
        vanish_y = int(height * 0.45)
        top_half_w = int(width * 0.05)
        bottom_half_w = int(width * 0.42)
        cx = width // 2
        return np.array(
            [
                [cx - top_half_w, vanish_y],
                [cx + top_half_w, vanish_y],
                [cx + bottom_half_w, height],
                [cx - bottom_half_w, height],
            ],
            dtype=np.int32,
        )

    def corridor_polygon(self, width: int, height: int) -> np.ndarray:
        """Return the active corridor polygon as an (N, 2) int array.

        Uses the EMA-smoothed model polygon when one has been supplied and the
        mode allows it; otherwise the deterministic geometric prior.
        """
        if (
            self._settings.corridor_mode in ("model", "hybrid")
            and self._smoothed is not None
        ):
            return self._smoothed.astype(np.int32)

        if self._cached_shape == (width, height) and self._cached_polygon is not None:
            return self._cached_polygon
        poly = self._geometric_polygon(width, height)
        self._cached_shape = (width, height)
        self._cached_polygon = poly
        self._cached_mask = None  # invalidate
        return poly

    def update_model_polygon(self, raw_polygon: np.ndarray) -> None:
        """Feed a raw model-predicted polygon; applies EMA temporal smoothing.

        Smoothing reduces per-frame jitter/flicker of the segmentation. When
        the vertex count changes between frames (segmentation returns variable
        points), we reset to the new polygon rather than mis-aligning vertices.
        """
        raw = np.asarray(raw_polygon, dtype=np.float64)
        if self._smoothed is None or len(self._smoothed) != len(raw):
            self._smoothed = raw
        else:
            self._smoothed = self._alpha * raw + (1 - self._alpha) * self._smoothed
        self._cached_mask = None  # invalidate cached mask

    # -- mask & overlap -----------------------------------------------------
    def build_mask(self, width: int, height: int) -> np.ndarray:
        """Binary uint8 mask (1 inside corridor), cached per shape/polygon."""
        import cv2

        poly = self.corridor_polygon(width, height)
        if (
            self._cached_mask is not None
            and self._cached_mask.shape == (height, width)
        ):
            return self._cached_mask
        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [poly.astype(np.int32)], 1)
        self._cached_mask = mask
        return mask

    def overlap_ratio(self, box: BoundingBox, width: int, height: int) -> float:
        """Fraction of the box area that lies inside the corridor (0..1).

        Falls back to a triangle/polygon-free approximation when OpenCV is not
        available, sampling the box's foot-line against the polygon.
        """
        area = box.area
        if area <= 0:
            return 0.0
        try:
            mask = self.build_mask(width, height)
        except ImportError:
            return self._overlap_ratio_sampled(box, width, height)

        x1 = max(0, int(box.x1))
        y1 = max(0, int(box.y1))
        x2 = min(width, int(box.x2))
        y2 = min(height, int(box.y2))
        if x2 <= x1 or y2 <= y1:
            return 0.0
        inside = int(mask[y1:y2, x1:x2].sum())
        return inside / ((x2 - x1) * (y2 - y1))

    def _overlap_ratio_sampled(self, box: BoundingBox, width: int, height: int) -> float:
        """OpenCV-free approximation: sample a grid inside the box."""
        poly = self.corridor_polygon(width, height)
        xs = np.linspace(box.x1, box.x2, 6)
        ys = np.linspace(box.y1, box.y2, 6)
        hits = sum(
            1 for x in xs for y in ys if _point_in_polygon(float(x), float(y), poly)
        )
        return hits / 36.0

    # -- classification -----------------------------------------------------
    def is_on_track(self, box: BoundingBox, width: int, height: int) -> bool:
        """True if the obstacle intersects the railway corridor.

        Combines a foot-point-in-polygon test with a bounding-box overlap-ratio
        test (see module docstring).
        """
        poly = self.corridor_polygon(width, height)
        fx, fy = box.bottom_center
        if _point_in_polygon(fx, fy, poly):
            return True
        return self.overlap_ratio(box, width, height) >= self._overlap_ratio


def _point_in_polygon(x: float, y: float, poly: np.ndarray) -> bool:
    """Ray-casting point-in-polygon test."""
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside
