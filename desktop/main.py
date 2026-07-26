"""Entry point for the RailVision AI desktop application.

Run with:

    python -m desktop.main

The app runs the full inference pipeline in-process (no server needed) and
displays a native dashboard. It boots even without a GPU, trained weights, or
the ``[ai]`` extra by falling back to the mock detector.
"""

from __future__ import annotations

import sys

from app.config import get_settings
from app.logging_config import configure_logging

import desktop  # noqa: F401  (package import extends sys.path for `app`)


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)

    from PyQt6.QtWidgets import QApplication

    from desktop.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("RailVision AI")
    window = MainWindow(settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
