"""Shared pytest fixtures."""

from __future__ import annotations

import os

# Force a hardware-free, standalone configuration for the test session BEFORE
# the application (and its cached settings) are imported by any test module.
os.environ.setdefault("RV_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("RV_ENV", "development")
os.environ.setdefault("RV_ENABLE_VOICE_ALERTS", "false")

import numpy as np
import pytest

from app.config import Settings
from app.schemas import BoundingBox, Detection, ObstacleClass


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        camera_focal_px=1400.0,
        camera_height_m=3.5,
        train_speed_kmh=60.0,
    )


@pytest.fixture
def blank_frame() -> np.ndarray:
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def person_on_track() -> Detection:
    # Foot point near bottom-center → inside corridor.
    return Detection(
        label=ObstacleClass.HUMAN,
        raw_label="person",
        confidence=0.9,
        box=BoundingBox(x1=620, y1=400, x2=660, y2=680),
    )
