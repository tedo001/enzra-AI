"""Automatic model evaluation against a validation set.

Thin wrapper over Ultralytics ``model.val()`` that logs mAP metrics to MLflow
(when configured) so every trained candidate is scored and comparable in the
model registry. Falls back to plain stdout when MLflow is unavailable.

    python -m app.mlops.evaluate --data datasets/railvision/data.yaml
"""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.logging_config import configure_logging, get_logger

log = get_logger(__name__)


def evaluate(data_yaml: str, weights: str | None = None) -> dict:
    settings = get_settings()
    weights = weights or settings.model_path
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("install the '[ai]' extra to evaluate models") from exc

    model = YOLO(weights)
    metrics = model.val(data=data_yaml, imgsz=settings.img_size)
    report = {
        "map50": float(getattr(metrics.box, "map50", 0.0)),
        "map50_95": float(getattr(metrics.box, "map", 0.0)),
        "precision": float(getattr(metrics.box, "mp", 0.0)),
        "recall": float(getattr(metrics.box, "mr", 0.0)),
    }
    _log_mlflow(settings, report, weights)
    log.info("evaluation", **report)
    return report


def _log_mlflow(settings, report: dict, weights: str) -> None:
    try:
        import mlflow

        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.experiment_name)
        with mlflow.start_run(run_name="eval"):
            mlflow.log_param("weights", weights)
            mlflow.log_metrics(report)
    except Exception as exc:  # pragma: no cover
        log.warning("mlflow logging skipped", error=str(exc))


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--weights", default=None)
    args = parser.parse_args()
    print(evaluate(args.data, args.weights))


if __name__ == "__main__":
    main()
