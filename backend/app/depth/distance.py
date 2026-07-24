"""Monocular distance estimation.

RailVision estimates obstacle distance from a single forward-facing camera
using **ground-plane (inverse perspective) geometry**, which is robust and
calibration-driven — no depth network required:

    Z = (f * H) / (y_foot - y_horizon)

where ``f`` is focal length (px), ``H`` the camera mounting height (m), and the
denominator is the vertical offset of the obstacle's foot point below the
horizon. A physical-size cross-check (known class heights vs. box height)
disambiguates near-horizon cases and flying debris.

For curved track and richer scenes, a learned monocular-depth backend can be
substituted behind :meth:`estimate` — the pipeline only consumes ``distance_m``.
"""

from __future__ import annotations

from app.config import Settings
from app.schemas import BoundingBox, ObstacleClass

# Approximate real-world heights (m) for the size cross-check.
CLASS_HEIGHT_M: dict[ObstacleClass, float] = {
    ObstacleClass.HUMAN: 1.7,
    ObstacleClass.COW: 1.5,
    ObstacleClass.ELEPHANT: 3.0,
    ObstacleClass.DOG: 0.6,
    ObstacleClass.BUFFALO: 1.7,
    ObstacleClass.GOAT: 0.9,
    ObstacleClass.CAR: 1.5,
    ObstacleClass.TRUCK: 3.5,
    ObstacleClass.BUS: 3.2,
    ObstacleClass.MOTORCYCLE: 1.4,
    ObstacleClass.FALLEN_TREE: 1.0,
    ObstacleClass.ROCK: 0.8,
    ObstacleClass.CONSTRUCTION_BARRIER: 1.1,
    ObstacleClass.DEBRIS: 0.5,
    ObstacleClass.UNKNOWN: 1.5,
}


class DistanceEstimator:
    def __init__(self, settings: Settings) -> None:
        self._f = settings.camera_focal_px
        self._cam_h = settings.camera_height_m

    def estimate(
        self, box: BoundingBox, label: ObstacleClass, frame_height: int
    ) -> float:
        """Return estimated distance in metres (clamped to a sane range)."""
        horizon_y = frame_height * 0.45  # matches corridor vanishing point
        _, foot_y = box.bottom_center
        dy = foot_y - horizon_y

        if dy <= 1.0:
            # At/above horizon — geometry unreliable; use size-based estimate.
            return self._distance_from_size(box, label)

        ground = (self._f * self._cam_h) / dy
        size = self._distance_from_size(box, label)

        # Fuse: trust ground-plane more when foot point is well below horizon.
        w = min(1.0, dy / (frame_height * 0.3))
        fused = w * ground + (1 - w) * size
        return float(max(1.0, min(fused, 2000.0)))

    def _distance_from_size(self, box: BoundingBox, label: ObstacleClass) -> float:
        real_h = CLASS_HEIGHT_M.get(label, 1.5)
        px_h = max(box.height, 1.0)
        return (self._f * real_h) / px_h
