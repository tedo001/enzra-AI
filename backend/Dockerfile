# ---------------------------------------------------------------------------
# RailVision AI — backend image
# CPU-friendly base; for GPU use nvidia/cuda + install torch cu121 wheels.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# OpenCV runtime + video codecs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
# Install core deps first (better layer caching). Add [ai] for GPU inference.
RUN pip install --upgrade pip && pip install -e ".[s3]"

COPY app ./app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
