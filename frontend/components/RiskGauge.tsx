"use client";

import type { AlertLevel } from "@/lib/types";
import { ALERT_COLORS } from "@/lib/types";
import { Card, CardContent, CardTitle } from "@/components/ui/card";

export function RiskGauge({ score, level }: { score: number; level: AlertLevel }) {
  const clamped = Math.max(0, Math.min(100, score));
  const color = ALERT_COLORS[level];
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const offset = circ * (1 - clamped / 100);

  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-2 pt-4">
        <CardTitle>Collision Risk</CardTitle>
        <div className="relative h-36 w-36">
          <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
            <circle cx="64" cy="64" r={radius} fill="none" stroke="hsl(var(--muted))" strokeWidth="10" />
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circ}
              strokeDashoffset={offset}
              style={{ transition: "stroke-dashoffset 0.4s ease" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold" style={{ color }}>
              {clamped.toFixed(0)}
            </span>
            <span className="text-xs uppercase tracking-wide" style={{ color }}>
              {level}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
