"""Table of on-track obstacles, sorted by risk (highest first)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from desktop.theme import ALERT_COLORS

_COLS = ["Class", "ID", "Distance", "TTC", "Speed", "Risk"]


class DetectionTable(QTableWidget):
    def __init__(self) -> None:
        super().__init__(0, len(_COLS))
        self.setHorizontalHeaderLabels(_COLS)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setShowGrid(False)
        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(_COLS)):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def update_from(self, result) -> None:
        rows = sorted(
            (d for d in result.detections if d.on_track),
            key=lambda d: d.risk_score,
            reverse=True,
        )
        self.setRowCount(len(rows))
        for r, d in enumerate(rows):
            color = QColor(ALERT_COLORS.get(d.alert_level.value, "#e6edf7"))
            cells = [
                d.label.value.replace("_", " ").title(),
                "—" if d.track_id is None else f"#{d.track_id}",
                "—" if d.distance_m is None else f"{d.distance_m:.0f} m",
                "—" if d.time_to_collision_s is None else f"{d.time_to_collision_s:.1f} s",
                "—" if d.speed_mps is None else f"{d.speed_mps:.1f} m/s",
                f"{d.risk_score:.0f}",
            ]
            for c, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if c == 0 or c == 5:
                    item.setForeground(color)
                if c >= 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(r, c, item)
