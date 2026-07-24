"""FastAPI dependency providers.

Expose container-held singletons to routers via ``Depends``. The container is
attached to ``app.state`` during the lifespan handler in :mod:`app.main`.
"""

from __future__ import annotations

from fastapi import Request

from app.analytics.reporter import AnalyticsService
from app.container import Container
from app.detection.pipeline import RailVisionPipeline


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_pipeline(request: Request) -> RailVisionPipeline:
    return request.app.state.container.pipeline


def get_analytics(request: Request) -> AnalyticsService:
    return request.app.state.container.analytics
