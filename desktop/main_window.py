"""RailVision AI desktop — main application window.

Assembles the dashboard and wires the inference worker (backend) to the widgets
(frontend). One process does everything: capture, inference, visualization,
alerts, incident recording and analytics.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.config import Settings
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

import desktop  # noqa: F401  (package import extends sys.path for `app`)
from desktop.incident_store import IncidentStore
from desktop.pipeline_factory import build_bundle
from desktop.theme import STYLESHEET
from desktop.voice import VoiceAnnouncer
from desktop.widgets.alert_banner import AlertBanner
from desktop.widgets.analytics_panel import AnalyticsPanel
from desktop.widgets.common import Card
from desktop.widgets.control_panel import ControlPanel
from desktop.widgets.detection_table import DetectionTable
from desktop.widgets.risk_gauge import RiskGauge
from desktop.widgets.stat_tiles import StatTiles
from desktop.widgets.status_panel import StatusPanel
from desktop.widgets.video_view import VideoView
from desktop.workers.inference_worker import InferenceWorker

try:  # optional, only for snapshot writing
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self.setWindowTitle("RailVision AI — Railway Safety (Desktop)")
        self.resize(1400, 900)
        self.setStyleSheet(STYLESHEET)

        self._settings = settings or Settings()
        self._bundle = build_bundle(self._settings)
        self._store = IncidentStore(self._settings.storage_local_dir)
        self._voice = VoiceAnnouncer()
        self._worker: InferenceWorker | None = None
        self._frame_counter = 0

        self._build_ui()
        self._status.set_static(
            self._bundle.backend_name, self._bundle.device, self._bundle.model_loaded
        )

    # -- UI assembly --------------------------------------------------------
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(12)

        outer.addLayout(self._header())

        self._banner = AlertBanner()
        outer.addWidget(self._banner)

        self._tiles = StatTiles()
        outer.addWidget(self._tiles)

        # Main body: video/analytics (left) + controls/gauge/table/status (right)
        body = QHBoxLayout()
        body.setSpacing(12)

        left = QVBoxLayout()
        left.setSpacing(12)
        self._video = VideoView()
        video_card = Card("Live Feed")
        video_card.body().addWidget(self._video, 1)
        left.addWidget(video_card, 3)
        self._analytics = AnalyticsPanel()
        left.addWidget(self._analytics, 2)
        body.addLayout(left, 3)

        right = QVBoxLayout()
        right.setSpacing(12)
        self._controls = ControlPanel(voice_available=self._voice.available)
        right.addWidget(self._controls)

        gauge_card = Card("Collision Risk")
        self._gauge = RiskGauge()
        gauge_card.body().addWidget(self._gauge)
        right.addWidget(gauge_card)

        table_card = Card("Obstacles On Track")
        self._table = DetectionTable()
        table_card.body().addWidget(self._table)
        right.addWidget(table_card, 1)

        self._status = StatusPanel()
        right.addWidget(self._status)
        body.addLayout(right, 2)

        outer.addLayout(body, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Ready")

        self._wire_controls()

    def _header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        h1 = QLabel("🚆  RailVision AI")
        h1.setObjectName("H1")
        sub = QLabel("Railway Hazard Detection · YOLO26 · Real-time Collision Risk")
        sub.setObjectName("Sub")
        title_box.addWidget(h1)
        title_box.addWidget(sub)
        row.addLayout(title_box)
        row.addStretch(1)
        self._pill = QLabel("● Stopped")
        self._pill.setStyleSheet("color:#8aa0c0; font-size:12px;")
        row.addWidget(self._pill, 0, Qt.AlignmentFlag.AlignVCenter)
        return row

    def _wire_controls(self) -> None:
        c = self._controls
        c.startRequested.connect(self._start)
        c.stopRequested.connect(self._stop)
        c.confChanged.connect(self._bundle.set_confidence)
        c.overlapChanged.connect(self._bundle.set_overlap_ratio)
        c.voiceToggled.connect(self._voice.set_enabled)
        c.snapshotRequested.connect(self._save_snapshot)

    # -- worker lifecycle ---------------------------------------------------
    def _start(self, spec: dict) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        worker = InferenceWorker(self._bundle, self._store)
        worker.configure(spec, enhance=True)
        worker.frameReady.connect(self._video.show_frame)
        worker.resultReady.connect(self._on_result)
        worker.voiceAlert.connect(self._voice.announce)
        worker.sourceError.connect(self._on_error)
        worker.started_ok.connect(lambda: self._set_running(True))
        worker.finished.connect(self._on_finished)
        self._worker = worker
        worker.start()
        self.statusBar().showMessage(f"Starting source: {spec.get('kind')}…")

    def _stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(2000)

    def _on_finished(self) -> None:
        self._set_running(False)
        self._controls.set_stopped()
        self.statusBar().showMessage("Stopped")

    def _set_running(self, running: bool) -> None:
        self._status.set_stream(running)
        self._pill.setText("● Running" if running else "● Stopped")
        self._pill.setStyleSheet(
            f"color:{'#22c55e' if running else '#8aa0c0'}; font-size:12px;"
        )

    # -- per-frame updates --------------------------------------------------
    def _on_result(self, result) -> None:
        self._frame_counter += 1
        self._tiles.update_from(result)
        top = max((d.risk_score for d in result.detections if d.on_track), default=0.0)
        self._gauge.set_value(top, result.overall_alert.value)
        self._table.update_from(result)
        self._banner.set_alert(result.overall_alert.value, result.recommendation)
        self._status.tick()
        if self._frame_counter % 20 == 0:
            self._analytics.refresh(
                self._store.frequency(), self._store.incident_count()
            )

    def _on_error(self, message: str) -> None:
        self._set_running(False)
        self._controls.set_stopped()
        self.statusBar().showMessage(f"Source error: {message}")
        self._video.setText(f"⚠ Could not open source\n{message}")

    def _save_snapshot(self) -> None:
        if self._worker is None or cv2 is None:
            self.statusBar().showMessage("Snapshot unavailable (no active stream)")
            return
        frame = self._worker.last_annotated_frame
        if frame is None:
            self.statusBar().showMessage("No frame to capture yet")
            return
        out = Path(self._settings.storage_local_dir) / "snapshots"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"snapshot_{datetime.utcnow():%Y%m%d_%H%M%S}.jpg"
        cv2.imwrite(str(path), frame)
        self.statusBar().showMessage(f"Saved {path}")

    # -- shutdown -----------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._stop()
        self._voice.stop()
        self._store.close()
        super().closeEvent(event)
