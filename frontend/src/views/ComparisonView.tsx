import React, { useEffect, useState, useRef } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Layers,
  ArrowRight,
  Info,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { RunResultsResponse } from "../types";
import { TrajectoryViewer3D } from "../components/TrajectoryViewer3D";

export interface ComparisonViewProps {
  results: RunResultsResponse | null;
  onGoToAnalysis: () => void;
  visibleControllers: Record<string, boolean>;
  setVisibleControllers: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  currentTime: number;
  setCurrentTime: React.Dispatch<React.SetStateAction<number>>;
}

const CONTROLLER_CONFIG: Record<
  string,
  { name: string; color: string; hex: string }
> = {
  classic: { name: "PD", color: "text-[#0284C7]", hex: "#0284C7" },
  mlp: { name: "MLP", color: "text-[#10B981]", hex: "#10B981" },
  gru: { name: "GRU", color: "text-[#F59E0B]", hex: "#F59E0B" },
  lstm: { name: "LSTM", color: "text-[#8B5CF6]", hex: "#8B5CF6" },
};

export const ComparisonView: React.FC<ComparisonViewProps> = ({
  results,
  onGoToAnalysis,
  visibleControllers,
  setVisibleControllers,
  currentTime,
  setCurrentTime,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const animFrameRef = useRef<number | null>(null);
  const lastTimestampRef = useRef<number | null>(null);

  // Maximum duration across all available runs
  const maxDuration = Math.max(
    ...Object.values(results?.summaries || {}).map((s) => s.duration_s || 0),
    1.0
  );

  // Keyboard shortcut: Space for Play/Pause
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && e.target === document.body) {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Animation playback loop
  useEffect(() => {
    if (!isPlaying) {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      lastTimestampRef.current = null;
      return;
    }

    const step = (now: number) => {
      if (lastTimestampRef.current !== null) {
        const deltaSec = ((now - lastTimestampRef.current) / 1000) * playbackSpeed;
        setCurrentTime((prev) => {
          const next = prev + deltaSec;
          if (next >= maxDuration) {
            setIsPlaying(false);
            return maxDuration;
          }
          return next;
        });
      }
      lastTimestampRef.current = now;
      animFrameRef.current = requestAnimationFrame(step);
    };

    animFrameRef.current = requestAnimationFrame(step);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, playbackSpeed, maxDuration]);

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20 text-center flex flex-col items-center gap-3">
        <Layers className="w-12 h-12 text-aerolab-secondary/40" />
        <h2 className="text-base font-bold text-aerolab-text">Sin misión ejecutada</h2>
        <p className="text-xs text-aerolab-secondary max-w-md">
          Configura una misión en la pestaña anterior y pulsa «Ejecutar Misión» para comparar el PD con las redes neuronales.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col gap-6">
      {/* 3D PLAYBACK VISOR & PLAYER */}
      <div className="bg-white p-5 rounded-xl border border-aerolab-border shadow-xs flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-aerolab-border pb-3">
          <h2 className="text-base font-bold text-aerolab-text flex items-center gap-2">
            <Layers className="w-5 h-5 text-aerolab-action" />
            <span>Reproducción de Misión y Comparación 3D</span>
          </h2>

          <button
            onClick={onGoToAnalysis}
            className="flex items-center gap-1.5 text-xs font-semibold text-aerolab-action hover:underline self-start sm:self-auto cursor-pointer"
          >
            <span>Profundizar en Análisis</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* 3D View Canvas with In-Canvas Legend */}
        <TrajectoryViewer3D
          nominalPath={results.nominal_path}
          runsTrajectory={results.runs_trajectory}
          visibleControllers={visibleControllers}
          currentTime={currentTime}
          showLegend={true}
          showSpatialSummary={false}
          className="w-full h-[460px]"
        />

        {/* Playback Controls Bar */}
        <div className="bg-aerolab-canvas p-3.5 rounded-xl border border-aerolab-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          {/* Controls: Play/Pause, Reset, Speed */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (currentTime >= maxDuration) setCurrentTime(0);
                setIsPlaying(!isPlaying);
              }}
              className="w-9 h-9 flex items-center justify-center rounded-lg bg-aerolab-action text-white hover:bg-aerolab-action/90 shadow-xs cursor-pointer"
              title={isPlaying ? "Pausar (Espacio)" : "Reproducir (Espacio)"}
            >
              {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
            </button>

            <button
              onClick={() => {
                setIsPlaying(false);
                setCurrentTime(0);
              }}
              className="w-8 h-8 flex items-center justify-center rounded-lg bg-white border border-aerolab-border text-aerolab-secondary hover:text-aerolab-text cursor-pointer"
              title="Reiniciar reproducción"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            {/* Speed Pills */}
            <div className="flex items-center gap-1 bg-white p-0.5 rounded-lg border border-aerolab-border ml-2 text-xs font-mono">
              {[0.25, 0.5, 1.0, 2.0].map((s) => (
                <button
                  key={s}
                  onClick={() => setPlaybackSpeed(s)}
                  className={`px-2 py-1 rounded font-medium cursor-pointer ${
                    playbackSpeed === s ? "bg-aerolab-action text-white font-bold" : "text-aerolab-secondary hover:text-aerolab-text"
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>

          {/* Scrubber Timeline */}
          <div className="flex-1 flex items-center gap-3">
            <input
              type="range"
              min="0"
              max={maxDuration}
              step="0.05"
              value={currentTime}
              onChange={(e) => {
                setCurrentTime(parseFloat(e.target.value));
              }}
              className="w-full cursor-pointer accent-aerolab-action"
            />
            <div className="text-xs font-mono text-aerolab-secondary whitespace-nowrap min-w-[90px] text-right">
              <span className="font-semibold text-aerolab-text">{currentTime.toFixed(2)}</span> / {maxDuration.toFixed(2)} s
            </div>
          </div>
        </div>

        {/* Controller Visibility Toggles */}
        <div className="flex flex-wrap items-center gap-3 text-xs pt-1">
          <span className="text-aerolab-secondary font-medium">Controladores visibles:</span>
          {Object.entries(CONTROLLER_CONFIG).map(([cid, cfg]) => {
            const summary = results.summaries[cid];
            const isAvailable = !!summary && summary.status === "completed";
            return (
              <label
                key={cid}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border cursor-pointer select-none transition-all ${
                  visibleControllers[cid]
                    ? "bg-white border-aerolab-border shadow-2xs font-semibold text-aerolab-text"
                    : "bg-aerolab-canvas/50 border-transparent text-aerolab-secondary opacity-60"
                }`}
              >
                <input
                  type="checkbox"
                  checked={!!visibleControllers[cid]}
                  disabled={!isAvailable}
                  onChange={(e) => {
                    setVisibleControllers({ ...visibleControllers, [cid]: e.target.checked });
                  }}
                  className="rounded text-aerolab-action focus:ring-aerolab-action"
                />
                <span className="flex items-center gap-1.5 font-mono">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: cfg.hex }}
                  />
                  <span>{cfg.name}</span>
                </span>
              </label>
            );
          })}
        </div>
      </div>

      {/* METRICS OF FLIGHT TRACKING */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-aerolab-text">
            Métricas de Seguimiento
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(CONTROLLER_CONFIG).map(([cid, cfg]) => {
            const summary = results.summaries[cid];
            if (!summary) return null;

            const isInterrupted = summary.is_interrupted;
            const isCompleted = summary.status === "completed";

            return (
              <div
                key={cid}
                className={`bg-white p-4 rounded-xl border flex flex-col gap-3 shadow-xs ${
                  visibleControllers[cid] ? "border-aerolab-border" : "border-aerolab-border/40 opacity-75"
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between border-b border-aerolab-border pb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: cfg.hex }} />
                    <span className="text-xs font-bold text-aerolab-text font-mono">{cfg.name}</span>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-medium flex items-center gap-1 ${
                      isCompleted && !isInterrupted
                        ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : "bg-red-50 text-red-800 border border-red-200"
                    }`}
                  >
                    {isCompleted && !isInterrupted ? (
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    ) : (
                      <XCircle className="w-3 h-3 text-red-600" />
                    )}
                    <span>{isCompleted && !isInterrupted ? "Completado" : summary.status}</span>
                  </span>
                </div>

                {/* Metrics: Error medio y Error máx */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-aerolab-secondary block text-[11px]">Error medio</span>
                    <span className="text-base font-bold text-aerolab-text font-mono tabular-nums">
                      {summary.position_mae_m !== undefined && summary.position_mae_m !== null
                        ? `${summary.position_mae_m.toFixed(3)} m`
                        : "N/A"}
                    </span>
                  </div>

                  <div>
                    <span className="text-aerolab-secondary block text-[11px]">Error máx.</span>
                    <span className="text-base font-bold text-aerolab-text font-mono tabular-nums">
                      {summary.position_max_err_m !== undefined && summary.position_max_err_m !== null
                        ? `${summary.position_max_err_m.toFixed(3)} m`
                        : "N/A"}
                    </span>
                  </div>
                </div>

                {/* Termination reason: Shown ONLY if interrupted or error */}
                {(!isCompleted || isInterrupted) && (
                  <div className="text-[11px] bg-red-50 text-red-900 p-2.5 rounded-lg border border-red-200">
                    <span className="font-semibold block mb-0.5">Parada anticipada:</span>
                    <span className="line-clamp-2">{summary.termination_reason}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Waypoint caveat note if waypoint */}
        {results.mission_family === "waypoint" && (
          <div className="mt-4 p-3 bg-aerolab-canvas rounded-lg border border-aerolab-border text-xs text-aerolab-secondary flex items-start gap-2">
            <Info className="w-4 h-4 text-aerolab-action shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-aerolab-text">Nota sobre rutas por puntos:</span> En waypoint, la ruta geométrica espacial es común, pero el simulador avanza su referencia temporal de forma individual cuando cada vehículo cumple las tolerancias de llegada y asentamiento. El visor muestra la ruta espacial común y la sincronía temporal observada para cada uno.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
