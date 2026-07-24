"""YOLO26 detector backend (Ultralytics).

RailVision AI standardises on **YOLO26** — the latest Ultralytics detection
family — chosen over YOLO11 for its improved small-object recall (critical for
distant obstacles on the track) and native end-to-end NMS-free inference.

Design notes
------------
* The heavy ``ultralytics`` / ``torch`` imports are *lazy* so the API server,
  tests and CI can import this module without a GPU stack installed.
* If weights or the AI extra are missing, :meth:`load` raises
  :class:`DetectorUnavailable`; callers fall back to
  :class:`~app.ai.mock_detector.MockDetector` so the platform still boots.
* Custom RailVision weights emit native class names; a COCO-pretrained
  checkpoint is remapped via :mod:`app.ai.class_map`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.ai.base import BaseDetector
from app.ai.class_map import resolve_class
from app.config import Settings
from app.logging_config import get_logger
from app.schemas import BoundingBox, Detection

log = get_logger(__name__)


class DetectorUnavailable(RuntimeError):
    """Raised when the YOLO26 backend cannot be initialised."""


class Yolo26Detector(BaseDetector):
    backend_name = "yolo26-ultralytics"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = None
        self._device = "cpu"
        self._names: dict[int, str] = {}

    # -- lifecycle ----------------------------------------------------------
    def load(self) -> None:
        if self._model is not None:
            return
        try:
            from ultralytics import YOLO  # noqa: PLC0415  (lazy import by design)
        except ImportError as exc:  # pragma: no cover - env dependent
            raise DetectorUnavailable(
                "ultralytics is not installed; install the '[ai]' extra"
            ) from exc

        weights = Path(self._settings.model_path)
        if not weights.exists():
            # Zero-config bootstrap: fall back to a pretrained YOLO26 nano
            # checkpoint (auto-downloaded by ultralytics) remapped from COCO.
            log.warning(
                "custom weights not found; using pretrained yolo26n",
                requested=str(weights),
            )
            model_ref = "yolo26n.pt"
        else:
            model_ref = str(weights)

        self._device = self._resolve_device()
        try:
            self._model = YOLO(model_ref)
            self._model.to(self._device)
            self._names = self._model.names
        except Exception as exc:  # pragma: no cover - env dependent
            raise DetectorUnavailable(f"failed to load YOLO26: {exc}") from exc

        # Warm-up pass stabilises latency measurements downstream.
        self._model.predict(
            np.zeros((self._settings.img_size, self._settings.img_size, 3), np.uint8),
            verbose=False,
        )
        log.info("yolo26 loaded", device=self._device, model=model_ref)

    def _resolve_device(self) -> str:
        want = self._settings.device
        if want != "auto":
            return want
        try:
            import torch  # noqa: PLC0415

            return "cuda:0" if torch.cuda.is_available() else "cpu"
        except ImportError:  # pragma: no cover
            return "cpu"

    # -- inference ----------------------------------------------------------
    def predict(self, frame: np.ndarray) -> list[Detection]:
        if self._model is None:
            raise DetectorUnavailable("detector not loaded; call load() first")

        s = self._settings
        results = self._model.predict(
            frame,
            conf=s.conf_threshold,
            iou=s.iou_threshold,
            imgsz=s.img_size,
            max_det=s.max_det,
            half=s.half_precision and self._device.startswith("cuda"),
            device=self._device,
            verbose=False,
        )
        detections: list[Detection] = []
        if not results:
            return detections

        boxes = results[0].boxes
        if boxes is None:
            return detections

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)

        for (x1, y1, x2, y2), conf, cls_id in zip(xyxy, confs, clss, strict=False):
            raw = self._names.get(int(cls_id), str(cls_id))
            detections.append(
                Detection(
                    label=resolve_class(raw),
                    raw_label=raw,
                    confidence=float(conf),
                    box=BoundingBox(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2)),
                )
            )
        return detections

    # -- introspection ------------------------------------------------------
    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def device(self) -> str:
        return self._device
