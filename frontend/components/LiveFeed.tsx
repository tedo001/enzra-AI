"use client";

import { useEffect, useRef } from "react";
import type { FrameResult } from "@/lib/types";
import { ALERT_COLORS } from "@/lib/types";
import { titleCase } from "@/lib/utils";

const MJPEG_URL =
  (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000") + "/stream/mjpeg";

/**
 * Renders the annotated MJPEG preview as the background and overlays live
 * bounding boxes / corridor / risk from the WebSocket frame on a canvas so the
 * overlay stays crisp and interactive.
 */
export function LiveFeed({ frame }: { frame: FrameResult | null }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !frame) return;
    canvas.width = frame.width;
    canvas.height = frame.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Corridor overlay.
    if (frame.corridor_polygon.length) {
      ctx.beginPath();
      frame.corridor_polygon.forEach(([x, y], i) =>
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y),
      );
      ctx.closePath();
      ctx.fillStyle = "rgba(74,222,128,0.10)";
      ctx.fill();
      ctx.strokeStyle = "rgba(74,222,128,0.7)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Detections.
    for (const d of frame.detections) {
      const color = d.on_track ? ALERT_COLORS[d.alert_level] : "#9ca3af";
      const { x1, y1, x2, y2 } = d.box;
      ctx.strokeStyle = color;
      ctx.lineWidth = d.on_track ? 3 : 1.5;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

      const parts = [titleCase(d.label)];
      if (d.track_id != null) parts.push(`#${d.track_id}`);
      if (d.distance_m != null) parts.push(`${d.distance_m.toFixed(0)}m`);
      if (d.on_track && d.risk_score > 0) parts.push(`R${d.risk_score.toFixed(0)}`);
      const label = parts.join("  ");

      ctx.font = "600 15px ui-sans-serif, system-ui";
      const w = ctx.measureText(label).width + 10;
      ctx.fillStyle = color;
      ctx.fillRect(x1, Math.max(0, y1 - 22), w, 20);
      ctx.fillStyle = "#0b0b0b";
      ctx.fillText(label, x1 + 5, Math.max(14, y1 - 7));
    }
  }, [frame]);

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-xl border border-border bg-black">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={MJPEG_URL}
        alt="Live railway feed"
        className="absolute inset-0 h-full w-full object-contain opacity-90"
      />
      <canvas
        ref={canvasRef}
        className="absolute inset-0 h-full w-full object-contain"
      />
      <div className="absolute left-3 top-3 flex items-center gap-2 rounded-md bg-black/60 px-2 py-1 text-xs text-white">
        <span className="h-2 w-2 animate-pulse rounded-full bg-critical" />
        LIVE · {frame?.fps.toFixed(0) ?? 0} FPS
        {frame?.weather && <span className="opacity-70">· {frame.weather}</span>}
      </div>
    </div>
  );
}
