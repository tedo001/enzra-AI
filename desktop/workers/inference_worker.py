"""Inference worker thread.

Runs the RailVision pipeline off the GUI thread so the UI stays responsive at
30+ FPS. Reads frames from a :class:`VideoSource`, enhances them, runs the full
pipeline, records incidents, and emits:

* ``frameReady``   — an annotated ``QImage`` for the video view.
* ``resultReady``  — the :class:`FrameResult` for widgets (gauge/table/alerts).
* ``voiceAlert``   — a phrase to speak (respecting cooldown).
* ``sourceError``  — a human-readable error string.

Live-tunable settings (confidence, overlap ratio) are read from the shared
``PipelineBundle`` each frame, so control-panel changes take effect immediately.
"""

from __future__ import annotations

import contextlib
import time

from app.utils.drawing import draw_frame
from app.utils.enhancement import auto_enhance
from app.utils.video import OpenCVSource, SyntheticSource
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

import desktop  # noqa: F401  (package import extends sys.path for `app`)
from desktop.incident_store import IncidentStore
from desktop.pipeline_factory import PipelineBundle


def _to_qimage(bgr) -> QImage:
    """Convert a BGR uint8 numpy frame to a detached RGB QImage."""
    h, w = bgr.shape[:2]
    rgb = bgr[:, :, ::-1].copy()  # BGR -> RGB, contiguous
    return QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()


class InferenceWorker(QThread):
    frameReady = pyqtSignal(QImage)
    resultReady = pyqtSignal(object)
    voiceAlert = pyqtSignal(str)
    sourceError = pyqtSignal(str)
    started_ok = pyqtSignal()

    def __init__(self, bundle: PipelineBundle, store: IncidentStore) -> None:
        super().__init__()
        self._bundle = bundle
        self._store = store
        self._running = False
        self._source_spec: dict = {"kind": "synthetic"}
        self._target_fps = 30.0
        self._enhance = True
        self._last_frame = None  # keep last annotated frame for snapshot

    # -- configuration ------------------------------------------------------
    def configure(self, source_spec: dict, *, enhance: bool = True) -> None:
        self._source_spec = source_spec
        self._enhance = enhance

    def _make_source(self):
        kind = self._source_spec.get("kind", "synthetic")
        if kind == "synthetic":
            return SyntheticSource(width=1280, height=720)
        if kind == "webcam":
            return OpenCVSource(int(self._source_spec.get("index", 0)))
        if kind in ("file", "url"):
            return OpenCVSource(self._source_spec["uri"], loop=(kind == "file"))
        return SyntheticSource()

    # -- lifecycle ----------------------------------------------------------
    def stop(self) -> None:
        self._running = False

    def run(self) -> None:  # noqa: C901 - linear control loop
        self._running = True
        self._bundle.reset()
        try:
            source = self._make_source()
            frame_iter = source.frames()
        except Exception as exc:  # pragma: no cover - hardware/env dependent
            self.sourceError.emit(str(exc))
            return

        self.started_ok.emit()
        min_dt = 1.0 / self._target_fps
        try:
            for frame in frame_iter:
                if not self._running:
                    break
                t0 = time.perf_counter()

                proc = auto_enhance(frame)[0] if self._enhance else frame
                result = self._bundle.pipeline.process(proc)

                self._store.observe(frame, result)
                self._store.maybe_record(frame, result)

                annotated = draw_frame(proc, result)
                self._last_frame = annotated
                self.frameReady.emit(_to_qimage(annotated))
                self.resultReady.emit(result)

                cue = self._bundle.alerts.voice_cue(result.overall_alert)
                if cue:
                    self.voiceAlert.emit(cue)

                # Pace to target FPS.
                elapsed = time.perf_counter() - t0
                if elapsed < min_dt:
                    self.msleep(int((min_dt - elapsed) * 1000))
        except Exception as exc:  # pragma: no cover
            self.sourceError.emit(str(exc))
        finally:
            with contextlib.suppress(Exception):
                source.close()

    @property
    def last_annotated_frame(self):
        return self._last_frame
