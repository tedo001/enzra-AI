"""Abstract detector interface (Dependency Inversion Principle).

The rest of the platform depends on :class:`BaseDetector`, never on a concrete
model. This keeps YOLO26 swappable for ONNX Runtime, TensorRT, a mocked
detector for tests, or a future model family — without touching the pipeline.
"""

from __future__ import annotations

import abc

import numpy as np

from app.schemas import Detection


class BaseDetector(abc.ABC):
    """Contract every detector backend must satisfy."""

    #: Human-readable backend identifier, e.g. ``"yolo26-ultralytics"``.
    backend_name: str = "base"

    @abc.abstractmethod
    def load(self) -> None:
        """Load weights and warm up the model. Idempotent."""

    @abc.abstractmethod
    def predict(self, frame: np.ndarray) -> list[Detection]:
        """Run detection on a single BGR frame and return raw detections.

        Implementations must NOT perform tracking, distance or risk scoring —
        those are downstream stages.
        """

    @property
    @abc.abstractmethod
    def is_loaded(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def device(self) -> str:
        ...
