# RailVision AI — Backend

The Python inference core and API for **RailVision AI**, a real-time railway
hazard detection & collision-risk platform (YOLO26).

This package (`app`) contains the full pipeline — detection, tracking, corridor
segmentation, distance estimation, collision-risk scoring, alerts, analytics,
incident recording — plus the FastAPI service (REST + WebSocket + MJPEG) and
MLOps scripts. It is consumed by both the web frontend and the PyQt6 desktop
app.

## Install

```bash
pip install -e .            # core
pip install -e ".[ai]"      # + ultralytics (YOLO26) + torch + onnxruntime
pip install -e ".[dev]"     # + test/lint tooling
```

## Run the API

```bash
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

## Test

```bash
pytest        # unit + integration tests
ruff check .  # lint
```

Without the `[ai]` extra or trained weights, the service boots on a mock
detector so the whole stack is demonstrable with zero ML dependencies.

See the [top-level README](../README.md) and [`../docs`](../docs) for the full
project documentation, architecture, and deployment guide.
