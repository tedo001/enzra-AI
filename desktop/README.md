# RailVision AI — Desktop App (PyQt6)

A **single-process desktop application** that runs the entire RailVision
pipeline *and* the dashboard — no FastAPI server, no Next.js, no browser. It
reuses the backend inference modules (`../backend/app`) directly.

![layout](https://img.shields.io/badge/UI-PyQt6-41CD52) ![offline](https://img.shields.io/badge/runs-offline-blue)

## Run

```bash
# from the repo root
pip install -r desktop/requirements.txt
python -m desktop.main
```

The app boots even with **no GPU, no weights, and no `ultralytics`** — it falls
back to the mock detector so the full UI and pipeline are demonstrable
immediately. Install `ultralytics` + `torch` (and drop trained weights in
`models/weights/`) for real YOLO26 inference.

## What it does (backend + frontend in one)

- **Video sources**: synthetic demo (default, no hardware), webcam, local video
  file, or an RTSP/HTTP stream URL.
- **Live inference** on a background `QThread` (UI stays smooth): enhance →
  detect → track → corridor filter → distance → collision risk → alerts.
- **Dashboard widgets**:
  - Live annotated feed (boxes, corridor, track IDs, distance, risk).
  - Color-coded alert banner (pulses at High/Critical).
  - KPI tiles: FPS, on-track obstacles, top risk, closest distance.
  - Circular collision-risk gauge (0–100).
  - On-track obstacle table (class, ID, distance, TTC, speed, risk).
  - Session analytics: obstacle-frequency bar chart + incident count.
  - System status: detector backend, device, model, frames, uptime.
- **Voice alerts** via offline TTS (`pyttsx3`), throttled by cooldown.
- **Incident recording**: annotated snapshot + video clip + JSON metadata,
  indexed in a local SQLite DB (`storage/railvision_desktop.db`).
- **Live tuning**: confidence and corridor-overlap sliders apply instantly.
- **Snapshot** button saves the current annotated frame.

## Architecture

```
desktop/
├── main.py                 # entry point (python -m desktop.main)
├── main_window.py          # assembles UI, wires worker ↔ widgets
├── pipeline_factory.py     # builds the reused RailVisionPipeline (backend)
├── incident_store.py       # synchronous SQLite + file evidence store
├── voice.py                # non-blocking TTS announcer
├── theme.py                # dark Qt stylesheet
├── workers/
│   └── inference_worker.py # QThread: capture → pipeline → signals
└── widgets/                # video view, gauge, banner, tiles, table, …
```

The inference core is UI-agnostic: `pipeline_factory` builds the same
`RailVisionPipeline` the API server uses, so behavior is identical across the
web and desktop front-ends. The worker communicates with the GUI purely through
Qt signals (thread-safe), keeping rendering off the inference thread.

## Notes

- Uses `opencv-python` (full build) rather than the headless build the backend
  pins, because desktop capture needs the GUI/codec components.
- All processing is local; nothing leaves the machine.
