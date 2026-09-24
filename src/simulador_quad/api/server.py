"""
FastAPI application and REST endpoints for NeuroFlight.
"""

import csv
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import torch
import uvicorn

from simulador_quad.api.bundle_verifier import BundleVerifier
from simulador_quad.api.envelope import validate_mission_envelope
from simulador_quad.api.models import (
    MissionConfigRequest,
    PreviewResponse,
    RunResultsResponse,
    RunStatusResponse,
    ValidationResponse,
)
from simulador_quad.api.pid_selection import select_pid_for_mission
from simulador_quad.api.presets import (
    generate_initial_variant,
    get_composite_presets,
    get_waypoint_presets,
)
from simulador_quad.api.runner_service import RunnerService
from simulador_quad.api.scenario_builder import compute_preview

app = FastAPI(
    title="NeuroFlight API",
    description="Backend API for quadcopter control simulation and neural comparison (AeroLab).",
    version="1.0.0",
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

runner_service = RunnerService()
bundle_verifier = BundleVerifier()


def _finite_number(value: Any, ndigits: int) -> Optional[float]:
    """Convierte un escalar finito. Una ausencia o un valor no numérico no se vuelve cero."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return round(number, ndigits)


def _vector_at(container: Any, key: str, size: int) -> Optional[List[Any]]:
    if not isinstance(container, dict) or key not in container:
        return None
    value = container.get(key)
    if not isinstance(value, (list, tuple)) or len(value) < size:
        return None
    return list(value)


def _component(vector: Optional[List[Any]], index: int, ndigits: int) -> Optional[float]:
    if vector is None or index >= len(vector):
        return None
    return _finite_number(vector[index], ndigits)


def series_from_samples(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Series de telemetría. Cada campo ausente queda en null, nunca como medida cero."""
    times: List[Optional[float]] = []
    signals: Dict[str, List[Optional[float]]] = {
        "pos_x_m": [], "pos_y_m": [], "pos_z_m": [],
        "ref_x_m": [], "ref_y_m": [], "ref_z_m": [],
        "pos_err_m": [],
        "vel_x_m_s": [], "vel_y_m_s": [], "vel_z_m_s": [],
        "thrust_N": [],
        "moment_x_Nm": [], "moment_y_Nm": [], "moment_z_Nm": [],
        "desired_fx_N": [], "desired_fy_N": [], "desired_fz_N": [],
        "desired_clipped_fx_N": [], "desired_clipped_fy_N": [], "desired_clipped_fz_N": [],
        "rotor_0_rpm": [], "rotor_1_rpm": [], "rotor_2_rpm": [], "rotor_3_rpm": [],
        "wind_x_m_s": [], "wind_y_m_s": [], "wind_z_m_s": [],
        "is_saturated": [],
    }

    for sample in samples:
        if not isinstance(sample, dict):
            sample = {}
        times.append(_finite_number(sample.get("time_s"), 3) if "time_s" in sample else None)

        state = sample.get("state") if isinstance(sample.get("state"), dict) else {}
        reference = sample.get("reference") if isinstance(sample.get("reference"), dict) else {}
        control = sample.get("control") if isinstance(sample.get("control"), dict) else {}
        rotors = sample.get("rotors") if isinstance(sample.get("rotors"), dict) else {}
        perturbation = sample.get("perturbation") if isinstance(sample.get("perturbation"), dict) else {}

        pos = _vector_at(state, "position_W_m", 3)
        vel = _vector_at(state, "velocity_W_m_s", 3)
        ref = _vector_at(reference, "position_W_m", 3)
        moments = _vector_at(control, "body_moments_Nm", 3)
        rpms = _vector_at(rotors, "rotor_speed_rpm", 4)
        flags = _vector_at(rotors, "saturation_flags", 1)
        wind = _vector_at(perturbation, "wind_W_m_s", 3)

        for index, key in enumerate(("pos_x_m", "pos_y_m", "pos_z_m")):
            signals[key].append(_component(pos, index, 3))
        for index, key in enumerate(("ref_x_m", "ref_y_m", "ref_z_m")):
            signals[key].append(_component(ref, index, 3))
        for index, key in enumerate(("vel_x_m_s", "vel_y_m_s", "vel_z_m_s")):
            signals[key].append(_component(vel, index, 3))

        if pos is not None and ref is not None:
            pos_nums = [_finite_number(item, 6) for item in pos]
            ref_nums = [_finite_number(item, 6) for item in ref]
            if all(item is not None for item in pos_nums + ref_nums):
                err = float(np.linalg.norm(np.array(pos_nums, dtype=float) - np.array(ref_nums, dtype=float)))
                signals["pos_err_m"].append(round(err, 4))
            else:
                signals["pos_err_m"].append(None)
        else:
            signals["pos_err_m"].append(None)

        thrust = _finite_number(control.get("collective_thrust_N"), 3) if "collective_thrust_N" in control else None
        signals["thrust_N"].append(thrust)
        for index, key in enumerate(("moment_x_Nm", "moment_y_Nm", "moment_z_Nm")):
            signals[key].append(_component(moments, index, 4))

        desired = sample.get("desired_force_W_N") if "desired_force_W_N" in sample else None
        desired_vec = desired if isinstance(desired, (list, tuple)) and len(desired) >= 3 else None
        clipped = sample.get("desired_force_clipped_W_N") if "desired_force_clipped_W_N" in sample else None
        clipped_vec = clipped if isinstance(clipped, (list, tuple)) and len(clipped) >= 3 else None
        for index, key in enumerate(("desired_fx_N", "desired_fy_N", "desired_fz_N")):
            signals[key].append(_component(desired_vec, index, 3))
        for index, key in enumerate(("desired_clipped_fx_N", "desired_clipped_fy_N", "desired_clipped_fz_N")):
            signals[key].append(_component(clipped_vec, index, 3))

        for index in range(4):
            signals[f"rotor_{index}_rpm"].append(_component(rpms, index, 1))
        for index, key in enumerate(("wind_x_m_s", "wind_y_m_s", "wind_z_m_s")):
            signals[key].append(_component(wind, index, 3))

        if flags is None:
            signals["is_saturated"].append(None)
        else:
            signals["is_saturated"].append(1.0 if any(bool(flag) for flag in flags) else 0.0)

    return {"time_s": times, "signals": signals}


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Estado del servicio, verificación del bundle de modelos y aceleración."""
    bundle_status = bundle_verifier.verify()
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"

    return {
        "status": "ok" if bundle_status.get("valid") else "degraded",
        "app": "NeuroFlight",
        "team": "AeroLab",
        "device": device_name,
        "cuda_available": cuda_available,
        "bundle": bundle_status,
    }


@app.get("/api/presets")
def get_presets(seed: int = 42) -> Dict[str, Any]:
    """Catálogo de variantes iniciales y presets para misiones simples y compuestas."""
    return {
        "initial_variants": {
            "hold": generate_initial_variant("hold", seed),
            "circle": generate_initial_variant("circle", seed),
            "lissajous": generate_initial_variant("lissajous", seed),
            "waypoint": generate_initial_variant("waypoint", seed),
            "lemniscate": generate_initial_variant("lemniscate", seed),
        },
        "waypoint_presets": get_waypoint_presets(),
        "composite_presets": get_composite_presets(),
    }


@app.post("/api/mission/validate", response_model=ValidationResponse)
def validate_mission(mission: MissionConfigRequest) -> ValidationResponse:
    """Valida los parámetros de una misión contra la envolvente física y de producto."""
    is_valid, errors, warnings, init_pos = validate_mission_envelope(mission)

    pid_fam, pid_exp = None, None
    if is_valid or len(errors) == 0:
        pid_fam, pid_exp, _ = select_pid_for_mission(
            mission.mode, mission.family.value, mission.params, mission.segments
        )

    return ValidationResponse(
        valid=is_valid,
        errors=errors,
        warnings=warnings,
        initial_position=init_pos,
        selected_pid_family=pid_fam,
        selected_pid_explanation=pid_exp,
    )


@app.post("/api/mission/preview", response_model=PreviewResponse)
def preview_mission(mission: MissionConfigRequest) -> PreviewResponse:
    """Muestrea la ruta nominal 3D, punto de inicio y transiciones para la previsualización."""
    is_valid, errors, _, _ = validate_mission_envelope(mission)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": errors})

    try:
        return compute_preview(mission)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error generando previsualización: {exc}")


@app.post("/api/simulation/run")
def run_simulation(mission: MissionConfigRequest) -> Dict[str, str]:
    """Lanza la simulación comparativa de los cuatro controladores (PD, MLP, GRU, LSTM)."""
    is_valid, errors, _, _ = validate_mission_envelope(mission)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": errors})

    run_id = runner_service.start_simulation(mission)
    return {"run_id": run_id, "state": "preparing"}


@app.get("/api/simulation/{run_id}/status", response_model=RunStatusResponse)
def get_simulation_status(run_id: str) -> RunStatusResponse:
    """Consulta el progreso en tiempo real de cada controlador."""
    status = runner_service.get_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Ejecución '{run_id}' no encontrada.")
    return status


@app.get("/api/simulation/{run_id}/results", response_model=RunResultsResponse)
def get_simulation_results(run_id: str) -> RunResultsResponse:
    """Devuelve las métricas consolidadas y las trayectorias para la comparación y reproducción."""
    results = runner_service.get_results(run_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"Resultados de '{run_id}' no disponibles aún.")
    return results


@app.get("/api/simulation/{run_id}/telemetry/{controller_id}")
def get_controller_telemetry(run_id: str, controller_id: str) -> Dict[str, Any]:
    """Devuelve las series de telemetría completa para análisis y gráficas."""
    telem_file = runner_service.runs_dir / run_id / f"telemetry_{controller_id}.json"
    if not telem_file.exists():
        raise HTTPException(status_code=404, detail=f"Telemetría para '{controller_id}' no encontrada.")

    with open(telem_file, "r", encoding="utf-8") as f:
        samples = json.load(f)

    extracted = series_from_samples(samples)
    times = extracted["time_s"]
    signals = extracted["signals"]

    units = {
        "pos_x_m": "m", "pos_y_m": "m", "pos_z_m": "m",
        "ref_x_m": "m", "ref_y_m": "m", "ref_z_m": "m",
        "pos_err_m": "m",
        "vel_x_m_s": "m/s", "vel_y_m_s": "m/s", "vel_z_m_s": "m/s",
        "thrust_N": "N",
        "moment_x_Nm": "N·m", "moment_y_Nm": "N·m", "moment_z_Nm": "N·m",
        "desired_fx_N": "N", "desired_fy_N": "N", "desired_fz_N": "N",
        "desired_clipped_fx_N": "N", "desired_clipped_fy_N": "N", "desired_clipped_fz_N": "N",
        "rotor_0_rpm": "RPM", "rotor_1_rpm": "RPM", "rotor_2_rpm": "RPM", "rotor_3_rpm": "RPM",
        "wind_x_m_s": "m/s", "wind_y_m_s": "m/s", "wind_z_m_s": "m/s",
        "is_saturated": "booleano",
    }

    groups = {
        "pos_x_m": "Posición y Referencia", "pos_y_m": "Posición y Referencia", "pos_z_m": "Posición y Referencia",
        "ref_x_m": "Posición y Referencia", "ref_y_m": "Posición y Referencia", "ref_z_m": "Posición y Referencia",
        "pos_err_m": "Posición y Referencia",
        "vel_x_m_s": "Velocidad", "vel_y_m_s": "Velocidad", "vel_z_m_s": "Velocidad",
        "thrust_N": "Comandos de Control",
        "moment_x_Nm": "Comandos de Control", "moment_y_Nm": "Comandos de Control", "moment_z_Nm": "Comandos de Control",
        "desired_fx_N": "Fuerza Deseada Neuronal", "desired_fy_N": "Fuerza Deseada Neuronal", "desired_fz_N": "Fuerza Deseada Neuronal",
        "desired_clipped_fx_N": "Fuerza Deseada Neuronal", "desired_clipped_fy_N": "Fuerza Deseada Neuronal", "desired_clipped_fz_N": "Fuerza Deseada Neuronal",
        "rotor_0_rpm": "Rotores y Actuadores", "rotor_1_rpm": "Rotores y Actuadores", "rotor_2_rpm": "Rotores y Actuadores", "rotor_3_rpm": "Rotores y Actuadores",
        "wind_x_m_s": "Perturbaciones", "wind_y_m_s": "Perturbaciones", "wind_z_m_s": "Perturbaciones",
        "is_saturated": "Protecciones y Límites",
    }

    return {
        "run_id": run_id,
        "controller_id": controller_id,
        "time_s": times,
        "signals": signals,
        "units": units,
        "groups": groups,
    }


@app.get("/api/simulation/{run_id}/export/{export_format}")
def export_simulation_data(run_id: str, export_format: str = "json") -> Response:
    """Exporta las muestras y metadatos de la ejecución en JSON o CSV."""
    run_dir = runner_service.runs_dir / run_id
    manifest_file = run_dir / "run_manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail=f"Ejecución '{run_id}' no encontrada.")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    if export_format.lower() == "json":
        export_payload = {
            "metadata": manifest_data,
            "telemetry_files": {},
        }
        for cid in ["classic", "mlp", "gru", "lstm"]:
            t_path = run_dir / f"telemetry_{cid}.json"
            if t_path.exists():
                with open(t_path, "r", encoding="utf-8") as tf:
                    export_payload["telemetry_files"][cid] = json.load(tf)

        json_bytes = json.dumps(export_payload, indent=2).encode("utf-8")
        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="neuroflight_run_{run_id}.json"'},
        )

    elif export_format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "time_s", "controller_id", "pos_x_m", "pos_y_m", "pos_z_m",
            "ref_x_m", "ref_y_m", "ref_z_m", "pos_err_m",
            "vel_x_m_s", "vel_y_m_s", "vel_z_m_s", "thrust_N"
        ])

        for cid in ["classic", "mlp", "gru", "lstm"]:
            t_path = run_dir / f"telemetry_{cid}.json"
            if t_path.exists():
                with open(t_path, "r", encoding="utf-8") as tf:
                    samples = json.load(tf)
                extracted = series_from_samples(samples)
                rows = zip(
                    extracted["time_s"],
                    extracted["signals"]["pos_x_m"],
                    extracted["signals"]["pos_y_m"],
                    extracted["signals"]["pos_z_m"],
                    extracted["signals"]["ref_x_m"],
                    extracted["signals"]["ref_y_m"],
                    extracted["signals"]["ref_z_m"],
                    extracted["signals"]["pos_err_m"],
                    extracted["signals"]["vel_x_m_s"],
                    extracted["signals"]["vel_y_m_s"],
                    extracted["signals"]["vel_z_m_s"],
                    extracted["signals"]["thrust_N"],
                )
                for row in rows:
                    writer.writerow([
                        "" if row[0] is None else row[0],
                        cid,
                        *("" if value is None else value for value in row[1:]),
                    ])

        csv_bytes = output.getvalue().encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="neuroflight_run_{run_id}.csv"'},
        )

    raise HTTPException(status_code=400, detail="Formato de exportación no soportado. Use 'json' o 'csv'.")


# Serve frontend static assets if built
_possible_dist_paths = [
    Path("frontend/dist"),
    Path(__file__).resolve().parents[3] / "frontend" / "dist",
]
FRONTEND_DIST = next((p for p in _possible_dist_paths if p.exists()), None)
if FRONTEND_DIST is not None:
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")


def main():
    """CLI entrypoint para iniciar el servidor de NeuroFlight."""
    print("=" * 60)
    print("  Iniciando servidor NeuroFlight (AeroLab)")
    print("  Acceso web en: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("simulador_quad.api.server:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
