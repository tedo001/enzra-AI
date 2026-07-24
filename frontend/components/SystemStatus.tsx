"use client";

import { useEffect, useState } from "react";
import type { HealthStatus } from "@/lib/types";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SystemStatus({ connected }: { connected: boolean }) {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    const load = () => api.health().then(setHealth).catch(() => setHealth(null));
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const rows: [string, string][] = [
    ["Stream", connected ? "Connected" : "Reconnecting…"],
    ["Detector", health?.detector_backend ?? "—"],
    ["Device", health?.device ?? "—"],
    ["Model", health?.model_loaded ? "Loaded" : "Fallback"],
    ["Version", health?.version ?? "—"],
    ["Uptime", health ? `${health.uptime_s.toFixed(0)}s` : "—"],
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between">
            <span className="text-muted-foreground">{k}</span>
            <span className="font-medium">{v}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
