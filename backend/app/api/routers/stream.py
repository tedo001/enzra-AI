"""Live streaming endpoints: WebSocket (JSON results) + MJPEG (annotated video).

The WebSocket pushes :class:`FrameResult` JSON per frame for the dashboard to
render bounding boxes, risk and alerts. A parallel MJPEG endpoint serves an
annotated preview for quick visual inspection or embedding. Both run over a
shared synthetic/real source so the demo works with zero hardware.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_container
from app.container import Container
from app.logging_config import get_logger
from app.utils.drawing import draw_frame
from app.utils.enhancement import auto_enhance
from app.utils.video import SyntheticSource

router = APIRouter(prefix="/stream", tags=["streaming"])
log = get_logger(__name__)


def _make_source(container: Container):
    # Extension point: swap for OpenCVSource(uri) per camera_id (multi-camera).
    return SyntheticSource(width=1280, height=720)


@router.websocket("/ws")
async def stream_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    container: Container = websocket.app.state.container
    source = _make_source(container)
    container.pipeline.reset()
    try:
        for frame in source.frames():
            enhanced, weather = auto_enhance(frame)
            result = container.pipeline.process(enhanced)
            container.recorder.observe(frame, result)
            await container.recorder.maybe_record(frame, result)

            payload = result.model_dump(mode="json")
            payload["weather"] = weather.value
            voice = container.alerts.voice_cue(result.overall_alert)
            if voice:
                payload["voice_alert"] = voice
            await websocket.send_json(payload)
            await asyncio.sleep(1 / 30)  # pace to ~30 FPS
    except WebSocketDisconnect:
        log.info("ws client disconnected")
    finally:
        source.close()


@router.get("/mjpeg")
async def stream_mjpeg(container: Container = Depends(get_container)) -> StreamingResponse:
    try:
        import cv2
    except ImportError:  # pragma: no cover
        return StreamingResponse(iter([b""]), media_type="text/plain")

    source = _make_source(container)
    container.pipeline.reset()

    def gen():
        for frame in source.frames():
            enhanced, _ = auto_enhance(frame)
            result = container.pipeline.process(enhanced)
            annotated = draw_frame(enhanced, result)
            ok, buf = cv2.imencode(".jpg", annotated)
            if not ok:
                continue
            yield (
                b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                + buf.tobytes()
                + b"\r\n"
            )

    return StreamingResponse(
        gen(), media_type="multipart/x-mixed-replace; boundary=frame"
    )
