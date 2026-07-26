"""Small shared widget helpers."""

from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class Card(QFrame):
    """A rounded panel with an optional uppercase title (matches web cards)."""

    def __init__(self, title: str | None = None) -> None:
        super().__init__()
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 12)
        self._layout.setSpacing(8)
        if title:
            lbl = QLabel(title.upper())
            lbl.setObjectName("CardTitle")
            self._layout.addWidget(lbl)

    def body(self) -> QVBoxLayout:
        return self._layout
