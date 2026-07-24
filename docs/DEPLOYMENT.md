# Deployment Guide

## Docker Compose (recommended)

```bash
cp .env.example .env
docker compose up --build -d
```

Services:

| Service | Port | Purpose |
|---|---|---|
| frontend | 3000 | Next.js dashboard |
| backend | 8000 | FastAPI + WS/MJPEG |
| postgres | 5432 | incidents & stats |
| redis | 6379 | cache / pub-sub |
| minio | 9000/9001 | S3-compatible incident storage |

Health checks gate startup order; the backend waits for a healthy Postgres.

## GPU inference

Use a CUDA base image and install the AI extra with a CUDA torch wheel:

```dockerfile
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
# ... python + system libs ...
RUN pip install -e ".[ai]" && \
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Run with `--gpus all` (or the compose `deploy.resources.reservations.devices`
GPU block) and set `RV_DEVICE=cuda:0`, `RV_HALF_PRECISION=true`.

## Edge deployment

1. Export an optimised model:
   ```bash
   python -m app.mlops.export --format onnx      # portable
   python -m app.mlops.export --format engine --half   # Jetson / TensorRT
   ```
2. Deploy the backend only (headless), point a real camera via a `VideoSource`,
   and stream results to a control room over WebSocket.
3. For Jetson: use the TensorRT `.engine`, `RV_IMG_SIZE=640`, FP16.

## Production checklist

- [ ] `RV_ENV=production` (enables JSON structured logs).
- [ ] Set strong DB credentials & a private `RV_DATABASE_URL`.
- [ ] Restrict `RV_CORS_ORIGINS` to your dashboard origin.
- [ ] Put the API behind TLS (reverse proxy: nginx / Traefik) — use `wss://`.
- [ ] Configure S3 (`RV_STORAGE_BACKEND=s3`) with real bucket + keys.
- [ ] Provision GPU + `RV_DEVICE=cuda:0`; verify `python -m app.mlops.benchmark`.
- [ ] Run DB migrations (`alembic upgrade head`) or rely on `create_all` for dev.
- [ ] Set up MLflow (`RV_MLFLOW_TRACKING_URI`) for the model registry.

## Scaling

- **Multi-camera**: run one backend per camera (or one process per feed) and
  fan results into a shared Postgres/Redis; the dashboard can subscribe per
  `camera_id`.
- **Stateless API**: analytics endpoints are read-only and horizontally
  scalable behind a load balancer; streaming is sticky per connection.
