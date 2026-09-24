import React, { useEffect, useState } from "react";
import {
  Compass,
  Play,
  Sparkles,
  Wind,
  Plus,
  Trash2,
  AlertCircle,
  Layers,
  ChevronDown,
  ChevronUp,
  GripVertical,
} from "lucide-react";
import {
  MissionConfigRequest,
  PreviewResponse,
  TrajectoryFamily,
  ValidationResponse,
} from "../types";
import { fetchPresets, previewMission, runSimulation, validateMission } from "../api";
import { TrajectoryViewer3D } from "../components/TrajectoryViewer3D";

export interface MissionViewProps {
  presets: any;
  onSimulationStarted: (runId: string) => void;
  missionConfig: MissionConfigRequest;
  setMissionConfig: React.Dispatch<React.SetStateAction<MissionConfigRequest>>;
  setPresets: React.Dispatch<React.SetStateAction<any>>;
}

export const MissionView: React.FC<MissionViewProps> = ({
  presets,
  onSimulationStarted,
  missionConfig,
  setMissionConfig,
  setPresets,
}) => {
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [loadingPreview, setLoadingPreview] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState(false);

  // Re-validate and preview whenever configuration changes
  useEffect(() => {
    let active = true;

    const updateValidationAndPreview = async () => {
      try {
        const valRes = await validateMission(missionConfig);
        if (!active) return;
        setValidation(valRes);

        if (valRes.valid) {
          setLoadingPreview(true);
          const prevRes = await previewMission(missionConfig);
          if (!active) return;
          setPreview(prevRes);
        } else {
          setPreview(null);
        }
      } catch (err) {
        if (!active) return;
        console.error("Validation error:", err);
      } finally {
        if (active) setLoadingPreview(false);
      }
    };

    const timer = setTimeout(updateValidationAndPreview, 450);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [missionConfig]);

  const [expandedSegments, setExpandedSegments] = useState<Record<number, boolean>>({ 0: true, 1: true });
  const [draggedIdx, setDraggedIdx] = useState<number | null>(null);
  const [dragOverIdx, setDragOverIdx] = useState<number | null>(null);

  const handleSwapSegments = (fromIdx: number, toIdx: number) => {
    if (fromIdx === toIdx) return;
    const newSegs = [...(missionConfig.segments || [])];
    const temp = newSegs[fromIdx];
    newSegs[fromIdx] = newSegs[toIdx];
    newSegs[toIdx] = temp;
    setMissionConfig({ ...missionConfig, segments: newSegs });

    // Also swap expanded state
    setExpandedSegments((prev) => {
      const fromExp = prev[fromIdx] ?? false;
      const toExp = prev[toIdx] ?? false;
      return {
        ...prev,
        [fromIdx]: toExp,
        [toIdx]: fromExp,
      };
    });
  };

  const handleDragStart = (e: React.DragEvent, idx: number) => {
    setDraggedIdx(idx);
    e.dataTransfer.setData("text/plain", String(idx));
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent, idx: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (dragOverIdx !== idx) {
      setDragOverIdx(idx);
    }
  };

  const handleDragLeave = (_e: React.DragEvent, idx: number) => {
    if (dragOverIdx === idx) {
      setDragOverIdx(null);
    }
  };

  const handleDrop = (e: React.DragEvent, toIdx: number) => {
    e.preventDefault();
    const dataIdx = e.dataTransfer.getData("text/plain");
    const fromIdx = draggedIdx ?? (dataIdx ? parseInt(dataIdx, 10) : null);
    if (fromIdx !== null && !isNaN(fromIdx) && fromIdx !== toIdx) {
      handleSwapSegments(fromIdx, toIdx);
    }
    setDraggedIdx(null);
    setDragOverIdx(null);
  };

  const handleDragEnd = () => {
    setDraggedIdx(null);
    setDragOverIdx(null);
  };

  const updateSegmentParam = (segIdx: number, key: string, value: any) => {
    const newSegs = [...(missionConfig.segments || [])];
    if (!newSegs[segIdx]) return;
    newSegs[segIdx] = {
      ...newSegs[segIdx],
      params: {
        ...(newSegs[segIdx].params || {}),
        [key]: value,
      },
    };
    setMissionConfig({ ...missionConfig, segments: newSegs });
  };

  const handleSegmentTypeChange = (idx: number, newType: string) => {
    const newSegs = [...(missionConfig.segments || [])];
    let defaultParams: any = {};
    if (newType === "waypoint") {
      const p = presets?.waypoint_presets?.waypoint_clean;
      defaultParams = p
        ? {
          waypoints: p.waypoints.map((wp: any) => [...wp]),
          max_speed_m_s: p.max_speed_m_s,
          max_acceleration_m_s2: p.max_acceleration_m_s2,
          waypoint_tolerance_m: p.waypoint_tolerance_m,
          waypoint_speed_tolerance_m_s: p.waypoint_speed_tolerance_m_s,
          dwell_time_s: p.dwell_time_s,
        }
        : {
          waypoints: [[0, 0, 2], [1.5, 1.5, 2], [0, 2, 2]],
          max_speed_m_s: 0.6,
          max_acceleration_m_s2: 0.5,
          waypoint_tolerance_m: 0.2,
          waypoint_speed_tolerance_m_s: 0.2,
          dwell_time_s: 0.4,
        };
    } else if (newType === "circle") {
      defaultParams = {
        center_W_m: [0, 0, 2.0],
        radius_m: 1.5,
        omega_rad_s: 0.6,
        yaw_mode: "forward",
        tilt_deg: 0,
      };
    } else if (newType === "hold") {
      defaultParams = {
        position_W_m: [0, 0, 2.0],
        yaw_rad: 0,
      };
    } else if (newType === "lissajous") {
      defaultParams = {
        center_W_m: [0, 0, 2.5],
        amplitudes: [1.5, 1.5, 0.5],
        omegas: [0.5, 0.7, 0.3],
      };
    } else if (newType === "lemniscate") {
      defaultParams = {
        center_W_m: [0, 0, 2.0],
        a: 2.0,
        b: 1.0,
        omega_rad_s: 0.35,
      };
    } else {
      defaultParams = presets?.initial_variants?.[newType] || {};
    }

    newSegs[idx] = {
      ...newSegs[idx],
      type: newType,
      duration: newType === "waypoint" ? undefined : newSegs[idx].duration ?? 8,
      params: defaultParams,
    };
    setMissionConfig({ ...missionConfig, segments: newSegs });
  };

  // Family selector handler
  const handleFamilyChange = (fam: TrajectoryFamily) => {
    if (presets?.initial_variants?.[fam]) {
      setMissionConfig((prev) => ({
        ...prev,
        mode: "simple",
        family: fam,
        params: { ...presets.initial_variants[fam] },
      }));
    } else {
      setMissionConfig((prev) => ({
        ...prev,
        mode: "simple",
        family: fam,
      }));
    }
  };

  // Switch to Composite Mode
  const handleEnableComposite = () => {
    if (presets?.composite_presets?.composite_classic) {
      const p = presets.composite_presets.composite_classic;
      setMissionConfig((prev) => ({
        ...prev,
        mode: "composite",
        family: "composite" as TrajectoryFamily,
        transition_speed: p.transition_speed || 0.8,
        segments: [...p.segments],
      }));
    }
  };

  // Switch to Simple Mode
  const handleEnableSimple = () => {
    handleFamilyChange(TrajectoryFamily.CIRCLE);
  };

  // Preset loader for waypoints
  const handleLoadWaypointPreset = (key: string) => {
    const p = presets?.waypoint_presets?.[key];
    if (!p) return;
    setMissionConfig((prev) => ({
      ...prev,
      params: {
        ...prev.params,
        waypoints: p.waypoints.map((wp: any) => [...wp]),
        max_speed_m_s: p.max_speed_m_s,
        max_acceleration_m_s2: p.max_acceleration_m_s2,
        dwell_time_s: p.dwell_time_s,
      },
    }));
  };

  // Nueva variante: la semilla elige parámetros nuevos, no solo un número.
  const handleGenerateVariant = async () => {
    const nextSeed = missionConfig.seed + 1;
    try {
      const catalog = await fetchPresets(nextSeed);
      setPresets(catalog);
      if (missionConfig.mode === "composite") {
        const keys = Object.keys(catalog?.composite_presets || {});
        const pick = keys.length ? catalog.composite_presets[keys[nextSeed % keys.length]] : null;
        if (!pick) return;
        setMissionConfig((prev) => ({
          ...prev,
          seed: nextSeed,
          transition_speed: pick.transition_speed || 0.8,
          segments: pick.segments.map((seg: any) => ({
            ...seg,
            params: JSON.parse(JSON.stringify(seg.params || {})),
          })),
        }));
        return;
      }
      const variant = catalog?.initial_variants?.[missionConfig.family];
      if (!variant) return;
      setMissionConfig((prev) => ({
        ...prev,
        seed: nextSeed,
        params: { ...variant },
      }));
    } catch (err: any) {
      alert(`No se pudo generar otra variante: ${err.message}`);
    }
  };

  // Execute simulation
  const handleExecute = async () => {
    if (!validation?.valid) return;
    setIsSimulating(true);
    try {
      const res = await runSimulation(missionConfig);
      onSimulationStarted(res.run_id);
    } catch (err: any) {
      alert(`Error iniciando simulación: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* LEFT COLUMN: Controls & Parameters (7 Cols) */}
      <div className="lg:col-span-7 flex flex-col gap-5">
        {/* Mode & Family Selection Card */}
        <div className="bg-white p-5 rounded-xl border border-aerolab-border shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-aerolab-text flex items-center gap-2">
              <Compass className="w-5 h-5 text-aerolab-action" />
              <span>Configuración de Misión</span>
            </h2>

            {/* Mode switch */}
            <div className="flex items-center gap-1 bg-aerolab-canvas p-1 rounded-lg border border-aerolab-border text-xs">
              <button
                type="button"
                onClick={handleEnableSimple}
                className={`px-2.5 py-1 rounded font-medium ${missionConfig.mode === "simple"
                    ? "bg-white text-aerolab-action shadow-xs font-semibold"
                    : "text-aerolab-secondary hover:text-aerolab-text"
                  }`}
              >
                Misión Simple
              </button>
              <button
                type="button"
                onClick={handleEnableComposite}
                className={`px-2.5 py-1 rounded font-medium ${missionConfig.mode === "composite"
                    ? "bg-white text-aerolab-action shadow-xs font-semibold"
                    : "text-aerolab-secondary hover:text-aerolab-text"
                  }`}
              >
                Composición por Tramos
              </button>
            </div>
          </div>

          {/* Simple Family Selector Buttons */}
          {missionConfig.mode === "simple" && (
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {[
                { id: TrajectoryFamily.HOLD, label: "Mantener pos." },
                { id: TrajectoryFamily.CIRCLE, label: "Círculo" },
                { id: TrajectoryFamily.LISSAJOUS, label: "Lissajous" },
                { id: TrajectoryFamily.WAYPOINT, label: "Por puntos" },
                { id: TrajectoryFamily.LEMNISCATE, label: "Lemniscata" },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleFamilyChange(item.id)}
                  className={`px-3 py-2 rounded-lg text-xs font-medium border text-center transition-all ${missionConfig.family === item.id
                      ? "border-aerolab-action bg-aerolab-action/5 text-aerolab-action font-semibold shadow-xs"
                      : "border-aerolab-border bg-white text-aerolab-secondary hover:bg-aerolab-canvas"
                    }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Family Parameters Form */}
        <div className="bg-white p-5 rounded-xl border border-aerolab-border shadow-xs flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-aerolab-border pb-3">
            <span className="text-sm font-semibold text-aerolab-text capitalize">
              {missionConfig.mode === "composite" ? "Tramos de la Composición" : `Parámetros: ${missionConfig.family}`}
            </span>

            <div className="flex items-center gap-3">
              {missionConfig.mode === "simple" && missionConfig.family !== TrajectoryFamily.WAYPOINT && (
                <div className="flex items-center gap-1.5 text-xs">
                  <label className="text-aerolab-secondary font-medium whitespace-nowrap">Duración (s):</label>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    max="180"
                    value={missionConfig.params.duration ?? (missionConfig.family === "hold" ? 10 : missionConfig.family === "circle" ? 15 : missionConfig.family === "lissajous" ? 20 : 18)}
                    onChange={(e) => {
                      const d = parseFloat(e.target.value);
                      setMissionConfig({
                        ...missionConfig,
                        params: {
                          ...missionConfig.params,
                          duration: Number.isFinite(d) ? d : 15,
                        },
                      });
                    }}
                    className="w-16 border border-aerolab-border rounded px-2 py-1 font-mono text-center text-xs font-semibold bg-white"
                  />
                </div>
              )}

              <button
                onClick={handleGenerateVariant}
                className="flex items-center gap-1.5 text-xs text-aerolab-action hover:text-aerolab-action/80 font-medium px-2 py-1 rounded bg-aerolab-canvas border border-aerolab-border"
                title="Genera otra variante inicial con diferente semilla"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Siguiente variante</span>
              </button>
            </div>
          </div>

          {/* 1. HOLD FORM */}
          {missionConfig.mode === "simple" && missionConfig.family === TrajectoryFamily.HOLD && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Posición X (m)</label>
                <input
                  type="number"
                  step="0.1"
                  value={missionConfig.params.position_W_m?.[0] ?? 0.0}
                  onChange={(e) => {
                    const x = parseFloat(e.target.value) || 0;
                    const p = [...(missionConfig.params.position_W_m || [0, 0, 1.5])];
                    p[0] = x;
                    setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, position_W_m: p } });
                  }}
                  className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Posición Y (m)</label>
                <input
                  type="number"
                  step="0.1"
                  value={missionConfig.params.position_W_m?.[1] ?? 0.0}
                  onChange={(e) => {
                    const y = parseFloat(e.target.value) || 0;
                    const p = [...(missionConfig.params.position_W_m || [0, 0, 1.5])];
                    p[1] = y;
                    setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, position_W_m: p } });
                  }}
                  className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Altura Z (m)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.3"
                  value={missionConfig.params.position_W_m?.[2] ?? 1.5}
                  onChange={(e) => {
                    const z = parseFloat(e.target.value) || 1.5;
                    const p = [...(missionConfig.params.position_W_m || [0, 0, 1.5])];
                    p[2] = z;
                    setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, position_W_m: p } });
                  }}
                  className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                />
              </div>
            </div>
          )}

          {/* 2. CIRCLE FORM */}
          {missionConfig.mode === "simple" && missionConfig.family === TrajectoryFamily.CIRCLE && (() => {
            const currentR = missionConfig.params.radius_m ?? 1.5;
            const maxOmega = Math.min(1.5 / currentR, Math.sqrt(1.0 / currentR));
            const safeMaxOmega = Math.max(0.1, parseFloat(maxOmega.toFixed(2)));

            return (
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-aerolab-secondary mb-1 block">Radio R (m, 0.5 a 4.0)</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.5"
                      max="4.0"
                      value={currentR}
                      onChange={(e) => {
                        const r = parseFloat(e.target.value) || 1.5;
                        const newMaxOmega = Math.min(1.5 / r, Math.sqrt(1.0 / r));
                        const safeNewMax = Math.max(0.1, parseFloat(newMaxOmega.toFixed(2)));
                        const currentOmega = missionConfig.params.omega_rad_s ?? 0.6;
                        const clampedOmega = Math.min(currentOmega, safeNewMax);
                        setMissionConfig({
                          ...missionConfig,
                          params: { ...missionConfig.params, radius_m: r, omega_rad_s: clampedOmega },
                        });
                      }}
                      className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-aerolab-secondary mb-1 block">
                      Vel. angular ω (rad/s, 0.1 a {safeMaxOmega})
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      min="0.1"
                      max={safeMaxOmega}
                      value={missionConfig.params.omega_rad_s ?? 0.6}
                      onChange={(e) => {
                        const rawW = parseFloat(e.target.value) || 0.6;
                        const clampedW = Math.max(0.1, Math.min(safeMaxOmega, rawW));
                        setMissionConfig({
                          ...missionConfig,
                          params: { ...missionConfig.params, omega_rad_s: clampedW },
                        });
                      }}
                      className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-aerolab-secondary mb-1 block">Centro [X, Y, Z] (m)</label>
                    <div className="grid grid-cols-3 gap-1">
                      {[0, 1, 2].map((axisIdx) => (
                        <input
                          key={axisIdx}
                          type="number"
                          step="0.1"
                          value={missionConfig.params.center_W_m?.[axisIdx] ?? (axisIdx === 2 ? 2.0 : 0.0)}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0.0;
                            const c = [...(missionConfig.params.center_W_m || [0, 0, 2.0])];
                            c[axisIdx] = val;
                            setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, center_W_m: c } });
                          }}
                          placeholder={["X", "Y", "Z"][axisIdx]}
                          title={["Centro X (m)", "Centro Y (m)", "Centro Z (m)"][axisIdx]}
                          className="w-full text-xs border border-aerolab-border rounded px-1.5 py-1.5 font-mono text-center"
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Inclined Circle Controls */}
                <div className="bg-aerolab-canvas p-3.5 rounded-lg border border-aerolab-border flex flex-col gap-3">
                  <div className="text-xs font-semibold text-aerolab-text flex items-center justify-between">
                    <span>Inclinación del plano del círculo</span>
                    <span className="font-mono text-aerolab-action font-bold">
                      {missionConfig.params.tilt_deg ?? 0}°
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-aerolab-secondary">0°</span>
                    <input
                      type="range"
                      min="0"
                      max="30"
                      step="1"
                      value={missionConfig.params.tilt_deg ?? 0}
                      onChange={(e) => {
                        const t = parseFloat(e.target.value) || 0;
                        setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, tilt_deg: t } });
                      }}
                      className="w-full cursor-pointer accent-aerolab-action"
                    />
                    <span className="text-xs text-aerolab-secondary">30°</span>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* 3. LISSAJOUS FORM */}
          {missionConfig.mode === "simple" && missionConfig.family === TrajectoryFamily.LISSAJOUS && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Amplitudes [X, Y, Z] (m)</label>
                <div className="grid grid-cols-3 gap-1">
                  {[0, 1, 2].map((i) => (
                    <input
                      key={i}
                      type="number"
                      step="0.1"
                      value={missionConfig.params.amplitudes?.[i] ?? 1.5}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0.1;
                        const amps = [...(missionConfig.params.amplitudes || [1.5, 1.5, 0.5])];
                        amps[i] = val;
                        setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, amplitudes: amps } });
                      }}
                      className="text-xs border border-aerolab-border rounded px-2 py-1 font-mono text-center"
                    />
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Frecuencias [ωx, ωy, ωz]</label>
                <div className="grid grid-cols-3 gap-1">
                  {[0, 1, 2].map((i) => (
                    <input
                      key={i}
                      type="number"
                      step="0.05"
                      value={missionConfig.params.omegas?.[i] ?? 0.5}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0.1;
                        const oms = [...(missionConfig.params.omegas || [0.5, 0.7, 0.3])];
                        oms[i] = val;
                        setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, omegas: oms } });
                      }}
                      className="text-xs border border-aerolab-border rounded px-2 py-1 font-mono text-center"
                    />
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Centro [X, Y, Z] (m)</label>
                <div className="grid grid-cols-3 gap-1">
                  {[0, 1, 2].map((axisIdx) => (
                    <input
                      key={axisIdx}
                      type="number"
                      step="0.1"
                      value={missionConfig.params.center_W_m?.[axisIdx] ?? (axisIdx === 2 ? 2.5 : 0.0)}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0.0;
                        const c = [...(missionConfig.params.center_W_m || [0, 0, 2.5])];
                        c[axisIdx] = val;
                        setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, center_W_m: c } });
                      }}
                      placeholder={["X", "Y", "Z"][axisIdx]}
                      title={["Centro X (m)", "Centro Y (m)", "Centro Z (m)"][axisIdx]}
                      className="w-full text-xs border border-aerolab-border rounded px-1.5 py-1.5 font-mono text-center"
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 4. WAYPOINT FORM */}
          {missionConfig.mode === "simple" && missionConfig.family === TrajectoryFamily.WAYPOINT && (
            <div className="flex flex-col gap-3">
              {/* Presets dropdown */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-aerolab-secondary whitespace-nowrap">Presets OOD:</span>
                <select
                  onChange={(e) => handleLoadWaypointPreset(e.target.value)}
                  className="text-xs border border-aerolab-border rounded-lg px-2.5 py-1.5 bg-white font-medium text-aerolab-text"
                >
                  <option value="waypoint_clean">Ruta limpia con ascenso</option>
                  <option value="helix_ascending">Hélice ascendente (OOD)</option>
                  <option value="helix_descending">Hélice descendente (OOD)</option>
                  <option value="helix_tight">Hélice compacta (3 vueltas)</option>
                </select>
              </div>

              {/* Waypoints coordinate table */}
              <div className="border border-aerolab-border rounded-lg overflow-hidden max-h-48 overflow-y-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-aerolab-canvas text-aerolab-secondary border-b border-aerolab-border sticky top-0">
                    <tr>
                      <th className="p-2 w-8">#</th>
                      <th className="p-2">X (m)</th>
                      <th className="p-2">Y (m)</th>
                      <th className="p-2">Z (m)</th>
                      <th className="p-2 w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {(missionConfig.params.waypoints || []).map((wp: number[], idx: number) => (
                      <tr key={idx} className="border-b border-aerolab-border/50 hover:bg-aerolab-canvas/50">
                        <td className="p-2 font-sans text-aerolab-secondary">{idx + 1}</td>
                        <td className="p-1">
                          <input
                            type="number"
                            step="0.1"
                            value={wp[0]}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value) || 0;
                              const wps = [...missionConfig.params.waypoints];
                              wps[idx][0] = val;
                              setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, waypoints: wps } });
                            }}
                            className="w-16 border border-aerolab-border rounded px-1.5 py-0.5 text-center"
                          />
                        </td>
                        <td className="p-1">
                          <input
                            type="number"
                            step="0.1"
                            value={wp[1]}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value) || 0;
                              const wps = [...missionConfig.params.waypoints];
                              wps[idx][1] = val;
                              setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, waypoints: wps } });
                            }}
                            className="w-16 border border-aerolab-border rounded px-1.5 py-0.5 text-center"
                          />
                        </td>
                        <td className="p-1">
                          <input
                            type="number"
                            step="0.1"
                            value={wp[2]}
                            onChange={(e) => {
                              const val = parseFloat(e.target.value) || 0;
                              const wps = [...missionConfig.params.waypoints];
                              wps[idx][2] = val;
                              setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, waypoints: wps } });
                            }}
                            className="w-16 border border-aerolab-border rounded px-1.5 py-0.5 text-center"
                          />
                        </td>
                        <td className="p-1 text-center">
                          {missionConfig.params.waypoints.length > 2 && (
                            <button
                              onClick={() => {
                                const wps = missionConfig.params.waypoints.filter((_: any, i: number) => i !== idx);
                                setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, waypoints: wps } });
                              }}
                              className="text-aerolab-secondary hover:text-aerolab-lstm p-1 rounded"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Add point button */}
              <button
                onClick={() => {
                  const wps = [...(missionConfig.params.waypoints || [])];
                  const last = wps[wps.length - 1] || [0, 0, 2];
                  wps.push([last[0] + 1.0, last[1], last[2]]);
                  setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, waypoints: wps } });
                }}
                className="flex items-center justify-center gap-1.5 text-xs text-aerolab-action font-medium py-1.5 border border-dashed border-aerolab-border rounded-lg hover:bg-aerolab-canvas"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Añadir punto de ruta</span>
              </button>
            </div>
          )}

          {/* 5. LEMNISCATE FORM */}
          {missionConfig.mode === "simple" && missionConfig.family === TrajectoryFamily.LEMNISCATE && (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Semieje a (m, 0.5 a 4.0)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.5"
                  max="4.0"
                  value={missionConfig.params.a ?? 2.0}
                  onChange={(e) => {
                    const a = parseFloat(e.target.value) || 2.0;
                    setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, a } });
                  }}
                  className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Semieje b (m, 0.3 a 2.5)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0.3"
                  max="2.5"
                  value={missionConfig.params.b ?? 1.0}
                  onChange={(e) => {
                    const b = parseFloat(e.target.value) || 1.0;
                    setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, b } });
                  }}
                  className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Velocidad angular ω</label>
                <input
                  type="number"
                  step="0.05"
                  value={missionConfig.params.omega_rad_s ?? 0.35}
                  onChange={(e) => {
                    const w = parseFloat(e.target.value) || 0.35;
                    setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, omega_rad_s: w } });
                  }}
                  className="w-full text-sm border border-aerolab-border rounded-lg px-3 py-1.5 font-mono"
                />
              </div>
              <div>
                <label className="text-xs text-aerolab-secondary mb-1 block">Centro [X, Y, Z] (m)</label>
                <div className="grid grid-cols-3 gap-1">
                  {[0, 1, 2].map((axisIdx) => (
                    <input
                      key={axisIdx}
                      type="number"
                      step="0.1"
                      value={missionConfig.params.center_W_m?.[axisIdx] ?? (axisIdx === 2 ? 2.0 : 0.0)}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0.0;
                        const c = [...(missionConfig.params.center_W_m || [0, 0, 2.0])];
                        c[axisIdx] = val;
                        setMissionConfig({ ...missionConfig, params: { ...missionConfig.params, center_W_m: c } });
                      }}
                      placeholder={["X", "Y", "Z"][axisIdx]}
                      title={["Centro X (m)", "Centro Y (m)", "Centro Z (m)"][axisIdx]}
                      className="w-full text-xs border border-aerolab-border rounded px-1.5 py-1.5 font-mono text-center"
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 6. COMPOSITE SEGMENTS EDITOR */}
          {missionConfig.mode === "composite" && (
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between text-xs text-aerolab-secondary">
                <span>Define entre 2 y 4 tramos encadenados (arrastra el selector para intercambiar orden):</span>
                <span>PD seleccionado por longitud nominal dominante</span>
              </div>

              {(missionConfig.segments || []).map((seg, idx) => {
                const isExpanded = !!expandedSegments[idx];
                const isDragging = draggedIdx === idx;
                const isOver = dragOverIdx === idx;

                return (
                  <div
                    key={idx}
                    onDragOver={(e) => handleDragOver(e, idx)}
                    onDragLeave={(e) => handleDragLeave(e, idx)}
                    onDrop={(e) => handleDrop(e, idx)}
                    className={`p-3 rounded-lg border flex flex-col gap-2.5 transition-all ${
                      isDragging
                        ? "opacity-40 border-dashed border-aerolab-action bg-aerolab-action/5 scale-[0.99]"
                        : isOver
                        ? "border-aerolab-action ring-2 ring-aerolab-action/40 bg-sky-50/50 shadow-sm"
                        : "bg-aerolab-canvas border-aerolab-border"
                    }`}
                  >
                    {/* Segment Header */}
                    <div className="flex items-center justify-between gap-2">
                      <div
                        draggable
                        onDragStart={(e) => handleDragStart(e, idx)}
                        onDragEnd={handleDragEnd}
                        className="flex items-center gap-1.5 cursor-grab active:cursor-grabbing select-none group"
                        title="Arrastra para intercambiar el orden de este tramo"
                      >
                        <GripVertical className="w-4 h-4 text-aerolab-secondary/60 group-hover:text-aerolab-action transition-colors shrink-0" />
                        <span className="w-5 h-5 rounded-full bg-aerolab-action text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                          {idx + 1}
                        </span>
                        <select
                          value={seg.type}
                          onChange={(e) => handleSegmentTypeChange(idx, e.target.value)}
                          className="text-xs font-semibold border border-aerolab-border rounded px-2 py-1 bg-white capitalize cursor-pointer focus:ring-1 focus:ring-aerolab-action"
                        >
                          <option value="hold">Mantener posición</option>
                          <option value="circle">Círculo</option>
                          <option value="lissajous">Lissajous</option>
                          <option value="waypoint">Ruta por puntos</option>
                          <option value="lemniscate">Lemniscata</option>
                        </select>
                      </div>

                      <div className="flex items-center gap-2">
                        {seg.type === "waypoint" ? (
                          <span className="text-xs text-aerolab-secondary">
                            Termina al llegar y permanecer
                          </span>
                        ) : (
                          <>
                            <label className="text-xs text-aerolab-secondary">Duración (s):</label>
                            <input
                              type="number"
                              step="1"
                              min="1"
                              max="90"
                              value={seg.duration ?? 5.0}
                              onChange={(e) => {
                                const dur = parseFloat(e.target.value);
                                const newSegs = [...(missionConfig.segments || [])];
                                newSegs[idx] = { ...newSegs[idx], duration: Number.isFinite(dur) ? dur : newSegs[idx].duration };
                                setMissionConfig({ ...missionConfig, segments: newSegs });
                              }}
                              className="w-14 text-xs border border-aerolab-border rounded px-1.5 py-1 text-center font-mono bg-white"
                            />
                          </>
                        )}
                        <button
                          type="button"
                          onClick={() => setExpandedSegments((prev) => ({ ...prev, [idx]: !isExpanded }))}
                          className="text-aerolab-secondary hover:text-aerolab-text p-1 rounded cursor-pointer"
                          title={isExpanded ? "Ocultar parámetros" : "Configurar parámetros"}
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                        {(missionConfig.segments?.length || 0) > 2 && (
                          <button
                            type="button"
                            onClick={() => {
                              const newSegs = missionConfig.segments?.filter((_, i) => i !== idx);
                              setMissionConfig({ ...missionConfig, segments: newSegs });
                            }}
                            className="text-aerolab-secondary hover:text-red-500 p-1 rounded cursor-pointer"
                            title="Eliminar tramo"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Expandable Segment Parameter Editor */}
                    {isExpanded && (
                      <div className="pt-2 border-t border-aerolab-border/60 flex flex-col gap-2">
                        {seg.type === "circle" && (
                          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Radio R (m)</label>
                              <input
                                type="number"
                                step="0.1"
                                min="0.5"
                                max="4.0"
                                value={seg.params?.radius_m ?? 1.5}
                                onChange={(e) => updateSegmentParam(idx, "radius_m", parseFloat(e.target.value) || 1.5)}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Vel. angular ω (rad/s)</label>
                              <input
                                type="number"
                                step="0.05"
                                min="0.1"
                                max="2.0"
                                value={seg.params?.omega_rad_s ?? 0.6}
                                onChange={(e) => updateSegmentParam(idx, "omega_rad_s", parseFloat(e.target.value) || 0.6)}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                            <div className="col-span-2">
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Centro [X, Y, Z] (m)</label>
                              <div className="grid grid-cols-3 gap-1">
                                {[0, 1, 2].map((axisIdx) => (
                                  <input
                                    key={axisIdx}
                                    type="number"
                                    step="0.1"
                                    value={seg.params?.center_W_m?.[axisIdx] ?? (axisIdx === 2 ? 2.0 : 0.0)}
                                    onChange={(e) => {
                                      const val = parseFloat(e.target.value) || 0.0;
                                      const c = [...(seg.params?.center_W_m || [0, 0, 2.0])];
                                      c[axisIdx] = val;
                                      updateSegmentParam(idx, "center_W_m", c);
                                    }}
                                    placeholder={["X", "Y", "Z"][axisIdx]}
                                    title={["Centro X (m)", "Centro Y (m)", "Centro Z (m)"][axisIdx]}
                                    className="w-full border border-aerolab-border rounded px-1 py-1 font-mono text-center bg-white text-xs"
                                  />
                                ))}
                              </div>
                            </div>
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Inclinación (°)</label>
                              <input
                                type="number"
                                step="1"
                                min="0"
                                max="30"
                                value={seg.params?.tilt_deg ?? 0}
                                onChange={(e) => updateSegmentParam(idx, "tilt_deg", parseFloat(e.target.value) || 0)}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                          </div>
                        )}

                        {seg.type === "waypoint" && (
                          <div className="flex flex-col gap-2 text-xs">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-1.5">
                                <span className="text-[11px] text-aerolab-secondary">Cargar ruta:</span>
                                <select
                                  onChange={(e) => {
                                    const p = presets?.waypoint_presets?.[e.target.value];
                                    if (!p) return;
                                    const newSegs = [...(missionConfig.segments || [])];
                                    newSegs[idx].params = {
                                      ...newSegs[idx].params,
                                      waypoints: p.waypoints.map((wp: any) => [...wp]),
                                      max_speed_m_s: p.max_speed_m_s,
                                      max_acceleration_m_s2: p.max_acceleration_m_s2,
                                      dwell_time_s: p.dwell_time_s,
                                    };
                                    setMissionConfig({ ...missionConfig, segments: newSegs });
                                  }}
                                  className="text-[11px] border border-aerolab-border rounded px-2 py-1 bg-white font-medium text-aerolab-text cursor-pointer"
                                >
                                  <option value="">-- Presets OOD --</option>
                                  <option value="waypoint_clean">Ruta limpia con ascenso</option>
                                  <option value="helix_ascending">Hélice ascendente (OOD)</option>
                                  <option value="helix_descending">Hélice descendente (OOD)</option>
                                  <option value="helix_tight">Hélice compacta (3 vueltas)</option>
                                </select>
                              </div>
                              <div className="flex items-center gap-1.5">
                                <label className="text-[11px] text-aerolab-secondary">Vel. máx (m/s):</label>
                                <input
                                  type="number"
                                  step="0.1"
                                  min="0.2"
                                  max="1.5"
                                  value={seg.params?.max_speed_m_s ?? 0.6}
                                  onChange={(e) => updateSegmentParam(idx, "max_speed_m_s", parseFloat(e.target.value) || 0.6)}
                                  className="w-14 border border-aerolab-border rounded px-1 py-0.5 font-mono text-center bg-white"
                                />
                              </div>
                            </div>

                            {/* Waypoint table */}
                            <div className="border border-aerolab-border rounded overflow-hidden max-h-36 overflow-y-auto bg-white">
                              <table className="w-full text-left text-xs font-mono">
                                <thead className="bg-aerolab-canvas text-aerolab-secondary border-b border-aerolab-border sticky top-0">
                                  <tr>
                                    <th className="p-1.5 w-6">#</th>
                                    <th className="p-1.5">X (m)</th>
                                    <th className="p-1.5">Y (m)</th>
                                    <th className="p-1.5">Z (m)</th>
                                    <th className="p-1.5 w-8"></th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {(seg.params?.waypoints || [[0, 0, 2], [2, 0, 2]]).map((wp: number[], wpIdx: number) => (
                                    <tr key={wpIdx} className="border-b border-aerolab-border/40 hover:bg-aerolab-canvas/40">
                                      <td className="p-1 text-aerolab-secondary">{wpIdx + 1}</td>
                                      <td className="p-0.5">
                                        <input
                                          type="number"
                                          step="0.1"
                                          value={wp[0]}
                                          onChange={(e) => {
                                            const val = parseFloat(e.target.value) || 0;
                                            const wps = (seg.params?.waypoints || []).map((w: any) => [...w]);
                                            wps[wpIdx][0] = val;
                                            updateSegmentParam(idx, "waypoints", wps);
                                          }}
                                          className="w-14 border border-aerolab-border rounded px-1 py-0.5 text-center text-xs"
                                        />
                                      </td>
                                      <td className="p-0.5">
                                        <input
                                          type="number"
                                          step="0.1"
                                          value={wp[1]}
                                          onChange={(e) => {
                                            const val = parseFloat(e.target.value) || 0;
                                            const wps = (seg.params?.waypoints || []).map((w: any) => [...w]);
                                            wps[wpIdx][1] = val;
                                            updateSegmentParam(idx, "waypoints", wps);
                                          }}
                                          className="w-14 border border-aerolab-border rounded px-1 py-0.5 text-center text-xs"
                                        />
                                      </td>
                                      <td className="p-0.5">
                                        <input
                                          type="number"
                                          step="0.1"
                                          value={wp[2]}
                                          onChange={(e) => {
                                            const val = parseFloat(e.target.value) || 0.5;
                                            const wps = (seg.params?.waypoints || []).map((w: any) => [...w]);
                                            wps[wpIdx][2] = val;
                                            updateSegmentParam(idx, "waypoints", wps);
                                          }}
                                          className="w-14 border border-aerolab-border rounded px-1 py-0.5 text-center text-xs"
                                        />
                                      </td>
                                      <td className="p-0.5 text-center">
                                        {(seg.params?.waypoints?.length || 0) > 2 && (
                                          <button
                                            type="button"
                                            onClick={() => {
                                              const wps = (seg.params?.waypoints || []).filter((_: any, i: number) => i !== wpIdx);
                                              updateSegmentParam(idx, "waypoints", wps);
                                            }}
                                            className="text-aerolab-secondary hover:text-red-500 p-0.5 rounded cursor-pointer"
                                          >
                                            <Trash2 className="w-3 h-3" />
                                          </button>
                                        )}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>

                            <button
                              type="button"
                              onClick={() => {
                                const wps = (seg.params?.waypoints || [[0, 0, 2], [2, 0, 2]]).map((w: any) => [...w]);
                                const last = wps[wps.length - 1] || [0, 0, 2];
                                wps.push([last[0] + 1.0, last[1], last[2]]);
                                updateSegmentParam(idx, "waypoints", wps);
                              }}
                              className="flex items-center justify-center gap-1 text-[11px] text-aerolab-action font-medium py-1 border border-dashed border-aerolab-border rounded bg-white hover:bg-aerolab-canvas cursor-pointer"
                            >
                              <Plus className="w-3 h-3" />
                              <span>Añadir punto a este tramo</span>
                            </button>
                          </div>
                        )}

                        {seg.type === "hold" && (
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            {[0, 1, 2].map((axisIdx) => {
                              const labels = ["X (m)", "Y (m)", "Z (m)"];
                              return (
                                <div key={axisIdx}>
                                  <label className="text-[11px] text-aerolab-secondary block mb-0.5">{labels[axisIdx]}</label>
                                  <input
                                    type="number"
                                    step="0.1"
                                    value={seg.params?.position_W_m?.[axisIdx] ?? (axisIdx === 2 ? 2.0 : 0.0)}
                                    onChange={(e) => {
                                      const val = parseFloat(e.target.value) || 0.0;
                                      const pos = [...(seg.params?.position_W_m || [0, 0, 2.0])];
                                      pos[axisIdx] = val;
                                      updateSegmentParam(idx, "position_W_m", pos);
                                    }}
                                    className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                                  />
                                </div>
                              );
                            })}
                          </div>
                        )}

                        {seg.type === "lissajous" && (
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Amplitudes [Ax, Ay, Az]</label>
                              <input
                                type="number"
                                step="0.1"
                                value={seg.params?.amplitudes?.[0] ?? 1.5}
                                onChange={(e) => {
                                  const a = parseFloat(e.target.value) || 1.5;
                                  updateSegmentParam(idx, "amplitudes", [a, a, 0.5]);
                                }}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Frecuencia ω</label>
                              <input
                                type="number"
                                step="0.05"
                                value={seg.params?.omegas?.[0] ?? 0.5}
                                onChange={(e) => {
                                  const w = parseFloat(e.target.value) || 0.5;
                                  updateSegmentParam(idx, "omegas", [w, w + 0.2, 0.3]);
                                }}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Centro [X, Y, Z] (m)</label>
                              <div className="grid grid-cols-3 gap-1">
                                {[0, 1, 2].map((axisIdx) => (
                                  <input
                                    key={axisIdx}
                                    type="number"
                                    step="0.1"
                                    value={seg.params?.center_W_m?.[axisIdx] ?? (axisIdx === 2 ? 2.5 : 0.0)}
                                    onChange={(e) => {
                                      const val = parseFloat(e.target.value) || 0.0;
                                      const c = [...(seg.params?.center_W_m || [0, 0, 2.5])];
                                      c[axisIdx] = val;
                                      updateSegmentParam(idx, "center_W_m", c);
                                    }}
                                    placeholder={["X", "Y", "Z"][axisIdx]}
                                    title={["Centro X (m)", "Centro Y (m)", "Centro Z (m)"][axisIdx]}
                                    className="w-full border border-aerolab-border rounded px-1 py-1 font-mono text-center bg-white text-xs"
                                  />
                                ))}
                              </div>
                            </div>
                          </div>
                        )}

                        {seg.type === "lemniscate" && (
                          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Semieje a (m)</label>
                              <input
                                type="number"
                                step="0.1"
                                value={seg.params?.a ?? 2.0}
                                onChange={(e) => updateSegmentParam(idx, "a", parseFloat(e.target.value) || 2.0)}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Semieje b (m)</label>
                              <input
                                type="number"
                                step="0.1"
                                value={seg.params?.b ?? 1.0}
                                onChange={(e) => updateSegmentParam(idx, "b", parseFloat(e.target.value) || 1.0)}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Velocidad ω</label>
                              <input
                                type="number"
                                step="0.05"
                                value={seg.params?.omega_rad_s ?? 0.35}
                                onChange={(e) => updateSegmentParam(idx, "omega_rad_s", parseFloat(e.target.value) || 0.35)}
                                className="w-full border border-aerolab-border rounded px-2 py-1 font-mono text-center bg-white"
                              />
                            </div>
                            <div className="col-span-2">
                              <label className="text-[11px] text-aerolab-secondary block mb-0.5">Centro [X, Y, Z] (m)</label>
                              <div className="grid grid-cols-3 gap-1">
                                {[0, 1, 2].map((axisIdx) => (
                                  <input
                                    key={axisIdx}
                                    type="number"
                                    step="0.1"
                                    value={seg.params?.center_W_m?.[axisIdx] ?? (axisIdx === 2 ? 2.0 : 0.0)}
                                    onChange={(e) => {
                                      const val = parseFloat(e.target.value) || 0.0;
                                      const c = [...(seg.params?.center_W_m || [0, 0, 2.0])];
                                      c[axisIdx] = val;
                                      updateSegmentParam(idx, "center_W_m", c);
                                    }}
                                    placeholder={["X", "Y", "Z"][axisIdx]}
                                    title={["Centro X (m)", "Centro Y (m)", "Centro Z (m)"][axisIdx]}
                                    className="w-full border border-aerolab-border rounded px-1 py-1 font-mono text-center bg-white text-xs"
                                  />
                                ))}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}

              {(missionConfig.segments?.length || 0) < 4 && (
                <button
                  onClick={() => {
                    const newSegs = [...(missionConfig.segments || [])];
                    newSegs.push({
                      type: "circle",
                      duration: 8.0,
                      params: presets?.initial_variants?.circle || { radius_m: 1.5, omega_rad_s: 0.6 },
                    });
                    setMissionConfig({ ...missionConfig, segments: newSegs });
                  }}
                  className="flex items-center justify-center gap-1.5 text-xs text-aerolab-action font-medium py-1.5 border border-dashed border-aerolab-border rounded-lg hover:bg-aerolab-canvas"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Añadir tramo a la composición</span>
                </button>
              )}
            </div>
          )}

          {/* Perturbation: Wind */}
          <div className="border-t border-aerolab-border pt-4 mt-2 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <Wind className="w-4 h-4 text-aerolab-action" />
              <span className="text-xs font-semibold text-aerolab-text">
                Condiciones de Viento Horizontal
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-aerolab-canvas/60 p-3 rounded-lg border border-aerolab-border flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-aerolab-secondary">Velocidad</span>
                  <span className="text-xs font-mono font-semibold text-aerolab-text">
                    {missionConfig.wind.magnitude_m_s.toFixed(1)} m/s
                  </span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="1.4"
                  step="0.1"
                  value={missionConfig.wind.magnitude_m_s}
                  onChange={(e) => {
                    const mag = parseFloat(e.target.value) || 0.0;
                    setMissionConfig({
                      ...missionConfig,
                      wind: { ...missionConfig.wind, magnitude_m_s: mag },
                    });
                  }}
                  className="w-full cursor-pointer accent-aerolab-action"
                />
              </div>

              <div className="bg-aerolab-canvas/60 p-3 rounded-lg border border-aerolab-border flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-aerolab-secondary">Dirección</span>
                  <span className="text-xs font-mono font-semibold text-aerolab-text">
                    {missionConfig.wind.direction_deg}°
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="360"
                  step="15"
                  value={missionConfig.wind.direction_deg}
                  onChange={(e) => {
                    const dir = parseFloat(e.target.value) || 0;
                    setMissionConfig({
                      ...missionConfig,
                      wind: { ...missionConfig.wind, direction_deg: dir },
                    });
                  }}
                  className="w-full cursor-pointer accent-aerolab-action"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Validation Feedback Banner (Shown ONLY on invalid configuration) */}
        {validation && !validation.valid && (
          <div className="p-3.5 rounded-xl border flex items-start gap-3 text-xs bg-red-50/80 border-red-200 text-red-900">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="font-semibold mb-0.5">
                Revisión requerida antes de simular
              </div>
              <ul className="list-disc pl-4 space-y-1 text-red-800">
                {validation.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Action Button */}
        <div>
          <button
            onClick={handleExecute}
            disabled={!validation?.valid || isSimulating}
            className={`w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-semibold text-sm shadow-xs transition-all ${validation?.valid && !isSimulating
                ? "bg-aerolab-action text-white hover:bg-aerolab-action/90 cursor-pointer"
                : "bg-aerolab-border text-aerolab-secondary cursor-not-allowed"
              }`}
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{isSimulating ? "Iniciando corrida..." : "Ejecutar Misión"}</span>
          </button>
        </div>
      </div>

      {/* RIGHT COLUMN: 3D Previsualization (5 Cols) */}
      <div className="lg:col-span-5 flex flex-col gap-4">
        <div className="bg-white p-4 rounded-xl border border-aerolab-border shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-aerolab-text flex items-center gap-2">
                <Layers className="w-4 h-4 text-aerolab-action" />
                <span>Previsualización de Trayectoria</span>
              </h3>
              {loadingPreview && (
                <span className="text-xs text-aerolab-secondary animate-pulse font-normal">
                  (Calculando...)
                </span>
              )}
            </div>
          </div>

          {/* 3D Visor */}
          <TrajectoryViewer3D
            nominalPath={preview?.points || []}
            isTransitionFlags={preview?.is_transition || []}
            initialPosition={preview?.initial_position}
            accessibilitySummary={
              preview
                ? `Punto inicial: [${preview.initial_position.map((c) => c.toFixed(2)).join(", ")}] m • Cotas Z: [${preview.bounds.min_z.toFixed(2)}, ${preview.bounds.max_z.toFixed(2)}] m`
                : ""
            }
            className="w-full h-[360px]"
          />

          {/* Legend & Guidance */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-aerolab-secondary pt-1 border-t border-aerolab-border">
            <div className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 bg-aerolab-text rounded" />
              <span>Ruta nominal</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3.5 h-0.5 border-b border-dashed border-aerolab-secondary" />
              <span>Transición auto</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-aerolab-text" />
              <span>Punto de inicio</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
