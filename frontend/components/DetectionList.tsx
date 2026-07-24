"use client";

import type { Detection } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDistance, titleCase } from "@/lib/utils";

export function DetectionList({ detections }: { detections: Detection[] }) {
  const onTrack = detections
    .filter((d) => d.on_track)
    .sort((a, b) => b.risk_score - a.risk_score);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <CardTitle>Obstacles On Track ({onTrack.length})</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 space-y-2 overflow-y-auto">
        {onTrack.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Track clear — no obstacles in corridor.
          </p>
        )}
        {onTrack.map((d) => (
          <div
            key={`${d.track_id}-${d.label}`}
            className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{titleCase(d.label)}</span>
                {d.track_id != null && (
                  <span className="text-xs text-muted-foreground">#{d.track_id}</span>
                )}
              </div>
              <div className="mt-0.5 flex gap-3 text-xs text-muted-foreground">
                <span>{formatDistance(d.distance_m)}</span>
                {d.time_to_collision_s != null && (
                  <span>TTC {d.time_to_collision_s.toFixed(1)}s</span>
                )}
                {d.speed_mps != null && <span>{d.speed_mps.toFixed(1)} m/s</span>}
              </div>
            </div>
            <Badge variant={d.alert_level}>{d.risk_score.toFixed(0)}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
