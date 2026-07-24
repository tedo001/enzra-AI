# Installation Guide

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10–3.12 | backend |
| Node.js | 20+ | frontend |
| Docker + Compose | latest | full-stack option |
| NVIDIA GPU + CUDA 12 | optional | real-time YOLO26 inference |

## 1. Clone & configure

```bash
git clone <repo-url> railvision-ai && cd railvision-ai
cp .env.example .env      # edit as needed
```

## 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # core + dev tooling
```

Optional extras:

```bash
pip install -e ".[ai]"    # ultralytics (YOLO26) + torch + onnxruntime
pip install -e ".[s3]"    # S3 / MinIO storage
pip install -e ".[mlops]" # mlflow + dvc
```

> **GPU:** install a CUDA build of PyTorch matching your driver, e.g.
> `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`,
> then set `RV_DEVICE=cuda:0` in `.env`.

Run it:

```bash
uvicorn app.main:app --reload
# http://localhost:8000/docs
```

Without the `[ai]` extra or weights, the backend boots on the **mock detector**
so you can develop the full stack with zero ML dependencies.

## 3. Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
```

## 4. Database & cache (optional locally)

The backend falls back to in-memory SQLite if Postgres is unreachable. For the
real thing:

```bash
docker compose up -d postgres redis minio
```

## 5. Verify

```bash
cd backend
pytest                                   # 17 tests should pass
python -m app.mlops.benchmark --frames 100
curl http://localhost:8000/health
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ultralytics not installed` warning | expected without `[ai]`; using mock detector |
| `libGL.so.1` error | `apt-get install libgl1` (Docker image already includes it) |
| WebSocket won't connect | check `NEXT_PUBLIC_WS_URL` and CORS `RV_CORS_ORIGINS` |
| Postgres connection refused | `docker compose up -d postgres` or rely on SQLite fallback |
