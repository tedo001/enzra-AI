"use client";

import { AlertTriangle, ShieldCheck } from "lucide-react";
import type { AlertLevel } from "@/lib/types";
import { ALERT_COLORS } from "@/lib/types";

export function AlertBanner({
  level,
  recommendation,
}: {
  level: AlertLevel;
  recommendation: string;
}) {
  const color = ALERT_COLORS[level];
  const critical = level === "critical" || level === "high";
  const Icon = level === "safe" ? ShieldCheck : AlertTriangle;

  return (
    <div
      className="flex items-center gap-3 rounded-xl border px-4 py-3"
      style={{
        borderColor: color,
        backgroundColor: `${color}1a`,
      }}
    >
      <Icon
        className={critical ? "h-6 w-6 animate-pulse-glow" : "h-6 w-6"}
        style={{ color }}
      />
      <div className="min-w-0">
        <p className="text-sm font-semibold uppercase tracking-wide" style={{ color }}>
          {level} Alert
        </p>
        <p className="truncate text-sm text-foreground">{recommendation}</p>
      </div>
    </div>
  );
}
