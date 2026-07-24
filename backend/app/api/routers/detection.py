"""Single-image / uploaded-frame detection endpoint."""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_container
from app.container import Container
from app.schemas import FrameResult

router = APIRouter(prefix="/api/detect", tags=["detection"])


@router.post("", response_model=FrameResult)
async def detect_image(
    file: UploadFile = File(...),
    container: Container = Depends(get_container),
) -> FrameResult:
    """Run the full pipeline on a single uploaded image and record incidents."""
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(500, "OpenCV not available") from exc

    data = await file.read()
    arr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "could not decode image")

    result = container.pipeline.process(frame)
    container.recorder.observe(frame, result)
    await container.recorder.maybe_record(frame, result)
    return result
