"""Collision-risk prediction engine.

Combines four physical/heuristic signals into a 0–100 risk score and a
discrete :class:`AlertLevel`:

1. **Time-to-collision (TTC)** — distance / closing speed.
2. **Proximity** — absolute distance vs. emergency braking distance.
3. **On-track** — obstacles inside the corridor dominate risk.
4. **Class severity** — large/living obstacles weighted higher.

Relative speed is derived from the change in estimated distance across frames
for each track (a persistent ``track_id`` is required for a velocity estimate;
single-frame detections are treated as stationary worst-case).
"""

from __future__ import annotations

from app.config import Settings
from app.schemas import AlertLevel, Detection, ObstacleClass

# Per-class severity multiplier (0..1) — larger/heavier ⇒ worse outcome.
CLASS_SEVERITY: dict[ObstacleClass, float] = {
    ObstacleClass.HUMAN: 1.0,
    ObstacleClass.ELEPHANT: 1.0,
    ObstacleClass.TRUCK: 0.95,
    ObstacleClass.BUS: 0.95,
    ObstacleClass.COW: 0.85,
    ObstacleClass.BUFFALO: 0.85,
    ObstacleClass.CAR: 0.85,
    ObstacleClass.FALLEN_TREE: 0.8,
    ObstacleClass.CONSTRUCTION_BARRIER: 0.75,
    ObstacleClass.ROCK: 0.7,
    ObstacleClass.MOTORCYCLE: 0.65,
    ObstacleClass.DOG: 0.6,
    ObstacleClass.GOAT: 0.6,
    ObstacleClass.DEBRIS: 0.55,
    ObstacleClass.UNKNOWN: 0.7,
}


class CollisionRiskEngine:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._train_mps = settings.train_speed_kmh / 3.6
        self._braking_m = settings.braking_distance_m
        # Per-track previous distance & timestamp for speed estimation.
        self._prev: dict[int, tuple[float, float]] = {}

    def reset(self) -> None:
        self._prev.clear()

    def assess(self, det: Detection, now_s: float) -> Detection:
        """Return a copy of ``det`` enriched with speed/TTC/risk/alert."""
        if not det.on_track or det.distance_m is None:
            return det.model_copy(
                update={"risk_score": 0.0, "alert_level": AlertLevel.SAFE}
            )

        distance = det.distance_m
        closing = self._closing_speed(det, distance, now_s)
        ttc = distance / closing if closing > 0.1 else float("inf")

        risk = self._score(det.label, distance, ttc)
        level = self._level(risk, ttc)

        return det.model_copy(
            update={
                "speed_mps": round(closing, 2),
                "time_to_collision_s": round(ttc, 2) if ttc != float("inf") else None,
                "risk_score": round(risk, 1),
                "alert_level": level,
            }
        )

    # -- internals ----------------------------------------------------------
    def _closing_speed(self, det: Detection, distance: float, now_s: float) -> float:
        """Estimate closing speed (m/s): train speed + obstacle approach rate."""
        approach = 0.0
        if det.track_id is not None and det.track_id in self._prev:
            prev_d, prev_t = self._prev[det.track_id]
            dt = max(now_s - prev_t, 1e-3)
            approach = (prev_d - distance) / dt  # +ve ⇒ getting closer
        if det.track_id is not None:
            self._prev[det.track_id] = (distance, now_s)
        # Train always advances; obstacle motion adds/subtracts.
        return max(0.0, self._train_mps + approach)

    def _score(self, label: ObstacleClass, distance: float, ttc: float) -> float:
        severity = CLASS_SEVERITY.get(label, 0.7)

        # Proximity component: 1 when at braking distance, →0 far away.
        prox = max(0.0, 1.0 - distance / self._braking_m)

        # TTC component: sharp rise as TTC drops below ~15s.
        ttc_c = 0.0 if ttc == float("inf") else max(0.0, min(1.0, 1.0 - ttc / 15.0))

        raw = (0.55 * ttc_c + 0.45 * prox) * (0.6 + 0.4 * severity)
        return max(0.0, min(100.0, raw * 100.0))

    @staticmethod
    def _level(risk: float, ttc: float) -> AlertLevel:
        if ttc != float("inf") and ttc < 4.0:
            return AlertLevel.CRITICAL
        if risk >= 80:
            return AlertLevel.CRITICAL
        if risk >= 60:
            return AlertLevel.HIGH
        if risk >= 40:
            return AlertLevel.MEDIUM
        if risk >= 20:
            return AlertLevel.LOW
        return AlertLevel.SAFE
