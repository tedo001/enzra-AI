"""Health & readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.api.dependencies import get_container
from app.container import Container
from app.schemas import HealthStatus

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthStatus)
async def health(container: Container = Depends(get_container)) -> HealthStatus:
    return HealthStatus(
        version=__version__,
        device=container.detector.device,
        model_loaded=container.detector.is_loaded,
        detector_backend=container.detector.backend_name,
        uptime_s=round(container.uptime_s, 1),
    )


@router.get("/ready")
async def ready(container: Container = Depends(get_container)) -> dict:
    return {"ready": container.detector.is_loaded}
