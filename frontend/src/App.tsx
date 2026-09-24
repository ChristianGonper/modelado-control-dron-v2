import React, { useEffect, useRef, useState } from "react";
import { Header } from "./components/Header";
import { MissionView } from "./views/MissionView";
import { ComparisonView } from "./views/ComparisonView";
import { AnalysisView } from "./views/AnalysisView";
import {
  HealthResponse,
  MissionConfigRequest,
  RunResultsResponse,
  RunStatusResponse,
  TrajectoryFamily,
} from "./types";
import { fetchHealth, fetchPresets, fetchRunResults, fetchRunStatus } from "./api";

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<"mission" | "comparison" | "analysis">("mission");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [presets, setPresets] = useState<any>(null);

  // Active Mission Configuration
  const [missionConfig, setMissionConfig] = useState<MissionConfigRequest>({
    mode: "simple",
    family: TrajectoryFamily.CIRCLE,
    params: {
      center_W_m: [0.0, 0.0, 2.0],
      radius_m: 1.5,
      omega_rad_s: 0.6,
      yaw_mode: "forward",
      tilt_deg: 0.0,
      plane_yaw_deg: 0.0,
      duration: 15.0,
    },
    transition_speed: 0.8,
    wind: { magnitude_m_s: 0.0, direction_deg: 0.0 },
    seed: 42,
  });

  // Active Simulation State
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [runResults, setRunResults] = useState<RunResultsResponse | null>(null);

  // Shared Playback State (preserved when switching views!)
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [visibleControllers, setVisibleControllers] = useState<Record<string, boolean>>({
    classic: true,
    mlp: true,
    gru: false,
    lstm: false,
  });

  // La corrida visible pertenece solo a la configuración con la que se lanzó.
  const missionKeyRef = useRef(JSON.stringify(missionConfig));
  const submittedKeyRef = useRef<string | null>(null);
  missionKeyRef.current = JSON.stringify(missionConfig);

  // Fetch initial health and presets
  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => console.error("Health fetch error:", err));

    fetchPresets(42)
      .then((p) => {
        setPresets(p);
        if (p?.initial_variants?.circle) {
          setMissionConfig((prev) => ({
            ...prev,
            params: { ...p.initial_variants.circle },
          }));
        }
      })
      .catch((err) => console.error("Presets fetch error:", err));
  }, []);

  // Polling simulation status when activeRunId is set
  useEffect(() => {
    if (!activeRunId) return;

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const st = await fetchRunStatus(activeRunId);
        if (!isMounted) return;
        setRunStatus(st);

        if (st.state in { completed: 1, partial: 1, error: 1, interrupted: 1 }) {
          clearInterval(interval);
          if (submittedKeyRef.current !== missionKeyRef.current) {
            return;
          }
          const res = await fetchRunResults(activeRunId);
          if (!isMounted || submittedKeyRef.current !== missionKeyRef.current) return;
          setRunResults(res);
          setCurrentTime(0);
          setCurrentView("comparison");
        }
      } catch (err) {
        console.error("Status polling error:", err);
      }
    }, 500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [activeRunId]);

  // Editar la misión retira la comparación de la configuración anterior.
  useEffect(() => {
    if (!submittedKeyRef.current) return;
    if (missionKeyRef.current === submittedKeyRef.current) return;
    submittedKeyRef.current = null;
    setActiveRunId(null);
    setRunStatus(null);
    setRunResults(null);
    setCurrentTime(0);
    setCurrentView("mission");
  }, [missionConfig]);

  return (
    <div className="min-h-screen flex flex-col bg-aerolab-canvas text-aerolab-text">
      {/* AeroLab Header */}
      <Header
        currentView={currentView}
        onViewChange={setCurrentView}
        health={health}
        hasResults={!!runResults}
      />

      {/* Simulation In-Progress Banner */}
      {runStatus && runStatus.state === "running" && (
        <div className="bg-sky-50/80 border-b border-sky-200/60 py-2.5 px-6 shadow-2xs">
          <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 text-xs">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 bg-white border border-sky-200 px-2.5 py-1 rounded-full shadow-2xs">
                <div className="w-2 h-2 rounded-full bg-aerolab-action animate-pulse" />
                <span className="font-bold text-aerolab-action text-[11px] uppercase tracking-wide">
                  Simulación activa
                </span>
              </div>
              <span className="text-slate-700 font-medium">
                {(() => {
                  const controllerNames: Record<string, string> = {
                    classic: "PD",
                    mlp: "MLP",
                    gru: "GRU",
                    lstm: "LSTM",
                  };
                  const entries = Object.entries(runStatus.controllers || {});
                  const runningIndex = entries.findIndex(([_, c]) => c.status === "running");
                  if (runningIndex >= 0) {
                    const [cid] = entries[runningIndex];
                    const name = controllerNames[cid] || cid.toUpperCase();
                    return `Evaluando controlador ${name} (${runningIndex + 1} de ${entries.length})...`;
                  }
                  return "Procesando dinámicas de vuelo y protecciones...";
                })()}
              </span>
            </div>
            <div className="flex items-center gap-3 w-56">
              <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden shadow-inner">
                <div
                  className="bg-aerolab-action h-full transition-all duration-300 rounded-full"
                  style={{ width: `${Math.round(runStatus.progress_pct || 0)}%` }}
                />
              </div>
              <span className="font-mono text-slate-600 font-semibold tabular-nums text-xs">
                {Math.round(runStatus.progress_pct || 0)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1">
        {currentView === "mission" && (
          <MissionView
            presets={presets}
            onSimulationStarted={(runId) => {
              submittedKeyRef.current = missionKeyRef.current;
              setRunResults(null);
              setRunStatus(null);
              setActiveRunId(runId);
              setCurrentTime(0);
            }}
            missionConfig={missionConfig}
            setMissionConfig={setMissionConfig}
            setPresets={setPresets}
          />
        )}

        {currentView === "comparison" && (
          <ComparisonView
            results={runResults}
            onGoToAnalysis={() => setCurrentView("analysis")}
            visibleControllers={visibleControllers}
            setVisibleControllers={setVisibleControllers}
            currentTime={currentTime}
            setCurrentTime={setCurrentTime}
          />
        )}

        {currentView === "analysis" && (
          <AnalysisView
            results={runResults}
            onBackToComparison={() => setCurrentView("comparison")}
            visibleControllers={visibleControllers}
            setVisibleControllers={setVisibleControllers}
            currentTime={currentTime}
            setCurrentTime={setCurrentTime}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-aerolab-border bg-white py-3.5 px-6 text-xs text-aerolab-secondary">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-semibold text-aerolab-text">AeroLab</span> • Concurso Prototipos EIIIA 2026 • NeuroFlight
          </div>
          <div className="flex items-center gap-3">
            <span>Simulador 6DOF con control PD y redes neuronales en el lazo externo</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
