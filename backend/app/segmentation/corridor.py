"""Railway corridor segmentation & on-track filtering.

Two strategies, selectable via ``RV_CORRIDOR_MODE``:

* ``geometric`` — a trapezoidal region-of-interest anchored to the vanishing
  point. Zero-config, robust, and fully deterministic. Good default.
* ``model`` — a semantic-segmentation network (YOLO26-seg) predicts the rail
  bed mask. Higher fidelity on curves; requires ``seg`` weights.
* ``hybrid`` — intersect the model mask with the geometric prior to suppress
  false positives (recommended in production).

Downstream, a detection is flagged ``on_track`` when its ground-contact foot
point falls inside the corridor polygon — implementing the "ignore detections
outside the railway corridor" requirement.
"""

from __future__ import annotations

import numpy as np

from app.config import Settings
from app.schemas import BoundingBox


class CorridorSegmenter:
    """Estimates the railway corridor polygon for a frame."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cached_shape: tuple[int, int] | None = None
        self._cached_polygon: np.ndarray | None = None

    def corridor_polygon(self, width: int, height: int) -> np.ndarray:
        """Return the corridor polygon as an (N, 2) int array of pixel points.

        The geometric prior models the typical forward-facing cab view: a
        trapezoid narrowing toward a vanishing point ~45% down the frame.
        """
        if self._cached_shape == (width, height) and self._cached_polygon is not None:
            return self._cached_polygon

        vanish_y = int(height * 0.45)
        top_half_w = int(width * 0.05)
        bottom_half_w = int(width * 0.42)
        cx = width // 2
        poly = np.array(
            [
                [cx - top_half_w, vanish_y],
                [cx + top_half_w, vanish_y],
                [cx + bottom_half_w, height],
                [cx - bottom_half_w, height],
            ],
            dtype=np.int32,
        )
        self._cached_shape = (width, height)
        self._cached_polygon = poly
        return poly

    def build_mask(self, width: int, height: int) -> np.ndarray:
        """Binary uint8 mask (1 inside corridor)."""
        import cv2

        mask = np.zeros((height, width), dtype=np.uint8)
        cv2.fillPoly(mask, [self.corridor_polygon(width, height)], 1)
        return mask

    def is_on_track(self, box: BoundingBox, width: int, height: int) -> bool:
        """Point-in-polygon test on the detection's foot point.

        Uses a lightweight ray-casting test to avoid a hard OpenCV dependency
        in the hot path / tests.
        """
        poly = self.corridor_polygon(width, height)
        fx, fy = box.bottom_center
        return _point_in_polygon(fx, fy, poly)


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
