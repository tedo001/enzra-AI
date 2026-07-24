"""Ensemble detector tests."""

from __future__ import annotations

import numpy as np

from app.ai.base import BaseDetector
from app.ai.ensemble_detector import EnsembleDetector
from app.schemas import BoundingBox, Detection, ObstacleClass


class _StubDetector(BaseDetector):
    def __init__(self, name: str, dets: list[Detection]) -> None:
        self.backend_name = name
        self._dets = dets
        self._loaded = False

    def load(self) -> None:
        self._loaded = True

    def predict(self, frame: np.ndarray) -> list[Detection]:
        return list(self._dets)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def device(self) -> str:
        return "cpu"


def _det(raw, x1, conf, label=ObstacleClass.HUMAN) -> Detection:
    return Detection(
        label=label,
        raw_label=raw,
        confidence=conf,
        box=BoundingBox(x1=x1, y1=0, x2=x1 + 100, y2=100),
    )


def test_ensemble_merges_and_dedups():
    general = _StubDetector("yolo26-general", [_det("person", 0, 0.9)])
    specialist = _StubDetector(
        "specialist", [_det("fallen_tree", 5, 0.6, ObstacleClass.FALLEN_TREE)]
    )
    ens = EnsembleDetector([general, specialist], iou_threshold=0.5)
    ens.load()
    out = ens.predict(np.zeros((100, 200, 3), np.uint8))
    # The two boxes overlap heavily -> deduplicated to one.
    assert len(out) == 1
    assert ens.is_loaded


def test_ensemble_keeps_distinct_detections():
    general = _StubDetector("yolo26-general", [_det("person", 0, 0.9)])
    specialist = _StubDetector(
        "specialist", [_det("fallen_tree", 400, 0.8, ObstacleClass.FALLEN_TREE)]
    )
    ens = EnsembleDetector([general, specialist])
    ens.load()
    out = ens.predict(np.zeros((100, 600, 3), np.uint8))
    assert len(out) == 2
    assert "ensemble[" in ens.backend_name
