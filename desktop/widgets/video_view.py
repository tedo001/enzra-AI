"""Video display widget — shows the annotated feed, scaled and centered."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel


class VideoView(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(640, 360)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background:#000; border-radius:12px;")
        self.setText("No signal — choose a source and press Start")
        self._pix: QPixmap | None = None

    def show_frame(self, image: QImage) -> None:
        self._pix = QPixmap.fromImage(image)
        self._render()

    def _render(self) -> None:
        if self._pix is None:
            return
        self.setPixmap(
            self._pix.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._render()
        super().resizeEvent(event)
