"""Throughput / latency benchmark for the full pipeline.

Measures end-to-end FPS (detect → track → corridor → distance → risk → alerts)
so we can validate the 30+ FPS target and compare backends (YOLO26 vs ONNX vs
mock). Runs against the synthetic source, so it needs no camera.

    python -m app.mlops.benchmark --frames 300
"""

from __future__ import annotations

import argparse
import statistics
import time

from app.config import get_settings
from app.container import Container
from app.logging_config import configure_logging, get_logger
from app.utils.video import SyntheticSource

log = get_logger(__name__)


def run(n_frames: int = 300) -> dict:
    settings = get_settings()
    container = Container(settings)
    pipeline = container.pipeline
    source = SyntheticSource(n_frames=n_frames)

    latencies: list[float] = []
    t0 = time.perf_counter()
    for frame in source.frames():
        s = time.perf_counter()
        pipeline.process(frame)
        latencies.append((time.perf_counter() - s) * 1000.0)
    wall = time.perf_counter() - t0

    report = {
        "backend": container.detector.backend_name,
        "device": container.detector.device,
        "frames": len(latencies),
        "fps": round(len(latencies) / wall, 1),
        "latency_ms_mean": round(statistics.mean(latencies), 2),
        "latency_ms_p50": round(statistics.median(latencies), 2),
        "latency_ms_p95": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 2),
    }
    log.info("benchmark", **report)
    return report


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=300)
    args = parser.parse_args()
    report = run(args.frames)
    print("\n=== RailVision AI Benchmark ===")
    for k, v in report.items():
        print(f"{k:>18}: {v}")


if __name__ == "__main__":
    main()
