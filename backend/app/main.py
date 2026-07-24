"""RailVision AI — FastAPI application entrypoint.

Wires the composition root into the app lifespan, mounts routers, and applies
CORS. Run with:

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routers import analytics, detection, health, stream
from app.config import get_settings
from app.container import Container
from app.logging_config import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level, json_logs=settings.is_production)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting RailVision AI", version=__version__, env=settings.env)
    container = Container(settings)
    await container.startup()
    app.state.container = container
    try:
        yield
    finally:
        await container.shutdown()
        log.info("RailVision AI stopped")


app = FastAPI(
    title="RailVision AI",
    description="Real-time railway hazard detection & collision-risk platform (YOLO26).",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(detection.router)
app.include_router(analytics.router)
app.include_router(stream.router)


@app.get("/", tags=["system"])
async def root() -> dict:
    return {
        "name": "RailVision AI",
        "version": __version__,
        "docs": "/docs",
        "websocket": "/stream/ws",
        "mjpeg": "/stream/mjpeg",
    }
