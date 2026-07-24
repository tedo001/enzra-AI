"""Annotate frames with boxes, tracks, corridor and risk overlays.

Kept separate from the pipeline so rendering is optional (headless inference)
and reusable (incident snapshots, video clips, debug tooling).
"""

from __future__ import annotations

import numpy as np

from app.schemas import AlertLevel, FrameResult

try:  # pragma: no cover
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]

LEVEL_COLORS: dict[AlertLevel, tuple[int, int, int]] = {
    AlertLevel.SAFE: (0, 200, 0),
    AlertLevel.LOW: (0, 200, 200),
    AlertLevel.MEDIUM: (0, 165, 255),
    AlertLevel.HIGH: (0, 80, 255),
    AlertLevel.CRITICAL: (0, 0, 255),
}


def draw_frame(frame: np.ndarray, result: FrameResult) -> np.ndarray:
    """Return an annotated copy of ``frame`` (BGR)."""
    if cv2 is None:
        return frame
    canvas = frame.copy()

    # Corridor overlay.
    if result.corridor_polygon:
        poly = np.array(result.corridor_polygon, dtype=np.int32)
        overlay = canvas.copy()
        cv2.fillPoly(overlay, [poly], (60, 130, 60))
        canvas = cv2.addWeighted(overlay, 0.18, canvas, 0.82, 0)
        cv2.polylines(canvas, [poly], True, (90, 220, 90), 2)

    # Detections.
    for det in result.detections:
        color = LEVEL_COLORS[det.alert_level] if det.on_track else (150, 150, 150)
        x1, y1, x2, y2 = (int(det.box.x1), int(det.box.y1), int(det.box.x2), int(det.box.y2))
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        parts = [det.label.value]
        if det.track_id is not None:
            parts.append(f"#{det.track_id}")
        if det.distance_m is not None:
            parts.append(f"{det.distance_m:.0f}m")
        if det.on_track and det.risk_score > 0:
            parts.append(f"R{det.risk_score:.0f}")
        label = " ".join(parts)
        cv2.putText(
            canvas, label, (x1, max(15, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA,
        )

    # HUD.
    hud = (
        f"FPS {result.fps:.0f} | obstacles {result.obstacle_count} "
        f"| {result.overall_alert.value.upper()}"
    )
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 28), (20, 20, 20), -1)
    cv2.putText(
        canvas, hud, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
        LEVEL_COLORS[result.overall_alert], 2, cv2.LINE_AA,
    )
    return canvas
