"use client";

import { Activity, AlertOctagon, Gauge, TrainFront } from "lucide-react";
import { useRailVisionStream } from "@/hooks/useRailVisionStream";
import { LiveFeed } from "@/components/LiveFeed";
import { RiskGauge } from "@/components/RiskGauge";
import { AlertBanner } from "@/components/AlertBanner";
import { DetectionList } from "@/components/DetectionList";
import { StatCard } from "@/components/StatCard";
import { AnalyticsPanel } from "@/components/AnalyticsPanel";
import { SystemStatus } from "@/components/SystemStatus";
import { ALERT_COLORS } from "@/lib/types";
import { formatDistance } from "@/lib/utils";

export default function Dashboard() {
  const { frame, connected } = useRailVisionStream();

  const level = frame?.overall_alert ?? "safe";
  const topRisk = Math.max(0, ...(frame?.detections ?? []).map((d) => d.risk_score));
  const onTrack = (frame?.detections ?? []).filter((d) => d.on_track);
  const closest = onTrack.reduce<number | null>(
    (min, d) => (d.distance_m != null && (min == null || d.distance_m < min) ? d.distance_m : min),
    null,
  );

  return (
    <main className="mx-auto max-w-[1600px] space-y-4 p-4 lg:p-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrainFront className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-xl font-bold tracking-tight">RailVision AI</h1>
            <p className="text-xs text-muted-foreground">
              Railway Hazard Detection · YOLO26 · Real-time Collision Risk
            </p>
          </div>
        </div>
        <span
          className="flex items-center gap-2 rounded-full border border-border px-3 py-1 text-xs"
        >
          <span
            className={`h-2 w-2 rounded-full ${connected ? "bg-safe" : "bg-medium animate-pulse"}`}
          />
          {connected ? "Streaming" : "Connecting"}
        </span>
      </header>

      <AlertBanner level={level} recommendation={frame?.recommendation ?? "Awaiting stream…"} />

      {/* KPI row */}
      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="FPS" value={(frame?.fps ?? 0).toFixed(0)} icon={<Activity className="h-5 w-5" />} sub={`${(frame?.inference_ms ?? 0).toFixed(1)} ms/frame`} />
        <StatCard label="On-Track Obstacles" value={onTrack.length} icon={<AlertOctagon className="h-5 w-5" />} accent={onTrack.length ? ALERT_COLORS[level] : undefined} />
        <StatCard label="Top Risk" value={topRisk.toFixed(0)} icon={<Gauge className="h-5 w-5" />} accent={ALERT_COLORS[level]} />
        <StatCard label="Closest" value={formatDistance(closest)} sub="ground-plane estimate" />
      </section>

      {/* Main grid */}
      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <LiveFeed frame={frame} />
        </div>
        <div className="space-y-4">
          <RiskGauge score={topRisk} level={level} />
          <DetectionList detections={frame?.detections ?? []} />
        </div>
      </section>

      {/* Analytics + status */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AnalyticsPanel />
        </div>
        <SystemStatus connected={connected} />
      </section>

      <footer className="pt-2 text-center text-xs text-muted-foreground">
        RailVision AI — clean-room implementation · MIT licensed · YOLO26 detector is pluggable
      </footer>
    </main>
  );
}
