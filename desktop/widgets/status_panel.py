"""System-status panel: detector backend, device, model, frames, uptime."""

from __future__ import annotations

import time

from PyQt6.QtWidgets import QFormLayout, QLabel

from desktop.theme import FG, MUTED
from desktop.widgets.common import Card


class StatusPanel(Card):
    def __init__(self) -> None:
        super().__init__("System Status")
        self._start = time.monotonic()
        self._frames = 0
        self._values: dict[str, QLabel] = {}
        form = QFormLayout()
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(6)
        for key in ("Stream", "Detector", "Device", "Model", "Frames", "Uptime"):
            k = QLabel(key)
            k.setStyleSheet(f"color:{MUTED}; font-size:12px;")
            v = QLabel("—")
            v.setStyleSheet(f"color:{FG}; font-size:12px; font-weight:600;")
            self._values[key] = v
            form.addRow(k, v)
        self.body().addLayout(form)

    def set_static(self, backend: str, device: str, model_loaded: bool) -> None:
        self._values["Detector"].setText(backend)
        self._values["Device"].setText(device)
        self._values["Model"].setText("Loaded" if model_loaded else "Fallback")

    def set_stream(self, running: bool) -> None:
        self._values["Stream"].setText("Running" if running else "Stopped")

    def tick(self) -> None:
        self._frames += 1
        self._values["Frames"].setText(str(self._frames))
        self._values["Uptime"].setText(f"{time.monotonic() - self._start:.0f}s")
