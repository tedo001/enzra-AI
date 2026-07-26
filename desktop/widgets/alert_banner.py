"""Color-coded alert banner with a pulsing effect at high/critical levels."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel

from desktop.theme import ALERT_COLORS


class AlertBanner(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(58)
        self._level = "safe"
        self._pulse_on = True

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)
        self._icon = QLabel("🛡")
        self._icon.setStyleSheet("font-size:22px;")
        self._title = QLabel("SAFE")
        self._title.setStyleSheet("font-size:13px; font-weight:700;")
        self._msg = QLabel("Awaiting stream…")
        self._msg.setStyleSheet("font-size:13px;")
        col = QHBoxLayout()
        col.addWidget(self._title)
        lay.addWidget(self._icon)
        lay.addLayout(col)
        lay.addSpacing(10)
        lay.addWidget(self._msg, 1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._blink)
        self._apply()

    def set_alert(self, level: str, recommendation: str) -> None:
        self._level = level
        self._icon.setText("🛡" if level == "safe" else "⚠")
        self._title.setText(f"{level.upper()} ALERT" if level != "safe" else "SAFE")
        self._msg.setText(recommendation)
        if level in ("high", "critical"):
            if not self._timer.isActive():
                self._timer.start(450)
        else:
            self._timer.stop()
            self._pulse_on = True
        self._apply()

    def _blink(self) -> None:
        self._pulse_on = not self._pulse_on
        self._apply()

    def _apply(self) -> None:
        c = QColor(ALERT_COLORS.get(self._level, "#22c55e"))
        alpha = 40 if self._pulse_on else 18
        self.setStyleSheet(
            f"QFrame {{ background: rgba({c.red()},{c.green()},{c.blue()},{alpha});"
            f" border:1px solid {c.name()}; border-radius:12px; }}"
        )
        self._title.setStyleSheet(
            f"color:{c.name()}; font-size:13px; font-weight:700;"
        )
        self._icon.setStyleSheet(f"font-size:22px; color:{c.name()};")
        self._msg.setAlignment(Qt.AlignmentFlag.AlignVCenter)
