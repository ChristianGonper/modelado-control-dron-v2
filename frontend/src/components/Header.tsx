import React from "react";
import { Compass, Layers, BarChart3 } from "lucide-react";
import { HealthResponse } from "../types";

export interface HeaderProps {
  currentView: "mission" | "comparison" | "analysis";
  onViewChange: (view: "mission" | "comparison" | "analysis") => void;
  health?: HealthResponse | null;
  hasResults: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onViewChange,
  hasResults,
}) => {
  return (
    <header className="bg-white border-b border-aerolab-border px-6 py-3.5 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Brand & App Title */}
        <div className="flex items-center gap-3">
          <svg className="w-10 h-10 shrink-0 shadow-xs" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="droneGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                <stop stopColor="#0284C7" />
                <stop offset="1" stopColor="#0F172A" />
              </linearGradient>
            </defs>
            <rect width="40" height="40" rx="10" fill="url(#droneGrad)" />
            {/* Carbon Frame / Diagonal Arms */}
            <path d="M12 12L28 28M28 12L12 28" stroke="#FFFFFF" strokeWidth="2.2" strokeLinecap="round" strokeOpacity="0.9" />
            {/* 4 Rotors with spinning ring effect */}
            <circle cx="11" cy="11" r="3.2" stroke="#38BDF8" strokeWidth="1.6" fill="none" strokeDasharray="3 2" />
            <circle cx="29" cy="11" r="3.2" stroke="#38BDF8" strokeWidth="1.6" fill="none" strokeDasharray="3 2" />
            <circle cx="11" cy="29" r="3.2" stroke="#38BDF8" strokeWidth="1.6" fill="none" strokeDasharray="3 2" />
            <circle cx="29" cy="29" r="3.2" stroke="#38BDF8" strokeWidth="1.6" fill="none" strokeDasharray="3 2" />
            {/* Center Avionics Hub */}
            <circle cx="20" cy="20" r="4.2" fill="#FFFFFF" />
            <circle cx="20" cy="20" r="2.2" fill="#0284C7" />
            {/* Forward heading arrow */}
            <path d="M20 13L21.8 16.5H18.2L20 13Z" fill="#38BDF8" />
          </svg>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-aerolab-text tracking-tight">NeuroFlight</h1>
              <span className="text-xs bg-aerolab-canvas text-aerolab-secondary px-2 py-0.5 rounded border border-aerolab-border font-medium">
                AeroLab
              </span>
            </div>
            <p className="text-xs text-aerolab-secondary">
              Control de cuadricópteros • Comparativa clásica vs. neuronal
            </p>
          </div>
        </div>

        {/* View Navigation */}
        <nav className="flex items-center gap-1 bg-aerolab-canvas p-1 rounded-xl border border-aerolab-border" aria-label="Navegación principal">
          <button
            onClick={() => onViewChange("mission")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              currentView === "mission"
                ? "bg-white text-aerolab-action shadow-xs font-semibold"
                : "text-aerolab-secondary hover:text-aerolab-text"
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>1. Misión</span>
          </button>

          <button
            onClick={() => onViewChange("comparison")}
            disabled={!hasResults}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              currentView === "comparison"
                ? "bg-white text-aerolab-action shadow-xs font-semibold"
                : hasResults
                ? "text-aerolab-secondary hover:text-aerolab-text cursor-pointer"
                : "text-aerolab-secondary/40 cursor-not-allowed"
            }`}
            title={!hasResults ? "Ejecuta una misión para ver la comparación" : ""}
          >
            <Layers className="w-4 h-4" />
            <span>2. Comparación</span>
          </button>

          <button
            onClick={() => onViewChange("analysis")}
            disabled={!hasResults}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              currentView === "analysis"
                ? "bg-white text-aerolab-action shadow-xs font-semibold"
                : hasResults
                ? "text-aerolab-secondary hover:text-aerolab-text cursor-pointer"
                : "text-aerolab-secondary/40 cursor-not-allowed"
            }`}
            title={!hasResults ? "Ejecuta una misión para ver el análisis" : ""}
          >
            <BarChart3 className="w-4 h-4" />
            <span>3. Análisis</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
