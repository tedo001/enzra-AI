<div align="center">

# 🚆 RailVision AI

**Real-time Railway Hazard Detection & Collision-Risk Platform**

Computer-vision safety system that detects obstacles on railway tracks, tracks
them across frames, estimates distance, and predicts collision risk in
real time — powered by **YOLO26**.

`FastAPI` · `YOLO26` · `PyTorch` · `OpenCV` · `Next.js` · `TypeScript` · `PostgreSQL` · `Redis` · `Docker`

</div>

---

## ✨ Why RailVision AI

Trains cannot stop quickly — an obstacle spotted too late is a disaster.
RailVision AI turns a single forward-facing camera into a safety co-pilot that
sees hazards, judges *how dangerous* each one is, and alerts the operator with
enough lead time to act.

This is a **clean-room, from-scratch** implementation. Concepts were studied
from a public reference project
([`-Railway-Track-Obstacle-Detection-System`](https://github.com/tedo001/-Railway-Track-Obstacle-Detection-System),
MIT) for inspiration only; **no code was copied** — see
[`docs/ATTRIBUTION.md`](docs/ATTRIBUTION.md). It deliberately advances beyond it:

| Reference project | RailVision AI improvement |
|---|---|
| YOLO11 detector | **YOLO26** with a pluggable `BaseDetector` (swap ONNX/TensorRT/mock) |
| Dual fixed models (fallen-tree + COCO) | **N-model `EnsembleDetector`** fused by cross-model NMS with specialist priority |
| "Any pixel overlaps ⇒ danger" ROI test | **Foot-point OR overlap-ratio** test — catches trees lying *across* rails without over-triggering |
| DANGER/SAFE (WARNING is dead code) | Physically-grounded **5-level alerts** from distance + time-to-collision |
| No tracking / distance / risk | **Tracking IDs → distance → TTC → risk 0–100 → alerts** |
| Monolithic script | **Modular Clean Architecture** (SOLID, repository pattern, DI container) |
| Notebook/script demo | **Production stack**: FastAPI + WebSocket, Next.js dashboard, Postgres/Redis, Docker, tests, MLOps |
| Roboflow API dependency; crashes without a GPU/weights | **Graceful degradation** — auto-downloads weights, then falls back to a mock detector so it *always* boots |

## 🧠 How it works

```
 Camera ─▶ Enhance ─▶ YOLO26 ─▶ Tracker ─▶ Corridor ─▶ Distance ─▶ Risk ─▶ Alerts ─▶ Dashboard
          (night/     detect     (IDs +     filter      (ground-    (TTC +   (visual/   (WS + MJPEG)
           fog/rain)             velocity)  (on-track)   plane)      score)   voice)         │
                                                                                  └▶ Incident Recorder ─▶ DB / S3
```

Each arrow is an injected, independently testable stage. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## 🚀 Quick start

### Option A — Docker (full stack)

```bash
cp .env.example .env
docker compose up --build
# Dashboard  → http://localhost:3000
# API docs   → http://localhost:8000/docs
```

### Option B — local dev

```bash
# Backend (runs even with no GPU/weights — mock fallback)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # add ".[ai]" for real YOLO26 inference
uvicorn app.main:app --reload

# Frontend
cd ../frontend
npm install && npm run dev
```

Then open **http://localhost:3000** — the dashboard streams a live feed with
bounding boxes, FPS, risk gauge, obstacle list, alerts and analytics.

## 🧩 Features

**Core**
- Railway **track & corridor segmentation** (geometric / model / hybrid) with
  on-track filtering — detections outside the corridor are ignored.
- **Obstacle detection** across a 15-class taxonomy (humans, cattle, elephants,
  vehicles, fallen trees, rocks, barriers, debris, unknown…).
- **Object tracking** with persistent IDs (ByteTrack-inspired, dependency-free).
- **Distance estimation** via monocular ground-plane geometry + size cross-check.
- **Collision-risk prediction**: relative speed, time-to-collision, risk 0–100,
  and a 5-level alert (`safe → low → medium → high → critical`).
- **Smart alerts**: visual, voice (Web Speech API) and emergency recommendations.
- **Incident recording**: annotated snapshots, video clips, logs and JSON metadata.
- **Dashboard**: live feed, boxes, FPS, counts, obstacle list, risk, alerts, status.
- **Analytics**: daily reports, detection stats, obstacle frequency, incident history.

**Bonus / advanced**
- Adverse-weather enhancement (night / fog / rain) + weather classification.
- Multi-camera & drone/thermal ready (uniform `VideoSource` contract).
- Edge deployment: **ONNX** and **TensorRT** export.
- MLOps: DVC dataset versioning, MLflow experiment tracking + model registry,
  automatic evaluation and benchmark scripts.

## 📁 Repository layout

```
backend/     FastAPI app — api, ai, detection, tracking, segmentation,
             depth, analytics, alerts, database, utils, mlops, tests
frontend/    Next.js + TypeScript + Tailwind + ShadCN-style dashboard
models/      Weights + model-registry docs
datasets/    YOLO-format dataset spec (DVC-versioned)
docs/        Architecture, install, API, deployment, user manual
docker-compose.yml
```

## 🎯 Performance

The pipeline (detect → track → corridor → distance → risk → alerts) is designed
for **30+ FPS** with GPU-accelerated YOLO26 (FP16). Benchmark it:

```bash
cd backend && python -m app.mlops.benchmark --frames 300
```

## 🧪 Tests & quality

```bash
cd backend
pytest          # 17 unit/integration tests (green)
ruff check .    # lint
mypy app        # type-check
```

SOLID · Clean Architecture · Repository pattern · full type hints · structured
logging · centralised configuration.

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Installation](docs/INSTALLATION.md)
- [API reference](docs/API.md)
- [Deployment](docs/DEPLOYMENT.md)
- [User manual](docs/USER_MANUAL.md)

## ⚖️ License & attribution

MIT — see [`LICENSE`](LICENSE). RailVision AI isolates **Ultralytics YOLO
(AGPL-3.0)** behind the `BaseDetector` interface so the core platform stays MIT
and the detector remains swappable. Please respect the licenses of all
referenced projects.
