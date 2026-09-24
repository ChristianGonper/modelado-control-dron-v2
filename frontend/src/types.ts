export enum TrajectoryFamily {
  HOLD = "hold",
  CIRCLE = "circle",
  LISSAJOUS = "lissajous",
  WAYPOINT = "waypoint",
  LEMNISCATE = "lemniscate",
  COMPOSITE = "composite",
}

export interface WindConfig {
  magnitude_m_s: number;
  direction_deg: number;
}

export interface CompositeSegmentConfig {
  type: string;
  duration?: number;
  params: Record<string, any>;
}

export interface MissionConfigRequest {
  mode: "simple" | "composite";
  family: TrajectoryFamily;
  params: Record<string, any>;
  segments?: CompositeSegmentConfig[];
  transition_speed: number;
  wind: WindConfig;
  seed: number;
}

export interface ValidationResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
  initial_position: [number, number, number];
  selected_pid_family?: string;
  selected_pid_explanation?: string;
}

export interface PreviewResponse {
  points: [number, number, number][];
  time_series: number[];
  is_transition: boolean[];
  segment_indices: number[];
  initial_position: [number, number, number];
  bounds: {
    min_z: number;
    max_z: number;
    max_horiz_radius: number;
  };
  total_duration_s: number;
  accessibility_summary: string;
  selected_pid_family: string;
  selected_pid_explanation: string;
}

export interface ControllerProgress {
  status: "pending" | "running" | "completed" | "error" | "cancelled";
  progress_pct: number;
  error_message?: string;
  termination_reason?: string;
  duration_s?: number;
  position_mae_m?: number;
  position_max_err_m?: number;
}

export interface RunStatusResponse {
  run_id: string;
  state: "idle" | "preparing" | "running" | "completed" | "partial" | "interrupted" | "error";
  progress_pct: number;
  controllers: Record<string, ControllerProgress>;
  created_at: string;
}

export interface ControllerSummary {
  controller_id: string;
  name: string;
  family: string;
  status: string;
  termination_reason: string;
  duration_s: number;
  position_mae_m?: number;
  position_max_err_m?: number;
  sample_count: number;
  is_interrupted: boolean;
}

export interface TrajectorySample {
  time_s: number;
  pos: [number, number, number];
  yaw: number;
  err_m: number;
}

export interface RunResultsResponse {
  run_id: string;
  timestamp: string;
  mission_mode: string;
  mission_family: string;
  selected_pid: string;
  selected_pid_explanation: string;
  effective_config: Record<string, any>;
  seed: number;
  summaries: Record<string, ControllerSummary>;
  nominal_path: [number, number, number][];
  runs_trajectory: Record<string, TrajectorySample[]>;
  is_partial: boolean;
}

export interface TelemetrySeriesResponse {
  run_id: string;
  controller_id: string;
  time_s: number[];
  signals: Record<string, (number | null)[]>;
  units: Record<string, string>;
  groups: Record<string, string>;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  app: string;
  team: string;
  device: string;
  cuda_available: boolean;
  bundle: {
    valid: boolean;
    status: string;
    files_checked: number;
    missing_files: string[];
    hash_mismatches: any[];
  };
}
