"""Deterministic mock detector.

Used (a) in unit tests and CI, and (b) as a runtime fallback so the platform
boots and streams a live dashboard even when the GPU/torch stack or trained
weights are unavailable. It synthesises plausible moving obstacles so the full
pipeline (tracking → distance → risk → alerts) can be exercised end-to-end.
"""

from __future__ import annotations

import math

import numpy as np

from app.ai.base import BaseDetector
from app.schemas import BoundingBox, Detection, ObstacleClass


class MockDetector(BaseDetector):
    backend_name = "mock"

    def __init__(self, seed: int = 7) -> None:
        self._rng = np.random.default_rng(seed)
        self._t = 0
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def predict(self, frame: np.ndarray) -> list[Detection]:
        self._t += 1
        h, w = frame.shape[:2]
        dets: list[Detection] = []

        # A person walking toward the camera along the corridor (approaching).
        approach = (math.sin(self._t / 25.0) + 1) / 2  # 0..1
        cx = w * 0.5
        box_h = 40 + approach * 220
        box_w = box_h * 0.4
        y2 = h * 0.35 + approach * (h * 0.6)
        dets.append(
            Detection(
                label=ObstacleClass.HUMAN,
                raw_label="person",
                confidence=0.82,
                box=BoundingBox(
                    x1=cx - box_w / 2, y1=y2 - box_h, x2=cx + box_w / 2, y2=y2
                ),
            )
        )

        # An intermittent stationary obstacle off to the side.
        if self._t % 60 < 30:
            dets.append(
                Detection(
                    label=ObstacleClass.ROCK,
                    raw_label="rock",
                    confidence=0.61,
                    box=BoundingBox(
                        x1=w * 0.72, y1=h * 0.6, x2=w * 0.82, y2=h * 0.7
                    ),
                )
            )
        return dets

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def device(self) -> str:
        return "cpu"
