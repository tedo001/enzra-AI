"""Video source abstraction.

A generator-based reader over files, RTSP/HTTP streams or webcams, plus a
synthetic source so demos and tests run with zero hardware. All sources yield
BGR ``uint8`` frames, decoupling the pipeline from capture details
(multi-camera, drone, thermal feeds all implement the same contract).
"""

from __future__ import annotations

import abc
from collections.abc import Iterator

import numpy as np

try:  # pragma: no cover
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


class VideoSource(abc.ABC):
    @abc.abstractmethod
    def frames(self) -> Iterator[np.ndarray]:
        ...

    def close(self) -> None:  # noqa: B027 - optional override, not abstract
        """Release capture resources. Overridable; default is a no-op."""


class OpenCVSource(VideoSource):
    """Reads from any OpenCV-decodable source (file, RTSP, device index)."""

    def __init__(self, uri: str | int, loop: bool = False) -> None:
        self._uri = uri
        self._loop = loop
        self._cap = None

    def frames(self) -> Iterator[np.ndarray]:
        if cv2 is None:
            raise RuntimeError("OpenCV not available for video capture")
        self._cap = cv2.VideoCapture(self._uri)
        if not self._cap.isOpened():
            raise RuntimeError(f"cannot open video source: {self._uri}")
        while True:
            ok, frame = self._cap.read()
            if not ok:
                if self._loop:
                    self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            yield frame
        self.close()

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class SyntheticSource(VideoSource):
    """Procedurally generated frames — hardware-free demo/testing."""

    def __init__(self, width: int = 1280, height: int = 720, n_frames: int | None = None) -> None:
        self._w = width
        self._h = height
        self._n = n_frames

    def frames(self) -> Iterator[np.ndarray]:
        i = 0
        while self._n is None or i < self._n:
            frame = np.full((self._h, self._w, 3), 40, dtype=np.uint8)
            # Simple perspective "rails" so the corridor overlay looks plausible.
            if cv2 is not None:
                cx = self._w // 2
                top = int(self._h * 0.45)
                rail = (120, 120, 120)
                cv2.line(frame, (cx - 20, top), (cx - 400, self._h), rail, 4)
                cv2.line(frame, (cx + 20, top), (cx + 400, self._h), rail, 4)
            i += 1
            yield frame
