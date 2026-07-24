// Shared types mirroring the backend `app.schemas` contracts.

export type AlertLevel = "safe" | "low" | "medium" | "high" | "critical";

export type ObstacleClass =
  | "human" | "cow" | "elephant" | "dog" | "buffalo" | "goat"
  | "car" | "truck" | "bus" | "motorcycle"
  | "fallen_tree" | "rock" | "construction_barrier" | "debris" | "unknown";

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface Detection {
  label: ObstacleClass;
  raw_label: string;
  confidence: number;
  box: BoundingBox;
  track_id: number | null;
  on_track: boolean;
  distance_m: number | null;
  speed_mps: number | null;
  time_to_collision_s: number | null;
  risk_score: number;
  alert_level: AlertLevel;
}

export interface FrameResult {
  frame_id: number;
  timestamp: string;
  width: number;
  height: number;
  fps: number;
  inference_ms: number;
  detections: Detection[];
  corridor_polygon: number[][];
  overall_alert: AlertLevel;
  recommendation: string;
  weather?: string;
  voice_alert?: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  device: string;
  model_loaded: boolean;
  detector_backend: string;
  uptime_s: number;
}

export interface DailyReport {
  day: string;
  total_detections: number;
  total_incidents: number;
  critical_incidents: number;
  obstacle_frequency: Record<string, number>;
  incidents_by_level: Record<string, number>;
  closest_obstacle_m: number | null;
}

export interface IncidentRecord {
  id: string;
  created_at: string;
  alert_level: AlertLevel;
  frame_id: number;
  obstacle_classes: ObstacleClass[];
  min_distance_m: number | null;
  max_risk_score: number;
  camera_id: string;
}

export const ALERT_COLORS: Record<AlertLevel, string> = {
  safe: "#22c55e",
  low: "#14b8a6",
  medium: "#f59e0b",
  high: "#f97316",
  critical: "#ef4444",
};
