import React, { useRef, useState } from "react";
import { TelemetrySeriesResponse } from "../types";

export interface TelemetryChartProps {
  telemetryData: Record<string, TelemetrySeriesResponse>;
  selectedSignals: string[];
  visibleControllers?: Record<string, boolean>;
  currentTime: number;
  onTimeChange?: (newTime: number) => void;
}

const CONTROLLER_STYLE: Record<
  string,
  { name: string; color: string; dashArray?: string; styleLabel: string }
> = {
  classic: { name: "PD", color: "#0284C7", styleLabel: "continua" },
  mlp: { name: "MLP", color: "#10B981", styleLabel: "continua" },
  gru: { name: "GRU", color: "#F59E0B", dashArray: "5 3", styleLabel: "trazos" },
  lstm: { name: "LSTM", color: "#8B5CF6", dashArray: "2 2", styleLabel: "puntos" },
};

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  telemetryData,
  selectedSignals,
  visibleControllers = { classic: true, mlp: true, gru: true, lstm: true },
  currentTime,
  onTimeChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverTime, setHoverTime] = useState<number | null>(null);
  const [isMouseDown, setIsMouseDown] = useState(false);

  // SVG coordinate dimensions
  const svgW = 800;
  const svgH = 170;
  const padL = 55;
  const padR = 25;
  const padT = 20;
  const padB = 30;
  const plotW = svgW - padL - padR;
  const plotH = svgH - padT - padB;

  // Determine maximum time across ALL loaded controller series
  let maxTime = 0;
  Object.values(telemetryData).forEach((data) => {
    if (data?.time_s && data.time_s.length > 0) {
      const last = data.time_s[data.time_s.length - 1];
      if (last > maxTime) maxTime = last;
    }
  });
  if (maxTime <= 0) maxTime = 10;

  // Display time: hover takes precedence if hovering
  const activeDisplayTime = hoverTime !== null ? hoverTime : currentTime;
  const firstTelem = Object.values(telemetryData)[0];

  // Accurately convert screen client coordinates to SVG plot time
  const getTimeFromEvent = (e: React.MouseEvent<SVGSVGElement>): number | null => {
    if (maxTime <= 0) return null;
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width <= 0) return null;

    // Convert screen pixel X to SVG viewBox X coordinate (0 to 800)
    const svgX = ((e.clientX - rect.left) / rect.width) * svgW;
    const clampedX = Math.max(padL, Math.min(svgW - padR, svgX));
    const targetT = ((clampedX - padL) / plotW) * maxTime;
    return Math.max(0, Math.min(maxTime, targetT));
  };

  const getTimeFromTouch = (e: React.TouchEvent<SVGSVGElement>): number | null => {
    if (maxTime <= 0 || e.touches.length === 0) return null;
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width <= 0) return null;

    const svgX = ((e.touches[0].clientX - rect.left) / rect.width) * svgW;
    const clampedX = Math.max(padL, Math.min(svgW - padR, svgX));
    const targetT = ((clampedX - padL) / plotW) * maxTime;
    return Math.max(0, Math.min(maxTime, targetT));
  };

  const handleChartClick = (e: React.MouseEvent<SVGSVGElement>) => {
    const t = getTimeFromEvent(e);
    if (t !== null && onTimeChange) {
      onTimeChange(t);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    setIsMouseDown(true);
    const t = getTimeFromEvent(e);
    if (t !== null && onTimeChange) {
      onTimeChange(t);
    }
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const t = getTimeFromEvent(e);
    setHoverTime(t);
    if (isMouseDown && t !== null && onTimeChange) {
      onTimeChange(t);
    }
  };

  const handleMouseLeave = () => {
    setHoverTime(null);
    setIsMouseDown(false);
  };

  const handleMouseUp = () => {
    setIsMouseDown(false);
  };

  const handleTouchStart = (e: React.TouchEvent<SVGSVGElement>) => {
    const t = getTimeFromTouch(e);
    if (t !== null && onTimeChange) {
      onTimeChange(t);
    }
  };

  const handleTouchMove = (e: React.TouchEvent<SVGSVGElement>) => {
    const t = getTimeFromTouch(e);
    if (t !== null && onTimeChange) {
      onTimeChange(t);
    }
  };

  if (!firstTelem || selectedSignals.length === 0) {
    return (
      <div className="p-8 text-center bg-aerolab-canvas rounded-xl border border-aerolab-border text-xs text-aerolab-secondary">
        Selecciona al menos una señal de la lista inferior para renderizar sus curvas temporales.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4" onMouseUp={handleMouseUp}>
      {selectedSignals.map((sigKey) => {
        const unit = firstTelem.units[sigKey] || "";
        const group = firstTelem.groups[sigKey] || "";

        // Find min and max across all active controllers for this signal
        let yMin = Infinity;
        let yMax = -Infinity;

        Object.entries(telemetryData).forEach(([cid, data]) => {
          if (!visibleControllers[cid]) return;
          const series = data.signals[sigKey];
          if (!series || series.length === 0) return;
          for (let i = 0; i < series.length; i++) {
            const v = series[i];
            if (typeof v === "number" && !isNaN(v)) {
              if (v < yMin) yMin = v;
              if (v > yMax) yMax = v;
            }
          }
        });

        if (yMin === Infinity || yMax === -Infinity) {
          yMin = 0;
          yMax = 1;
        }

        // Add 12% vertical padding
        const span = yMax - yMin;
        const pad = span === 0 ? 0.5 : span * 0.12;
        const adjustedMin = yMin - pad;
        const adjustedMax = yMax + pad;
        const totalSpan = adjustedMax - adjustedMin || 1.0;

        const scaleX = (t: number) => padL + (t / maxTime) * plotW;
        const scaleY = (val: number) => padT + plotH - ((val - adjustedMin) / totalSpan) * plotH;

        // Current permanent time cursor position
        const cursorX = scaleX(Math.min(maxTime, currentTime));

        // Hover time cursor position
        const hoverX = hoverTime !== null ? scaleX(Math.min(maxTime, hoverTime)) : null;

        // Generate SVG path points and fetch instant values
        const paths: Record<string, string> = {};
        const displayedVals: Record<string, number | null> = {};
        const fixedVals: Record<string, number | null> = {};

        Object.entries(telemetryData).forEach(([cid, data]) => {
          if (!visibleControllers[cid]) return;
          const series = data.signals[sigKey];
          const tList = data.time_s;
          if (!series || !tList || series.length < 2) return;

          // Find sample closest to activeDisplayTime for this controller
          let cActiveIdx = 0;
          for (let i = 0; i < tList.length; i++) {
            if (tList[i] <= activeDisplayTime) {
              cActiveIdx = i;
            } else {
              break;
            }
          }
          displayedVals[cid] = series[cActiveIdx] ?? null;

          // Find sample closest to fixed currentTime for this controller
          let cFixedIdx = 0;
          for (let i = 0; i < tList.length; i++) {
            if (tList[i] <= currentTime) {
              cFixedIdx = i;
            } else {
              break;
            }
          }
          fixedVals[cid] = series[cFixedIdx] ?? null;

          // Downsample for crisp SVG rendering if high density (> 400 pts)
          const step = Math.max(1, Math.floor(series.length / 400));
          let d = "";
          for (let i = 0; i < series.length; i += step) {
            const val = series[i];
            if (val === null || val === undefined) continue;
            const px = scaleX(tList[i]);
            const py = scaleY(val);
            d += d.length === 0 ? `M ${px.toFixed(1)} ${py.toFixed(1)}` : ` L ${px.toFixed(1)} ${py.toFixed(1)}`;
          }
          const lastI = series.length - 1;
          const lastVal = series[lastI];
          if (lastVal !== null && lastVal !== undefined) {
            d += ` L ${scaleX(tList[lastI]).toFixed(1)} ${scaleY(lastVal).toFixed(1)}`;
          }
          paths[cid] = d;
        });

        // 3 Y-axis ticks
        const yTicks = [adjustedMin + pad, (adjustedMin + adjustedMax) / 2, adjustedMax - pad];

        return (
          <div
            key={sigKey}
            className="bg-white p-4 rounded-xl border border-aerolab-border shadow-xs flex flex-col gap-2 transition-all hover:border-aerolab-border/80"
          >
            {/* Header: Signal Name, Unit, and Instant Values */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-aerolab-border/60 pb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-aerolab-text font-mono">{sigKey}</span>
                {unit && (
                  <span className="text-xs bg-aerolab-canvas text-aerolab-secondary px-2 py-0.5 rounded font-mono border border-aerolab-border">
                    {unit}
                  </span>
                )}
                <span className="text-xs text-aerolab-secondary">({group})</span>
                <span className="text-xs bg-sky-50 text-aerolab-action font-mono px-2 py-0.5 rounded font-semibold border border-sky-200">
                  t = {activeDisplayTime.toFixed(2)} s
                </span>
              </div>

              {/* Instant values badge for each visible controller - larger & clearer */}
              <div className="flex flex-wrap items-center gap-2">
                {Object.entries(CONTROLLER_STYLE).map(([cid, meta]) => {
                  if (!visibleControllers[cid]) return null;
                  const v = displayedVals[cid];
                  return (
                    <div
                      key={cid}
                      className="flex items-center gap-1.5 bg-aerolab-canvas px-2.5 py-1 rounded-lg border border-aerolab-border/80 shadow-2xs"
                    >
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: meta.color }} />
                      <span className="font-sans text-xs text-aerolab-secondary font-medium">{meta.name}:</span>
                      <span className="text-sm font-mono font-bold tabular-nums text-aerolab-text">
                        {v !== null && v !== undefined ? v.toFixed(3) : "—"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Interactive SVG Chart */}
            <div className="w-full overflow-hidden" ref={containerRef}>
              <svg
                viewBox={`0 0 ${svgW} ${svgH}`}
                role="img"
                aria-label={`Gráfica temporal de la señal ${sigKey} (${unit || "adimensional"})`}
                className="w-full h-auto cursor-crosshair select-none touch-none"
                onClick={handleChartClick}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
              >
                {/* Horizontal Gridlines & Y-labels */}
                {yTicks.map((yVal, i) => {
                  const yPos = scaleY(yVal);
                  return (
                    <g key={i}>
                      <line
                        x1={padL}
                        y1={yPos}
                        x2={svgW - padR}
                        y2={yPos}
                        stroke="#E2E8F0"
                        strokeDasharray="4 4"
                      />
                      <text
                        x={padL - 8}
                        y={yPos + 4}
                        textAnchor="end"
                        className="text-[10px] fill-slate-400 font-mono"
                      >
                        {yVal.toFixed(2)}
                      </text>
                    </g>
                  );
                })}

                {/* X-Axis base line */}
                <line
                  x1={padL}
                  y1={svgH - padB}
                  x2={svgW - padR}
                  y2={svgH - padB}
                  stroke="#CBD5E1"
                  strokeWidth="1.5"
                />

                {/* X-Axis Ticks (every 25% of duration) */}
                {[0, 0.25, 0.5, 0.75, 1.0].map((frac) => {
                  const t = frac * maxTime;
                  const x = scaleX(t);
                  return (
                    <g key={frac}>
                      <line x1={x} y1={svgH - padB} x2={x} y2={svgH - padB + 5} stroke="#94A3B8" />
                      <text
                        x={x}
                        y={svgH - padB + 16}
                        textAnchor="middle"
                        className="text-[10px] fill-slate-500 font-mono"
                      >
                        {t.toFixed(1)}s
                      </text>
                    </g>
                  );
                })}

                {/* Plotted Controller Curves */}
                {Object.entries(paths).map(([cid, d]) => {
                  const meta = CONTROLLER_STYLE[cid];
                  if (!meta) return null;
                  return (
                    <path
                      key={cid}
                      d={d}
                      fill="none"
                      stroke={meta.color}
                      strokeWidth="2.2"
                      strokeDasharray={meta.dashArray}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  );
                })}

                {/* Permanent Time Cursor Vertical Line */}
                <line
                  x1={cursorX}
                  y1={padT}
                  x2={cursorX}
                  y2={svgH - padB}
                  stroke="#0F172A"
                  strokeWidth="1.8"
                  strokeDasharray="2 2"
                />

                {/* Permanent Cursor Intersection Points on each curve */}
                {Object.entries(fixedVals).map(([cid, val]) => {
                  if (val === null || val === undefined || !visibleControllers[cid]) return null;
                  const cy = scaleY(val);
                  const color = CONTROLLER_STYLE[cid]?.color || "#0284C7";
                  return (
                    <circle
                      key={cid}
                      cx={cursorX}
                      cy={cy}
                      r="4"
                      fill={color}
                      stroke="#FFFFFF"
                      strokeWidth="1.5"
                      className="transition-all duration-75"
                    />
                  );
                })}

                {/* Hover Guide Line, Data Value Badges & X-Axis Timestamp */}
                {hoverX !== null && hoverTime !== null && (
                  <g className="pointer-events-none">
                    <line
                      x1={hoverX}
                      y1={padT}
                      x2={hoverX}
                      y2={svgH - padB}
                      stroke="#0284C7"
                      strokeWidth="1.5"
                      strokeDasharray="3 3"
                    />

                    {/* Data values displayed near the point on each curve */}
                    {Object.entries(displayedVals).map(([cid, val]) => {
                      if (val === null || val === undefined || !visibleControllers[cid]) return null;
                      const cy = scaleY(val);
                      const meta = CONTROLLER_STYLE[cid];
                      const color = meta?.color || "#0284C7";
                      const valStr = Number(val).toFixed(2);
                      const pillW = valStr.length * 6.5 + 12;
                      const pillX = hoverX + 8 + pillW > svgW - padR ? hoverX - 8 - pillW : hoverX + 8;
                      const pillY = Math.max(padT, Math.min(svgH - padB - 16, cy - 8));

                      return (
                        <g key={`hover-val-${cid}`}>
                          <circle
                            cx={hoverX}
                            cy={cy}
                            r="4"
                            fill="#FFFFFF"
                            stroke={color}
                            strokeWidth="2.5"
                          />
                          <rect
                            x={pillX}
                            y={pillY}
                            width={pillW}
                            height={16}
                            rx={3}
                            fill={color}
                            opacity={0.92}
                          />
                          <text
                            x={pillX + pillW / 2}
                            y={pillY + 11}
                            textAnchor="middle"
                            className="text-[9px] fill-white font-mono font-bold"
                          >
                            {valStr}
                          </text>
                        </g>
                      );
                    })}

                    {/* Timestamp badge positioned on the X-axis */}
                    <rect
                      x={Math.max(padL, Math.min(svgW - padR - 48, hoverX - 24))}
                      y={svgH - padB + 2}
                      width={48}
                      height={16}
                      rx={4}
                      fill="#0F172A"
                    />
                    <text
                      x={Math.max(padL + 24, Math.min(svgW - padR - 24, hoverX))}
                      y={svgH - padB + 13}
                      textAnchor="middle"
                      className="text-[9px] fill-white font-mono font-bold"
                    >
                      {hoverTime.toFixed(2)}s
                    </text>
                  </g>
                )}
              </svg>
            </div>
          </div>
        );
      })}
    </div>
  );
};
