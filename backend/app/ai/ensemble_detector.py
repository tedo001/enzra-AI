"""Ensemble detector — combine multiple detectors behind one interface.

Motivation
----------
A single general model misses domain-specific hazards that rarely appear in
generic datasets (fallen trees, rock slides, track debris). The reference
project addressed this by running a general COCO model alongside a custom
"fallen tree" model and merging the results. RailVision generalises that idea:

* Any number of :class:`BaseDetector` backends can be composed.
* Each is a first-class, independently loadable detector (e.g. a general
  YOLO26 model + a specialist YOLO26 model fine-tuned on rare hazards).
* Outputs are fused with :func:`~app.ai.nms.cross_model_nms`, with an optional
  confidence bonus so the specialist wins in its own domain.

Because the ensemble *is itself* a :class:`BaseDetector`, the rest of the
pipeline is unchanged — it does not know or care how many models produced the
detections (Liskov substitution).
"""

from __future__ import annotations

import numpy as np

from app.ai.base import BaseDetector
from app.ai.nms import cross_model_nms
from app.logging_config import get_logger
from app.schemas import Detection

log = get_logger(__name__)


class EnsembleDetector(BaseDetector):
    backend_name = "ensemble"

    def __init__(
        self,
        detectors: list[BaseDetector],
        *,
        iou_threshold: float = 0.5,
        specialist_bonus: float = 0.05,
        specialist_backends: tuple[str, ...] = ("specialist",),
    ) -> None:
        if not detectors:
            raise ValueError("EnsembleDetector requires at least one detector")
        self._detectors = detectors
        self._iou = iou_threshold
        self._specialist_bonus = specialist_bonus
        self._specialist_backends = specialist_backends

    def load(self) -> None:
        for d in self._detectors:
            d.load()
        self.backend_name = "ensemble[" + "+".join(d.backend_name for d in self._detectors) + "]"
        log.info("ensemble ready", members=[d.backend_name for d in self._detectors])

    def predict(self, frame: np.ndarray) -> list[Detection]:
        combined: list[Detection] = []
        priority: dict[str, float] = {}
        for det in self._detectors:
            results = det.predict(frame)
            is_specialist = det.backend_name in self._specialist_backends
            for r in results:
                combined.append(r)
                if is_specialist:
                    # Bonus keyed by the raw label so NMS ranking can favour it.
                    priority[r.raw_label] = self._specialist_bonus
        return cross_model_nms(
            combined, iou_threshold=self._iou, source_priority=priority
        )

    @property
    def is_loaded(self) -> bool:
        return all(d.is_loaded for d in self._detectors)

    @property
    def device(self) -> str:
        # Report the first member's device (they should share one).
        return self._detectors[0].device
