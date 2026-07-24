"""Export YOLO26 weights to deployment formats (ONNX / TensorRT / TFLite).

Usage
-----
    python -m app.mlops.export --format onnx
    python -m app.mlops.export --format engine --half     # TensorRT
    python -m app.mlops.export --format tflite

Exported artifacts land next to the source weights and can be served by the
ONNX Runtime detector backend or an edge runtime for edge deployment.
"""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.logging_config import configure_logging, get_logger

log = get_logger(__name__)

VALID_FORMATS = ("onnx", "engine", "tflite", "openvino", "torchscript")


def export(fmt: str, half: bool, imgsz: int, weights: str | None = None) -> str:
    settings = get_settings()
    src = weights or settings.model_path
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("install the '[ai]' extra to export models") from exc

    log.info("exporting", weights=src, format=fmt, imgsz=imgsz, half=half)
    model = YOLO(src)
    out = model.export(format=fmt, half=half, imgsz=imgsz, dynamic=False, simplify=True)
    log.info("export complete", output=str(out))
    return str(out)


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Export RailVision YOLO26 weights")
    parser.add_argument("--format", choices=VALID_FORMATS, default="onnx")
    parser.add_argument("--half", action="store_true", help="FP16 export")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--weights", default=None)
    args = parser.parse_args()
    export(args.format, args.half, args.imgsz, args.weights)


if __name__ == "__main__":
    main()
