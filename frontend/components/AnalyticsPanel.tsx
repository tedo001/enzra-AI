"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DailyReport } from "@/lib/types";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { titleCase } from "@/lib/utils";

export function AnalyticsPanel() {
  const [report, setReport] = useState<DailyReport | null>(null);

  useEffect(() => {
    const load = () => api.dailyReport().then(setReport).catch(() => void 0);
    load();
    const id = setInterval(load, 10_000);
    return () => clearInterval(id);
  }, []);

  const data = Object.entries(report?.obstacle_frequency ?? {}).map(
    ([name, count]) => ({ name: titleCase(name), count }),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Obstacle Frequency (Today)</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            No detections recorded yet today.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={60} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
