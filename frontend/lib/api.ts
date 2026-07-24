// REST client for the RailVision backend.
import type { DailyReport, HealthStatus, IncidentRecord } from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<HealthStatus>("/health"),
  dailyReport: (day?: string) =>
    get<DailyReport>(`/api/analytics/daily${day ? `?day=${day}` : ""}`),
  stats: () => get<Record<string, unknown>>("/api/analytics/stats"),
  incidents: (limit = 50) =>
    get<IncidentRecord[]>(`/api/analytics/incidents?limit=${limit}`),
};

export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/stream/ws";
