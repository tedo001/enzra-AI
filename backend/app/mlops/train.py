"""Train / fine-tune RailVision YOLO26 on the railway obstacle dataset.

    python -m app.mlops.train --data datasets/railvision/data.yaml \
        --model yolo26s.pt --epochs 100

Logs hyper-parameters and metrics to MLflow for experiment tracking, and writes
best weights to ``models/weights/``. Dataset versioning is handled by DVC
(see ``datasets/README.md``).
"""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.logging_config import configure_logging, get_logger

log = get_logger(__name__)


def train(data: str, model: str, epochs: int, imgsz: int, batch: int) -> None:
    settings = get_settings()
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("install the '[ai]' extra to train models") from exc

    _mlflow_autolog(settings)
    net = YOLO(model)
    net.train(
        data=data,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project="runs/railvision",
        name="yolo26-obstacles",
        patience=25,
        pretrained=True,
    )
    log.info("training complete", best="runs/railvision/yolo26-obstacles/weights/best.pt")


def _mlflow_autolog(settings) -> None:
    try:
        import mlflow

        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(settings.experiment_name)
        mlflow.autolog()
    except Exception as exc:  # pragma: no cover
        log.warning("mlflow autolog unavailable", error=str(exc))


def main() -> None:
    configure_logging()
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--model", default="yolo26s.pt")
    p.add_argument("--epochs", type=int, default=100)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    a = p.parse_args()
    train(a.data, a.model, a.epochs, a.imgsz, a.batch)


if __name__ == "__main__":
    main()
