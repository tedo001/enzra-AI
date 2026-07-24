# API Reference

Base URL: `http://localhost:8000` · Interactive docs: `/docs` (Swagger) · `/redoc`

## System

### `GET /`
Service metadata and entrypoints.

### `GET /health` → `HealthStatus`
```json
{
  "status": "ok",
  "version": "0.1.0",
  "device": "cuda:0",
  "model_loaded": true,
  "detector_backend": "yolo26-ultralytics",
  "uptime_s": 1234.5
}
```

### `GET /ready`
Readiness probe: `{ "ready": true }`.

## Detection

### `POST /api/detect` (multipart) → `FrameResult`
Run the full pipeline on a single uploaded image.

```bash
curl -F "file=@track.jpg" http://localhost:8000/api/detect
```

`FrameResult` (abridged):
```json
{
  "frame_id": 1,
  "width": 1280, "height": 720,
  "fps": 31.2, "inference_ms": 18.4,
  "overall_alert": "high",
  "recommendation": "Human at 42 m. Apply service brake and prepare to stop.",
  "corridor_polygon": [[600,324],[680,324],[1177,720],[103,720]],
  "detections": [{
    "label": "human", "confidence": 0.87,
    "box": {"x1": 620,"y1": 400,"x2": 660,"y2": 680},
    "track_id": 3, "on_track": true,
    "distance_m": 42.0, "speed_mps": 16.7,
    "time_to_collision_s": 2.5, "risk_score": 88.0,
    "alert_level": "critical"
  }]
}
```

## Streaming

### `WS /stream/ws`
Pushes one `FrameResult` JSON per frame (~30 FPS). Adds `weather` and, when an
alert fires, a `voice_alert` phrase for TTS.

```js
const ws = new WebSocket("ws://localhost:8000/stream/ws");
ws.onmessage = (e) => render(JSON.parse(e.data));
```

### `GET /stream/mjpeg`
`multipart/x-mixed-replace` stream of annotated JPEG frames — embeddable in an
`<img>` tag.

## Analytics

### `GET /api/analytics/daily?day=YYYY-MM-DD`
Daily report: totals, obstacle frequency, incidents by level, closest obstacle.

### `GET /api/analytics/stats`
Aggregate statistics across all recorded data.

### `GET /api/analytics/incidents?limit=50`
Recent incident history (most recent first).

## Enums

- **AlertLevel**: `safe`, `low`, `medium`, `high`, `critical`
- **ObstacleClass**: `human, cow, elephant, dog, buffalo, goat, car, truck, bus,
  motorcycle, fallen_tree, rock, construction_barrier, debris, unknown`
