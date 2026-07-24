"""Collision-risk engine tests."""

from __future__ import annotations

from app.detection.risk import CollisionRiskEngine
from app.schemas import AlertLevel, ObstacleClass


def test_off_track_is_safe(settings, person_on_track):
    engine = CollisionRiskEngine(settings)
    det = person_on_track.model_copy(update={"on_track": False, "distance_m": 50})
    out = engine.assess(det, now_s=1.0)
    assert out.alert_level == AlertLevel.SAFE
    assert out.risk_score == 0.0


def test_close_on_track_is_risky(settings, person_on_track):
    engine = CollisionRiskEngine(settings)
    det = person_on_track.model_copy(
        update={"on_track": True, "distance_m": 30.0, "track_id": 1}
    )
    out = engine.assess(det, now_s=1.0)
    assert out.risk_score > 20
    assert out.alert_level.rank >= AlertLevel.LOW.rank


def test_approaching_increases_risk(settings, person_on_track):
    engine = CollisionRiskEngine(settings)
    d1 = person_on_track.model_copy(
        update={"on_track": True, "distance_m": 120.0, "track_id": 7}
    )
    engine.assess(d1, now_s=0.0)
    d2 = person_on_track.model_copy(
        update={"on_track": True, "distance_m": 40.0, "track_id": 7}
    )
    out = engine.assess(d2, now_s=1.0)
    # Rapid approach must yield a finite TTC and elevated risk.
    assert out.time_to_collision_s is not None
    assert out.risk_score > 0


def test_class_severity_ordering(settings, person_on_track):
    engine = CollisionRiskEngine(settings)
    human = person_on_track.model_copy(
        update={"on_track": True, "distance_m": 60.0, "track_id": 1}
    )
    debris = person_on_track.model_copy(
        update={
            "label": ObstacleClass.DEBRIS,
            "on_track": True,
            "distance_m": 60.0,
            "track_id": 2,
        }
    )
    r_human = engine.assess(human, 1.0).risk_score
    r_debris = engine.assess(debris, 1.0).risk_score
    assert r_human >= r_debris
