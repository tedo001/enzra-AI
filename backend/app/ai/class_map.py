"""Mapping from raw model class names to the RailVision obstacle taxonomy.

A custom-trained RailVision YOLO26 model emits the canonical class names
directly. When running on a generic COCO-pretrained model (the zero-config
fallback), we remap COCO labels into the railway taxonomy so the platform is
useful out-of-the-box, before any custom training.
"""

from __future__ import annotations

from app.schemas import ObstacleClass

# COCO-80 → RailVision taxonomy. Unmapped COCO classes are ignored as noise.
COCO_TO_RAILVISION: dict[str, ObstacleClass] = {
    "person": ObstacleClass.HUMAN,
    "bicycle": ObstacleClass.MOTORCYCLE,
    "motorcycle": ObstacleClass.MOTORCYCLE,
    "car": ObstacleClass.CAR,
    "bus": ObstacleClass.BUS,
    "truck": ObstacleClass.TRUCK,
    "cow": ObstacleClass.COW,
    "elephant": ObstacleClass.ELEPHANT,
    "dog": ObstacleClass.DOG,
    "sheep": ObstacleClass.GOAT,   # closest COCO analogue for goat/sheep
    "horse": ObstacleClass.COW,    # large quadruped fallback
    "bird": ObstacleClass.UNKNOWN,
}

# Canonical name → enum, for a custom RailVision-trained model.
RAILVISION_NATIVE: dict[str, ObstacleClass] = {c.value: c for c in ObstacleClass}


def resolve_class(raw_label: str) -> ObstacleClass:
    """Resolve a raw detector label into an :class:`ObstacleClass`.

    Resolution order: native RailVision names → COCO remap → ``UNKNOWN``.
    """
    key = raw_label.strip().lower().replace(" ", "_")
    if key in RAILVISION_NATIVE:
        return RAILVISION_NATIVE[key]
    if key in COCO_TO_RAILVISION:
        return COCO_TO_RAILVISION[key]
    return ObstacleClass.UNKNOWN
