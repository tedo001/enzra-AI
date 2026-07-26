"""Control panel — source selection, start/stop, live threshold tuning."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
)

from desktop.theme import MUTED
from desktop.widgets.common import Card


class ControlPanel(Card):
    startRequested = pyqtSignal(dict)  # source spec
    stopRequested = pyqtSignal()
    confChanged = pyqtSignal(float)
    overlapChanged = pyqtSignal(float)
    voiceToggled = pyqtSignal(bool)
    snapshotRequested = pyqtSignal()

    def __init__(self, *, voice_available: bool) -> None:
        super().__init__("Controls")
        b = self.body()

        # Source selection.
        self._source = QComboBox()
        self._source.addItems(["Synthetic (demo)", "Webcam", "Video file…", "Stream URL"])
        self._source.currentIndexChanged.connect(self._on_source_change)
        b.addWidget(QLabel("Video source"))
        b.addWidget(self._source)

        self._uri = QLineEdit()
        self._uri.setPlaceholderText("rtsp://…  or  /path/to/video.mp4")
        self._uri.setVisible(False)
        b.addWidget(self._uri)

        # Start / stop.
        row = QHBoxLayout()
        self._start = QPushButton("▶  Start")
        self._stop = QPushButton("■  Stop")
        self._stop.setObjectName("Ghost")
        self._stop.setEnabled(False)
        self._start.clicked.connect(self._on_start)
        self._stop.clicked.connect(self._on_stop)
        row.addWidget(self._start)
        row.addWidget(self._stop)
        b.addLayout(row)

        b.addWidget(self._divider())

        # Confidence slider.
        self._conf = self._slider(5, 95, 35)
        self._conf_lbl = QLabel("Confidence: 0.35")
        self._conf.valueChanged.connect(self._on_conf)
        b.addWidget(self._conf_lbl)
        b.addWidget(self._conf)

        # Overlap ratio slider.
        self._overlap = self._slider(0, 60, 12)
        self._overlap_lbl = QLabel("Corridor overlap: 0.12")
        self._overlap.valueChanged.connect(self._on_overlap)
        b.addWidget(self._overlap_lbl)
        b.addWidget(self._overlap)

        b.addWidget(self._divider())

        # Voice + snapshot.
        self._voice = QCheckBox("Voice alerts")
        self._voice.setChecked(voice_available)
        self._voice.setEnabled(voice_available)
        if not voice_available:
            self._voice.setText("Voice alerts (install pyttsx3)")
        self._voice.toggled.connect(self.voiceToggled)
        b.addWidget(self._voice)

        self._snap = QPushButton("📷  Save snapshot")
        self._snap.setObjectName("Ghost")
        self._snap.clicked.connect(self.snapshotRequested)
        b.addWidget(self._snap)
        b.addStretch(1)

    # -- helpers ------------------------------------------------------------
    def _slider(self, lo: int, hi: int, val: int) -> QSlider:
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(lo, hi)
        s.setValue(val)
        return s

    def _divider(self) -> QLabel:
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{MUTED}; margin:6px 0;")
        return line

    def _on_source_change(self, idx: int) -> None:
        self._uri.setVisible(idx in (2, 3))
        if idx == 2:
            path, _ = QFileDialog.getOpenFileName(
                self, "Choose video", "", "Video (*.mp4 *.avi *.mov *.mkv)"
            )
            if path:
                self._uri.setText(path)

    def _source_spec(self) -> dict:
        idx = self._source.currentIndex()
        if idx == 0:
            return {"kind": "synthetic"}
        if idx == 1:
            return {"kind": "webcam", "index": 0}
        if idx == 2:
            return {"kind": "file", "uri": self._uri.text().strip()}
        return {"kind": "url", "uri": self._uri.text().strip()}

    # -- slots --------------------------------------------------------------
    def _on_start(self) -> None:
        self._start.setEnabled(False)
        self._stop.setEnabled(True)
        self._source.setEnabled(False)
        self.startRequested.emit(self._source_spec())

    def _on_stop(self) -> None:
        self.set_stopped()
        self.stopRequested.emit()

    def set_stopped(self) -> None:
        self._start.setEnabled(True)
        self._stop.setEnabled(False)
        self._source.setEnabled(True)

    def _on_conf(self, v: int) -> None:
        self._conf_lbl.setText(f"Confidence: {v/100:.2f}")
        self.confChanged.emit(v / 100.0)

    def _on_overlap(self, v: int) -> None:
        self._overlap_lbl.setText(f"Corridor overlap: {v/100:.2f}")
        self.overlapChanged.emit(v / 100.0)
