"""Domain schemas shared across the pipeline (Pydantic v2).

These are the *contracts* passed between detection → tracking → segmentation →
depth → risk → alerts. Keeping them in one place enforces a stable, typed
boundary between modules (Clean Architecture: modules depend on these
abstractions, not on each other's internals).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AlertLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return {"safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]


class ObstacleClass(str, Enum):
    """Canonical obstacle taxonomy for railway safety."""

    HUMAN = "human"
    COW = "cow"
    ELEPHANT = "elephant"
    DOG = "dog"
    BUFFALO = "buffalo"
    GOAT = "goat"
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    FALLEN_TREE = "fallen_tree"
    ROCK = "rock"
    CONSTRUCTION_BARRIER = "construction_barrier"
    DEBRIS = "debris"
    UNKNOWN = "unknown"

    @property
    def is_living(self) -> bool:
        return self in {
            ObstacleClass.HUMAN,
            ObstacleClass.COW,
            ObstacleClass.ELEPHANT,
            ObstacleClass.DOG,
            ObstacleClass.BUFFALO,
            ObstacleClass.GOAT,
        }


class BoundingBox(BaseModel):
    """Axis-aligned box in pixel coordinates (xyxy)."""

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)

    @property
    def bottom_center(self) -> tuple[float, float]:
        """Foot point — the most reliable ground-contact reference."""
        return ((self.x1 + self.x2) / 2.0, self.y2)


class Detection(BaseModel):
    """A single detected object in one frame."""

    label: ObstacleClass
    raw_label: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    box: BoundingBox
    track_id: int | None = None
    on_track: bool = False
    distance_m: float | None = None
    speed_mps: float | None = None
    time_to_collision_s: float | None = None
    risk_score: float = 0.0
    alert_level: AlertLevel = AlertLevel.SAFE


class FrameResult(BaseModel):
    """Full per-frame analysis result — the primary API/WS payload."""

    frame_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    width: int
    height: int
    fps: float = 0.0
    inference_ms: float = 0.0
    detections: list[Detection] = Field(default_factory=list)
    corridor_polygon: list[list[int]] = Field(default_factory=list)
    overall_alert: AlertLevel = AlertLevel.SAFE
    recommendation: str = ""

    @property
    def obstacle_count(self) -> int:
        return sum(1 for d in self.detections if d.on_track)


class IncidentRecord(BaseModel):
    """Persisted incident metadata."""

    id: str
    created_at: datetime
    alert_level: AlertLevel
    frame_id: int
    obstacle_classes: list[ObstacleClass]
    min_distance_m: float | None
    max_risk_score: float
    image_path: str | None = None
    clip_path: str | None = None
    metadata_path: str | None = None
    camera_id: str = "cam-0"


class HealthStatus(BaseModel):
    status: str = "ok"
    version: str
    device: str
    model_loaded: bool
    detector_backend: str
    uptime_s: float
