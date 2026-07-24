"""Alert manager — derives overall alert level, recommendations and voice cues.

Applies a cooldown so voice/emergency alerts don't storm the operator, and
maps each :class:`AlertLevel` to a concrete, actionable recommendation plus a
short phrase suitable for TTS on the frontend (Web Speech API) or an on-board
annunciator.
"""

from __future__ import annotations

import time

from app.config import Settings
from app.schemas import AlertLevel, Detection, ObstacleClass

RECOMMENDATIONS: dict[AlertLevel, str] = {
    AlertLevel.SAFE: "Track clear. Maintain normal operation.",
    AlertLevel.LOW: "Obstacle detected near corridor. Stay alert and monitor.",
    AlertLevel.MEDIUM: "Obstacle on track ahead. Reduce speed and sound horn.",
    AlertLevel.HIGH: "Hazard on track. Apply service brake and prepare to stop.",
    AlertLevel.CRITICAL: "COLLISION IMMINENT. Apply emergency brake NOW and sound horn.",
}

VOICE_PHRASES: dict[AlertLevel, str] = {
    AlertLevel.SAFE: "",
    AlertLevel.LOW: "Caution. Obstacle nearby.",
    AlertLevel.MEDIUM: "Warning. Obstacle on the track ahead.",
    AlertLevel.HIGH: "Danger. Hazard on track. Brake now.",
    AlertLevel.CRITICAL: "Emergency. Collision imminent. Emergency brake.",
}


class AlertManager:
    def __init__(self, settings: Settings) -> None:
        self._cooldown = settings.alert_cooldown_s
        self._voice_enabled = settings.enable_voice_alerts
        self._last_voice_at: float = 0.0
        self._last_voice_level: AlertLevel = AlertLevel.SAFE

    def overall_level(self, detections: list[Detection]) -> AlertLevel:
        level = AlertLevel.SAFE
        for det in detections:
            if det.alert_level.rank > level.rank:
                level = det.alert_level
        return level

    def recommendation(self, level: AlertLevel, detections: list[Detection]) -> str:
        base = RECOMMENDATIONS[level]
        if level.rank >= AlertLevel.MEDIUM.rank:
            worst = self._worst(detections)
            if worst is not None:
                cls = worst.label.value.replace("_", " ")
                dist = f"{worst.distance_m:.0f} m" if worst.distance_m else "unknown range"
                base = f"{cls.title()} at {dist}. {base}"
        return base

    def voice_cue(self, level: AlertLevel) -> str | None:
        """Return a TTS phrase respecting cooldown; ``None`` when suppressed."""
        if not self._voice_enabled or level == AlertLevel.SAFE:
            return None
        now = time.monotonic()
        escalated = level.rank > self._last_voice_level.rank
        if escalated or (now - self._last_voice_at) >= self._cooldown:
            self._last_voice_at = now
            self._last_voice_level = level
            return VOICE_PHRASES[level]
        return None

    @staticmethod
    def _worst(detections: list[Detection]) -> Detection | None:
        candidates = [d for d in detections if d.on_track]
        if not candidates:
            return None
        return max(candidates, key=lambda d: d.risk_score)

    @staticmethod
    def emergency_class_priority(detections: list[Detection]) -> ObstacleClass | None:
        living = [d for d in detections if d.on_track and d.label.is_living]
        if living:
            return max(living, key=lambda d: d.risk_score).label
        return None
