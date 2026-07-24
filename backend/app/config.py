"""Centralised configuration using pydantic-settings.

All runtime configuration is sourced from environment variables (prefixed
``RV_``) or an ``.env`` file. A single cached :class:`Settings` instance is
exposed via :func:`get_settings` so the rest of the codebase depends on an
injectable object rather than reading ``os.environ`` directly (Clean
Architecture — configuration is a boundary concern).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Device = Literal["auto", "cpu"] | str
Environment = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_prefix="RV_",
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    env: Environment = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # --- AI / Inference ---
    model_path: str = "models/weights/railvision_yolo26.pt"
    device: Device = "auto"
    conf_threshold: float = 0.35
    iou_threshold: float = 0.5
    img_size: int = 640
    half_precision: bool = True
    max_det: int = 100
    tracker: Literal["bytetrack", "botsort", "centroid"] = "bytetrack"

    # --- Segmentation ---
    seg_model_path: str = "models/weights/railvision_seg.pt"
    corridor_mode: Literal["geometric", "model", "hybrid"] = "hybrid"

    # --- Depth / distance calibration ---
    camera_height_m: float = 3.5
    camera_focal_px: float = 1400.0
    track_gauge_m: float = 1.435

    # --- Collision risk ---
    train_speed_kmh: float = 60.0
    braking_distance_m: float = 800.0

    # --- Database / cache ---
    database_url: str = "postgresql+asyncpg://railvision:railvision@localhost:5432/railvision"
    redis_url: str = "redis://localhost:6379/0"

    # --- Storage ---
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_dir: str = "storage"
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "railvision-incidents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    # --- Alerts ---
    enable_voice_alerts: bool = True
    alert_cooldown_s: float = 5.0

    # --- MLOps ---
    mlflow_tracking_uri: str = "http://localhost:5000"
    experiment_name: str = "railvision-detection"

    @field_validator("cors_origins")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def storage_path(self) -> Path:
        p = Path(self.storage_local_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""
    return Settings()
