import React, { useEffect, useState } from "react";
import {
  BarChart3,
  Download,
  Search,
  ArrowLeft,
  Cpu,
  Sliders,
  Filter,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  X,
  Layers,
} from "lucide-react";
import { RunResultsResponse, TelemetrySeriesResponse } from "../types";
import { fetchTelemetry, getExportUrl } from "../api";
import { TelemetryChart } from "../components/TelemetryChart";

export interface AnalysisViewProps {
  results: RunResultsResponse | null;
  onBackToComparison: () => void;
  visibleControllers?: Record<string, boolean>;
  setVisibleControllers?: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  currentTime: number;
  setCurrentTime: React.Dispatch<React.SetStateAction<number>>;
}

const GROUPS = [
  "Todos",
  "Posición y Referencia",
  "Velocidad",
  "Comandos de Control",
  "Fuerza Deseada Neuronal",
  "Rotores y Actuadores",
  "Perturbaciones",
  "Protecciones y Límites",
];

const DEFAULT_SIGNALS = [
  "pos_err_m",
  "pos_z_m",
  "thrust_N",
  "desired_fz_N",
];

const CONTROLLER_CONFIG: Record<
  string,
  { name: string; color: string; hex: string }
> = {
  classic: { name: "PD", color: "text-[#0284C7]", hex: "#0284C7" },
  mlp: { name: "MLP", color: "text-[#10B981]", hex: "#10B981" },
  gru: { name: "GRU", color: "text-[#F59E0B]", hex: "#F59E0B" },
  lstm: { name: "LSTM", color: "text-[#8B5CF6]", hex: "#8B5CF6" },
};

export const AnalysisView: React.FC<AnalysisViewProps> = ({
  results,
  onBackToComparison,
  visibleControllers = { classic: true, mlp: true, gru: true, lstm: true },
  setVisibleControllers,
  currentTime,
  setCurrentTime,
}) => {
  const [telemetryData, setTelemetryData] = useState<Record<string, TelemetrySeriesResponse>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedGroup, setSelectedGroup] = useState("Todos");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSignals, setSelectedSignals] = useState<string[]>(DEFAULT_SIGNALS);
  const [isSignalsDrawerOpen, setIsSignalsDrawerOpen] = useState(false);
  const [isTableOpen, setIsTableOpen] = useState(false);

  // Load telemetry for all controllers in parallel
  useEffect(() => {
    if (!results) return;

    let active = true;
    const loadAll = async () => {
      setLoading(true);
      const dataMap: Record<string, TelemetrySeriesResponse> = {};
      for (const cid of ["classic", "mlp", "gru", "lstm"]) {
        try {
          const t = await fetchTelemetry(results.run_id, cid);
          dataMap[cid] = t;
        } catch {
          // controller might not have run or failed
        }
      }
      if (active) {
        setTelemetryData(dataMap);
        setLoading(false);
      }
    };

    loadAll();
    return () => {
      active = false;
    };
  }, [results?.run_id]);

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20 text-center flex flex-col items-center gap-3">
        <BarChart3 className="w-12 h-12 text-aerolab-secondary/40" />
        <h2 className="text-base font-bold text-aerolab-text">Sin datos de análisis</h2>
        <p className="text-xs text-aerolab-secondary">
          Ejecuta una simulación desde la vista Misión para acceder al análisis de señales y telemetría completa.
        </p>
      </div>
    );
  }

  // Available signals inventory from the first loaded telemetry
  const sampleTelem = Object.values(telemetryData)[0];
  const allSignalKeys = sampleTelem ? Object.keys(sampleTelem.signals) : [];

  const filteredSignals = allSignalKeys.filter((sigKey) => {
    const groupMatch =
      selectedGroup === "Todos" || sampleTelem?.groups[sigKey] === selectedGroup;
    const searchMatch =
      !searchQuery ||
      sigKey.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sampleTelem?.groups[sigKey]?.toLowerCase().includes(searchQuery.toLowerCase());
    return groupMatch && searchMatch;
  });

  // Duration and sample index closest to currentTime
  const maxDuration = Math.max(
    ...Object.values(results?.summaries || {}).map((s) => s.duration_s || 0),
    ...Object.values(telemetryData).map((t) => (t?.time_s?.length ? t.time_s[t.time_s.length - 1] : 0)),
    1.0
  );

  const primaryTimeList = sampleTelem?.time_s || [];
  let currentSampleIdx = 0;
  for (let i = 0; i < primaryTimeList.length; i++) {
    if (primaryTimeList[i] <= currentTime) {
      currentSampleIdx = i;
    } else {
      break;
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col gap-6">
      {/* HEADER & NAVIGATION */}
      <div className="flex flex-col gap-4 border-b border-aerolab-border pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <button
                onClick={onBackToComparison}
                className="flex items-center gap-1 text-xs font-semibold text-aerolab-action hover:underline cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Volver a Comparación</span>
              </button>
            </div>
            <h2 className="text-lg font-bold text-aerolab-text flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-aerolab-action" />
              <span>Análisis de Ejecución y Telemetría</span>
              {loading && (
                <span className="text-xs font-normal text-aerolab-secondary animate-pulse">
                  (Cargando telemetría...)
                </span>
              )}
            </h2>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center gap-2">
            <a
              href={getExportUrl(results.run_id, "json")}
              download
              className="flex items-center gap-1.5 text-xs font-semibold bg-white border border-aerolab-border px-3 py-2 rounded-lg text-aerolab-text hover:bg-aerolab-canvas shadow-xs transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-aerolab-action" />
              <span>Exportar JSON</span>
            </a>
            <a
              href={getExportUrl(results.run_id, "csv")}
              download
              className="flex items-center gap-1.5 text-xs font-semibold bg-white border border-aerolab-border px-3 py-2 rounded-lg text-aerolab-text hover:bg-aerolab-canvas shadow-xs transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-aerolab-mlp" />
              <span>Exportar CSV</span>
            </a>
          </div>
        </div>

        {/* Controller Visibility Pills */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-aerolab-border/60">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-aerolab-secondary font-medium mr-1">Controladores:</span>
            {Object.entries(CONTROLLER_CONFIG).map(([cid, cfg]) => {
              const summary = results.summaries[cid];
              const isAvailable = !!summary && summary.status === "completed";
              const isChecked = !!visibleControllers[cid];

              return (
                <label
                  key={cid}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border cursor-pointer select-none transition-all ${isChecked
                      ? "bg-white border-aerolab-border shadow-2xs font-semibold text-aerolab-text"
                      : "bg-aerolab-canvas/50 border-transparent text-aerolab-secondary opacity-60 hover:opacity-90"
                    }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={(e) => {
                      if (setVisibleControllers) {
                        setVisibleControllers((prev) => ({
                          ...prev,
                          [cid]: e.target.checked,
                        }));
                      }
                    }}
                    className="rounded text-aerolab-action accent-aerolab-action cursor-pointer"
                  />
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cfg.hex }} />
                  <span>{cfg.name}</span>
                  {!isAvailable && summary?.status && (
                    <span className="text-[10px] text-red-500 font-mono">({summary.status})</span>
                  )}
                </label>
              );
            })}
          </div>

          {/* Quick Time Scrubber */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-aerolab-secondary">Tiempo:</span>
            <input
              type="range"
              min="0"
              max={maxDuration}
              step="0.05"
              value={currentTime}
              onChange={(e) => setCurrentTime(parseFloat(e.target.value))}
              className="w-32 sm:w-44 cursor-pointer accent-aerolab-action"
            />
            <span className="font-mono text-aerolab-text font-semibold tabular-nums w-12 text-right">
              {currentTime.toFixed(2)}s
            </span>
          </div>
        </div>
      </div>

      {/* SUMMARY ENGINEERING CARDS (2-column layout) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Card 1: Classic PID */}
        <div className="bg-white p-4 rounded-xl border border-aerolab-border shadow-xs flex flex-col gap-2">
          <div className="flex items-center gap-2 text-xs font-bold text-aerolab-text">
            <Sliders className="w-4 h-4 text-aerolab-action" />
            <span>Selección del Controlador PD</span>
          </div>
          <p className="text-xs text-aerolab-secondary leading-relaxed">
            {results.selected_pid_explanation}
          </p>
          <div className="mt-auto pt-2 border-t border-aerolab-border/50 text-[11px] font-mono text-aerolab-secondary">
            Configuración activa: pid_{results.selected_pid}_v1.yaml
          </div>
        </div>

        {/* Card 2: Neural outer-force imitation */}
        <div className="bg-white p-4 rounded-xl border border-aerolab-border shadow-xs flex flex-col gap-2">
          <div className="flex items-center gap-2 text-xs font-bold text-aerolab-text">
            <Cpu className="w-4 h-4 text-aerolab-mlp" />
            <span>Estructura Híbrida NeuroFlight</span>
          </div>
          <p className="text-xs text-aerolab-secondary leading-relaxed">
            Las redes neuronales (MLP, GRU, LSTM) sustituyen el control externo de posición estimando la fuerza deseada en el eje corporal. El lazo interno mantiene la estabilización de actitud con cuaterniones y las protecciones físicas.
          </p>
          <div className="mt-auto pt-2 border-t border-aerolab-border/50 text-[11px] font-mono text-aerolab-secondary">
            Vector de entrada: outer_force_min_v1 (9 canales)
          </div>
        </div>
      </div>

      {/* FULL TELEMETRY SECTION */}
      <div className="bg-white p-5 rounded-xl border border-aerolab-border shadow-xs flex flex-col gap-5">
        {/* Telemetry Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-aerolab-border pb-3">
          <div>
            <h3 className="text-base font-bold text-aerolab-text flex items-center gap-2">
              <Filter className="w-4 h-4 text-aerolab-action" />
              <span>Telemetría y Registro Temporal</span>
            </h3>
            <p className="text-xs text-aerolab-secondary mt-0.5">
              Haz clic o arrastra sobre las curvas para saltar al instante deseado de la misión.
            </p>
          </div>
        </div>

        {/* COLLAPSIBLE SIGNAL SELECTOR DRAWER */}
        <div className="bg-aerolab-canvas rounded-xl border border-aerolab-border overflow-hidden transition-all">
          {/* Summary Drawer Bar */}
          <div className="p-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => setIsSignalsDrawerOpen(!isSignalsDrawerOpen)}
                className="flex items-center gap-1.5 text-xs font-semibold text-aerolab-text hover:text-aerolab-action transition-colors cursor-pointer"
              >
                <Layers className="w-4 h-4 text-aerolab-action" />
                <span>Canales seleccionados ({selectedSignals.length} activos)</span>
                {isSignalsDrawerOpen ? (
                  <ChevronUp className="w-3.5 h-3.5 text-aerolab-secondary" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5 text-aerolab-secondary" />
                )}
              </button>

              {/* Active signal badges */}
              <div className="flex flex-wrap items-center gap-1.5 ml-2">
                {selectedSignals.slice(0, 5).map((sig) => (
                  <span
                    key={sig}
                    className="inline-flex items-center gap-1 text-[11px] font-mono bg-white border border-aerolab-border px-2 py-0.5 rounded text-aerolab-text shadow-2xs"
                  >
                    <span>{sig}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedSignals(selectedSignals.filter((s) => s !== sig));
                      }}
                      className="text-aerolab-secondary hover:text-red-500 cursor-pointer"
                      title={`Quitar ${sig}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                {selectedSignals.length > 5 && (
                  <span className="text-[11px] text-aerolab-secondary font-mono">
                    +{selectedSignals.length - 5} más
                  </span>
                )}
              </div>
            </div>

            {/* Quick action buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelectedSignals(DEFAULT_SIGNALS)}
                className="flex items-center gap-1 text-[11px] font-medium text-aerolab-secondary hover:text-aerolab-text bg-white px-2.5 py-1 rounded border border-aerolab-border shadow-2xs cursor-pointer"
                title="Restablecer a señales estándar"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Estándar</span>
              </button>
              <button
                onClick={() => setIsSignalsDrawerOpen(!isSignalsDrawerOpen)}
                className="text-xs font-semibold text-aerolab-action hover:underline cursor-pointer"
              >
                {isSignalsDrawerOpen ? "Cerrar selector" : "Configurar canales"}
              </button>
            </div>
          </div>

          {/* Drawer Expanded Content */}
          {isSignalsDrawerOpen && (
            <div className="p-4 border-t border-aerolab-border flex flex-col gap-3.5 bg-white/60">
              {/* Search and Category Filters */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="relative flex-1 max-w-sm">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-aerolab-secondary" />
                  <input
                    type="text"
                    placeholder="Buscar canal o señal..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full text-xs border border-aerolab-border rounded-lg pl-8 pr-3 py-1.5 font-mono focus:border-aerolab-action bg-white"
                  />
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <button
                    onClick={() => {
                      const allVisible = Array.from(new Set([...selectedSignals, ...filteredSignals]));
                      setSelectedSignals(allVisible);
                    }}
                    className="text-[11px] text-aerolab-action hover:underline cursor-pointer font-medium"
                  >
                    Activar visibles
                  </button>
                  <span className="text-aerolab-secondary">•</span>
                  <button
                    onClick={() => setSelectedSignals([])}
                    className="text-[11px] text-aerolab-secondary hover:text-red-500 cursor-pointer font-medium"
                  >
                    Limpiar todos
                  </button>
                </div>
              </div>

              {/* Group Filter Pills */}
              <div className="flex flex-wrap gap-1.5">
                {GROUPS.map((g) => (
                  <button
                    key={g}
                    onClick={() => setSelectedGroup(g)}
                    className={`text-xs px-2.5 py-1 rounded-lg border transition-all cursor-pointer ${selectedGroup === g
                        ? "bg-aerolab-action text-white font-semibold border-aerolab-action shadow-xs"
                        : "bg-white text-aerolab-secondary border-aerolab-border hover:bg-aerolab-canvas"
                      }`}
                  >
                    {g}
                  </button>
                ))}
              </div>

              {/* Signals Checkbox Grid */}
              <div className="bg-white p-3 rounded-lg border border-aerolab-border max-h-48 overflow-y-auto">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                  {filteredSignals.map((sigKey) => {
                    const isChecked = selectedSignals.includes(sigKey);
                    const unit = sampleTelem?.units[sigKey] || "";
                    return (
                      <label
                        key={sigKey}
                        className={`flex items-center gap-2 p-1.5 rounded cursor-pointer select-none transition-all ${isChecked
                            ? "bg-aerolab-canvas text-aerolab-action font-semibold border border-aerolab-action/30"
                            : "text-aerolab-secondary hover:bg-aerolab-canvas/50"
                          }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedSignals([...selectedSignals, sigKey]);
                            } else {
                              setSelectedSignals(selectedSignals.filter((k) => k !== sigKey));
                            }
                          }}
                          className="rounded text-aerolab-action accent-aerolab-action"
                        />
                        <span className="truncate" title={sigKey}>
                          {sigKey} {unit && <span className="text-[10px] text-slate-400">({unit})</span>}
                        </span>
                      </label>
                    );
                  })}
                  {filteredSignals.length === 0 && (
                    <div className="col-span-4 py-4 text-center text-aerolab-secondary text-xs">
                      No se encontraron señales coincidentes con "{searchQuery}".
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* INTERACTIVE TELEMETRY CHARTS */}
        <TelemetryChart
          telemetryData={telemetryData}
          selectedSignals={selectedSignals}
          visibleControllers={visibleControllers}
          currentTime={currentTime}
          onTimeChange={setCurrentTime}
        />

        {/* COLLAPSIBLE SAMPLE INSPECTION TABLE */}
        <div className="bg-aerolab-canvas rounded-xl border border-aerolab-border overflow-hidden transition-all">
          <div
            onClick={() => setIsTableOpen(!isTableOpen)}
            className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-aerolab-border/20 transition-colors select-none"
          >
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-aerolab-text">
                Muestras en t = {currentTime.toFixed(2)} s (Muestra #{currentSampleIdx + 1})
              </span>
              <span className="text-[11px] text-aerolab-secondary font-mono">
                {selectedSignals.length} canales
              </span>
            </div>
            <button className="flex items-center gap-1 text-xs font-semibold text-aerolab-action">
              <span>{isTableOpen ? "Ocultar tabla de valores" : "Mostrar tabla de valores"}</span>
              {isTableOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>

          {isTableOpen && (
            <div className="p-3 border-t border-aerolab-border bg-white overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-aerolab-canvas text-aerolab-secondary border-b border-aerolab-border">
                  <tr>
                    <th className="p-2.5 font-sans font-semibold">Canal / Señal</th>
                    <th className="p-2.5 font-sans font-semibold">Grupo</th>
                    <th className="p-2.5 font-sans font-semibold">Unidad</th>
                    <th className="p-2.5 font-sans font-semibold text-[#0284C7]">PD</th>
                    <th className="p-2.5 font-sans font-semibold text-[#10B981]">MLP</th>
                    <th className="p-2.5 font-sans font-semibold text-[#F59E0B]">GRU</th>
                    <th className="p-2.5 font-sans font-semibold text-[#8B5CF6]">LSTM</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-aerolab-border/60">
                  {selectedSignals.map((sigKey) => {
                    const unit = sampleTelem?.units[sigKey] || "";
                    const group = sampleTelem?.groups[sigKey] || "";

                    return (
                      <tr key={sigKey} className="hover:bg-aerolab-canvas/50">
                        <td className="p-2.5 font-semibold text-aerolab-text">{sigKey}</td>
                        <td className="p-2.5 font-sans text-aerolab-secondary">{group}</td>
                        <td className="p-2.5 text-aerolab-secondary">{unit}</td>

                        {["classic", "mlp", "gru", "lstm"].map((cid) => {
                          const isVis = visibleControllers[cid];
                          const tSeries = telemetryData[cid]?.signals[sigKey];
                          const val = tSeries ? tSeries[currentSampleIdx] : null;

                          return (
                            <td key={cid} className={`p-2.5 tabular-nums ${!isVis ? "opacity-40" : ""}`}>
                              {val !== null && val !== undefined ? (
                                <span className="font-semibold">
                                  {typeof val === "number" ? val.toFixed(3) : val}
                                </span>
                              ) : (
                                <span className="text-aerolab-secondary/50 font-sans italic">
                                  —
                                </span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
