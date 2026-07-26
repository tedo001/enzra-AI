"""RailVision AI — PyQt6 desktop application.

A single self-contained desktop app that runs the full RailVision inference
pipeline (the "backend") and renders a native dashboard (the "frontend") in one
process. It reuses the backend package under ``../backend`` directly, so there
is no FastAPI server or web frontend to run.

Importing this package makes the backend importable: we prepend the sibling
``backend`` directory to ``sys.path`` here, so every ``desktop.*`` submodule can
``import app...`` without requiring ``pip install -e backend``.
"""

import sys as _sys
from pathlib import Path as _Path

__version__ = "0.1.0"

_BACKEND = _Path(__file__).resolve().parents[1] / "backend"
if _BACKEND.is_dir() and str(_BACKEND) not in _sys.path:
    _sys.path.insert(0, str(_BACKEND))
