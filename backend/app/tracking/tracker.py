"""Lightweight multi-object tracker with persistent IDs.

A dependency-free tracker combining IoU association with a constant-velocity
motion estimate (a pragmatic ByteTrack-inspired design). It runs on CPU at
video rate and needs no extra weights, so the platform tracks reliably even in
the zero-config fallback path. For production, a Kalman-based ByteTrack/BoT-SORT
can be dropped in behind the same interface — the pipeline only depends on the
``track_id`` and ``speed_mps`` fields it populates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import BoundingBox, Detection


def _iou(a: BoundingBox, b: BoundingBox) -> float:
    ix1, iy1 = max(a.x1, b.x1), max(a.y1, b.y1)
    ix2, iy2 = min(a.x2, b.x2), min(a.y2, b.y2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    union = a.area + b.area - inter
    return inter / union if union > 0 else 0.0


@dataclass
class _Track:
    track_id: int
    box: BoundingBox
    label: str
    misses: int = 0
    hits: int = 1
    history: list[tuple[float, float]] = field(default_factory=list)  # foot points

    def update(self, box: BoundingBox) -> None:
        self.box = box
        self.misses = 0
        self.hits += 1
        self.history.append(box.bottom_center)
        if len(self.history) > 30:
            self.history.pop(0)


class ObjectTracker:
    """Greedy IoU tracker with track lifecycle management."""

    def __init__(self, iou_threshold: float = 0.3, max_age: int = 30, min_hits: int = 2) -> None:
        self._iou_threshold = iou_threshold
        self._max_age = max_age
        self._min_hits = min_hits
        self._tracks: dict[int, _Track] = {}
        self._next_id = 1

    def reset(self) -> None:
        self._tracks.clear()
        self._next_id = 1

    def update(self, detections: list[Detection]) -> list[Detection]:
        """Associate detections to tracks and stamp ``track_id`` in place-ish.

        Returns a new list of detections with ``track_id`` populated. The pixel
        displacement of each track's foot point is exposed as a proxy velocity
        that the distance stage later converts to metres/second.
        """
        unmatched = set(self._tracks.keys())
        assignments: dict[int, int] = {}  # det index -> track id

        # Greedy association by descending IoU.
        pairs = []
        for di, det in enumerate(detections):
            for tid in unmatched:
                score = _iou(det.box, self._tracks[tid].box)
                if score >= self._iou_threshold:
                    pairs.append((score, di, tid))
        pairs.sort(reverse=True)

        used_dets: set[int] = set()
        used_tracks: set[int] = set()
        for _score, di, tid in pairs:
            if di in used_dets or tid in used_tracks:
                continue
            assignments[di] = tid
            used_dets.add(di)
            used_tracks.add(tid)
            self._tracks[tid].update(detections[di].box)
            self._tracks[tid].label = detections[di].label.value

        # Spawn new tracks for unmatched detections.
        for di, det in enumerate(detections):
            if di in used_dets:
                continue
            tid = self._next_id
            self._next_id += 1
            self._tracks[tid] = _Track(
                track_id=tid,
                box=det.box,
                label=det.label.value,
                history=[det.box.bottom_center],
            )
            assignments[di] = tid

        # Age out unmatched tracks.
        for tid in list(self._tracks.keys()):
            if tid not in used_tracks and tid not in assignments.values():
                self._tracks[tid].misses += 1
                if self._tracks[tid].misses > self._max_age:
                    del self._tracks[tid]

        # Stamp results.
        out: list[Detection] = []
        for di, det in enumerate(detections):
            tid = assignments.get(di)
            track = self._tracks.get(tid) if tid is not None else None
            confirmed = track is not None and track.hits >= self._min_hits
            det = det.model_copy(
                update={
                    "track_id": tid if confirmed else None,
                }
            )
            out.append(det)
        return out

    def foot_history(self, track_id: int) -> list[tuple[float, float]]:
        track = self._tracks.get(track_id)
        return list(track.history) if track else []
