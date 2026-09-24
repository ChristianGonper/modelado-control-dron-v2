import {
  HealthResponse,
  MissionConfigRequest,
  PreviewResponse,
  RunResultsResponse,
  RunStatusResponse,
  TelemetrySeriesResponse,
  ValidationResponse,
} from "./types";

const API_BASE = "/api";

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Fallo consultando estado de salud del servidor");
  return res.json();
}

export async function fetchPresets(seed: number = 42): Promise<any> {
  const res = await fetch(`${API_BASE}/presets?seed=${seed}`);
  if (!res.ok) throw new Error("Fallo obteniendo presets de misión");
  return res.json();
}

export async function validateMission(mission: MissionConfigRequest): Promise<ValidationResponse> {
  const res = await fetch(`${API_BASE}/mission/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mission),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.errors?.join("; ") || "Error validando configuración de misión");
  }
  return res.json();
}

export async function previewMission(mission: MissionConfigRequest): Promise<PreviewResponse> {
  const res = await fetch(`${API_BASE}/mission/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mission),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.errors?.join("; ") || err.detail || "Error generando previsualización");
  }
  return res.json();
}

export async function runSimulation(mission: MissionConfigRequest): Promise<{ run_id: string; state: string }> {
  const res = await fetch(`${API_BASE}/simulation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mission),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.errors?.join("; ") || "Error iniciando simulación");
  }
  return res.json();
}

export async function fetchRunStatus(runId: string): Promise<RunStatusResponse> {
  const res = await fetch(`${API_BASE}/simulation/${runId}/status`);
  if (!res.ok) throw new Error(`Error consultando estado de simulación ${runId}`);
  return res.json();
}

export async function fetchRunResults(runId: string): Promise<RunResultsResponse> {
  const res = await fetch(`${API_BASE}/simulation/${runId}/results`);
  if (!res.ok) throw new Error(`Error obteniendo resultados de simulación ${runId}`);
  return res.json();
}

export async function fetchTelemetry(runId: string, controllerId: string): Promise<TelemetrySeriesResponse> {
  const res = await fetch(`${API_BASE}/simulation/${runId}/telemetry/${controllerId}`);
  if (!res.ok) throw new Error(`Error cargando telemetría de ${controllerId}`);
  return res.json();
}

export function getExportUrl(runId: string, format: "json" | "csv"): string {
  return `${API_BASE}/simulation/${runId}/export/${format}`;
}
