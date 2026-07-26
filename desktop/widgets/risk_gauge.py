"""Custom-painted circular collision-risk gauge (0–100)."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from desktop.theme import ALERT_COLORS, BORDER


class RiskGauge(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(170)
        self._score = 0.0
        self._level = "safe"

    def set_value(self, score: float, level: str) -> None:
        self._score = max(0.0, min(100.0, score))
        self._level = level
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 16
        rect = QRectF((self.width() - side) / 2, 8, side, side)

        # Track ring.
        pen = QPen(QColor(BORDER), 12)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(rect, 0, 360 * 16)

        # Value arc (start at top, clockwise).
        color = QColor(ALERT_COLORS.get(self._level, "#22c55e"))
        pen.setColor(color)
        p.setPen(pen)
        span = int(-self._score / 100.0 * 360 * 16)
        p.drawArc(rect, 90 * 16, span)

        # Center text.
        p.setPen(color)
        p.setFont(QFont("Segoe UI", int(side * 0.22), QFont.Weight.Bold))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._score:.0f}")
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        label_rect = QRectF(rect.x(), rect.y() + side * 0.62, side, 20)
        label_rect.moveLeft(rect.x())
        p.drawText(
            QRectF(rect.x(), rect.bottom() - side * 0.30, side, 20),
            Qt.AlignmentFlag.AlignHCenter,
            self._level.upper(),
        )
        p.end()
