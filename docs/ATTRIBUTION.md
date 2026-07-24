# Attribution & Reference Study

RailVision AI is an **original, clean-room implementation**. No source code was
copied. This document credits the public reference project we studied for
inspiration and records exactly what we learned, what we re-implemented
independently, and how RailVision improves on it.

## Reference project

- **Railway Track Obstacle Detection System** — `tedo001/-Railway-Track-Obstacle-Detection-System`
  <https://github.com/tedo001/-Railway-Track-Obstacle-Detection-System>
- License: **MIT** (Copyright © 2026). Compatible with RailVision's MIT license.

We reviewed its architecture and modules (`yolo_detector.py`,
`detection_merger.py`, `track_detector.py`, `roi_analyzer.py`, `pipeline.py`,
`visualizer.py`, `config.py`) to understand its approach. We then designed and
wrote our own system from scratch.

## Ideas we studied and re-implemented independently

| Reference concept | RailVision clean-room implementation | Improvement |
|---|---|---|
| Dual YOLO models (custom fallen-tree + COCO) run concurrently | `app/ai/ensemble_detector.py` — an `EnsembleDetector` composing **N** `BaseDetector`s | Generalised to any number of models; each is a swappable, independently-loaded backend behind the same interface (LSP). |
| Cross-model greedy IoU merge (`detection_merger.py`) | `app/ai/nms.py` — `cross_model_nms()` over typed `Detection`s | Operates on Pydantic contracts; adds a configurable **source-priority bonus** so a specialist wins ties without mutating reported confidence. |
| Mask-based bbox↔ROI overlap ("any pixel ⇒ danger") | `CorridorSegmenter.overlap_ratio()` + combined foot-point OR overlap test | Uses an **overlap-ratio threshold** instead of "any single pixel", removing the reference's over-triggering on tall trackside objects; still catches obstacles lying *across* the rails. |
| ROI polygon EMA temporal smoothing + periodic re-detection | `CorridorSegmenter.update_model_polygon()` (EMA) + `RV_TRACK_DETECTION_INTERVAL` | Same jitter-reduction, wired for the optional YOLO26-seg model mode. |
| COCO class filtering to classes of interest | `app/ai/class_map.py` COCO→taxonomy remap | Maps into a canonical 15-class railway taxonomy with living/large-obstacle semantics used by risk scoring. |
| Per-N-frame track detection for performance | `RV_TRACK_DETECTION_INTERVAL` config | Same idea, decoupled from the detector cadence. |

## Bug we identified in the reference (and avoided)

In the reference, `roi_analyzer.classify_detections()` never populates
`warning_dets`, yet `get_track_status()` has a WARNING branch — so the WARNING
state is unreachable dead code. RailVision replaces the binary DANGER/SAFE +
dead WARNING with a physically-grounded **5-level alert** (`safe → low → medium
→ high → critical`) driven by distance and time-to-collision.

## Capabilities RailVision adds beyond the reference

The reference is a single-process, script-driven video annotator. RailVision
adds, as original work:

- **Object tracking** with persistent IDs (`app/tracking`).
- **Monocular distance estimation** via ground-plane geometry (`app/depth`).
- **Collision-risk engine**: relative speed, time-to-collision, 0–100 risk
  score, 5-level alerts (`app/detection/risk.py`).
- **Smart alerts**: visual + voice + emergency recommendations (`app/alerts`).
- **Incident recording**: snapshots, clips, logs, JSON metadata (`app/analytics`).
- **FastAPI** REST + WebSocket + MJPEG serving; **Next.js** dashboard.
- **PostgreSQL/Redis/S3**, Docker Compose, CI, tests, and MLOps
  (train/evaluate/benchmark/ONNX+TensorRT export, MLflow, DVC).
- **Clean Architecture** (SOLID, repository pattern, DI composition root).
- **YOLO26** in place of YOLO11, isolated behind a pluggable interface.

## Third-party libraries

See [`LICENSE`](../LICENSE) for the full third-party attribution list
(Ultralytics YOLO — AGPL-3.0; OpenCV — Apache-2.0; PyTorch — BSD-3-Clause;
FastAPI/Next.js — MIT).
