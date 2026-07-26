"""Row of KPI tiles: FPS, on-track count, top risk, closest distance."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from desktop.theme import ALERT_COLORS
from desktop.widgets.common import Card


class _Tile(Card):
    def __init__(self, label: str) -> None:
        super().__init__()
        self._value = QLabel("—")
        self._value.setObjectName("StatValue")
        self._sub = QLabel(label)
        self._sub.setObjectName("StatLabel")
        box = QVBoxLayout()
        box.setSpacing(2)
        box.addWidget(self._value)
        box.addWidget(self._sub)
        self.body().addLayout(box)

    def set(self, value: str, color: str | None = None) -> None:
        self._value.setText(value)
        self._value.setStyleSheet(f"color:{color};" if color else "")


class StatTiles(QWidget):
    def __init__(self) -> None:
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        self.fps = _Tile("FPS")
        self.on_track = _Tile("ON-TRACK OBSTACLES")
        self.top_risk = _Tile("TOP RISK")
        self.closest = _Tile("CLOSEST")
        for t in (self.fps, self.on_track, self.top_risk, self.closest):
            lay.addWidget(t)

    def update_from(self, result) -> None:
        on_track = [d for d in result.detections if d.on_track]
        top = max((d.risk_score for d in on_track), default=0.0)
        dists = [d.distance_m for d in on_track if d.distance_m is not None]
        closest = min(dists) if dists else None
        color = ALERT_COLORS.get(result.overall_alert.value)

        if closest is None:
            closest_txt = "—"
        elif closest >= 1000:
            closest_txt = f"{closest / 1000:.2f} km"
        else:
            closest_txt = f"{closest:.0f} m"

        self.fps.set(f"{result.fps:.0f}")
        self.on_track.set(str(len(on_track)), color if on_track else None)
        self.top_risk.set(f"{top:.0f}", color)
        self.closest.set(closest_txt)
