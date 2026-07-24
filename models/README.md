# Models & Model Registry

RailVision AI standardises on the **YOLO26** detection family (Ultralytics).

## Weights (not committed)

| File                              | Purpose                              |
|-----------------------------------|--------------------------------------|
| `weights/railvision_yolo26.pt`    | Custom-trained obstacle detector     |
| `weights/railvision_seg.pt`       | Railway corridor segmentation (opt.) |
| `weights/railvision_yolo26.onnx`  | ONNX export for edge / ONNX Runtime  |
| `weights/railvision_yolo26.engine`| TensorRT engine (GPU edge)           |

Weights are ignored by git (`*.pt`, `*.onnx`, `*.engine`). Track them in a
model registry (MLflow) or object storage.

## Zero-config bootstrap

If `weights/railvision_yolo26.pt` is absent, the detector auto-downloads a
pretrained `yolo26n` checkpoint and remaps COCO classes into the RailVision
taxonomy (`app/ai/class_map.py`), so the platform is useful before any custom
training. If the AI stack itself is unavailable, it falls back to a deterministic
mock detector so the API and dashboard still run.

## Registry workflow

```bash
# Train + auto-log to MLflow
python -m app.mlops.train --data datasets/railvision/data.yaml --model yolo26s.pt

# Evaluate a candidate (logs mAP to MLflow)
python -m app.mlops.evaluate --data datasets/railvision/data.yaml \
    --weights runs/railvision/yolo26-obstacles/weights/best.pt

# Promote: copy best weights into models/weights/railvision_yolo26.pt

# Export for deployment
python -m app.mlops.export --format onnx
python -m app.mlops.export --format engine --half   # TensorRT
```

## Attribution / license note

Ultralytics YOLO is **AGPL-3.0**. RailVision AI isolates it behind the
`BaseDetector` interface so the platform core stays MIT-licensed and the
detector remains swappable (ONNX Runtime / TensorRT / a future model).
