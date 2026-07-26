"""Session analytics: a custom-painted horizontal bar chart of obstacle
frequency, plus an incident counter. Reads from the IncidentStore."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from desktop.theme import BORDER, MUTED, PRIMARY
from desktop.widgets.common import Card


class _BarChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(180)
        self._data: dict[str, int] = {}

    def set_data(self, data: dict[str, int]) -> None:
        self._data = dict(sorted(data.items(), key=lambda kv: kv[1], reverse=True)[:8])
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._data:
            p.setPen(QColor(MUTED))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No detections yet")
            p.end()
            return
        top = max(self._data.values()) or 1
        n = len(self._data)
        row_h = min(28, (self.height() - 10) / n)
        label_w = 140
        p.setFont(QFont("Segoe UI", 9))
        for i, (name, val) in enumerate(self._data.items()):
            y = int(i * row_h) + 4
            p.setPen(QColor(MUTED))
            p.drawText(
                0, y, label_w - 8, int(row_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                name.replace("_", " ").title(),
            )
            bar_max = self.width() - label_w - 40
            w = int(bar_max * val / top)
            p.fillRect(label_w, y + 4, max(2, w), int(row_h) - 8, QColor(PRIMARY))
            p.fillRect(label_w, y + 4, 1, int(row_h) - 8, QColor(BORDER))
            p.setPen(QColor("#e6edf7"))
            p.drawText(
                label_w + w + 6, y, 34, int(row_h),
                Qt.AlignmentFlag.AlignVCenter, str(val),
            )
        p.end()


class AnalyticsPanel(Card):
    def __init__(self) -> None:
        super().__init__("Obstacle Frequency (session)")
        self._chart = _BarChart()
        self._incidents = QLabel("Incidents recorded: 0")
        self._incidents.setStyleSheet(f"color:{MUTED}; font-size:11px;")
        inner = QVBoxLayout()
        inner.addWidget(self._chart)
        inner.addWidget(self._incidents)
        self.body().addLayout(inner)

    def refresh(self, frequency: dict[str, int], incident_count: int) -> None:
        self._chart.set_data(frequency)
        self._incidents.setText(f"Incidents recorded: {incident_count}")
