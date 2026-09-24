"""
Scenario builder and nominal trajectory sampler for NeuroFlight.
Constructs full declarative scenario dictionaries compliant with validate_scenario_config.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import yaml

from simulador_quad.api.bundle_verifier import BundleVerifier
from simulador_quad.api.envelope import (
    SIMPLE_DURATION_MAX_S,
    planned_duration_s,
    simulation_duration_s,
    validate_mission_envelope,
)
from simulador_quad.api.models import MissionConfigRequest, PreviewResponse
from simulador_quad.api.pid_selection import select_pid_for_mission
from simulador_quad.core.contracts import VehicleState
from simulador_quad.scenarios.loader import instantiate_trajectory
from simulador_quad.scenarios.schema import validate_scenario_config

# Standard vehicle parameters
BASE_VEHICLE = {
    "mass_kg": 1.0,
    "inertia_B_kg_m2": [[0.05, 0.0, 0.0], [0.0, 0.05, 0.0], [0.0, 0.0, 0.1]],
    "gravity_m_s2": 9.81,
    "rotor_template": {
        "k_f": 1.0e-4,
        "k_m": 1.0e-6,
        "omega_max_rad_s": 500.0,
        "time_constant_s": 0.03,
        "delay_s": 0.01,
    },
}

STANDARD_ROTORS = [
    {"position_B_m": [0.17, 0.17, 0.0], "turning_direction": -1, **BASE_VEHICLE["rotor_template"]},
    {"position_B_m": [0.17, -0.17, 0.0], "turning_direction": 1, **BASE_VEHICLE["rotor_template"]},
    {"position_B_m": [-0.17, 0.17, 0.0], "turning_direction": 1, **BASE_VEHICLE["rotor_template"]},
    {"position_B_m": [-0.17, -0.17, 0.0], "turning_direction": -1, **BASE_VEHICLE["rotor_template"]},
]


def build_trajectory_config(mission: MissionConfigRequest) -> Dict[str, Any]:
    """Genera la sección 'trajectory' de configuración declarativa del escenario."""
    if mission.mode == "simple":
        fam = mission.family.value
        t_cfg = {"type": fam, **mission.params}
        # Eliminar 'duration' en misiones simples ya que la duración la fija termination.max_duration_s
        t_cfg.pop("duration", None)
        # Omitir 'times' legado en waypoints
        if fam in ("waypoint", "line"):
            t_cfg.pop("times", None)
        return t_cfg

    # Modo compuesto
    sequence = []
    for seg in (mission.segments or []):
        st = seg.type.lower()
        sub_cfg = {"type": st, **seg.params}
        sub_cfg.pop("times", None)
        # Waypoint termina por llegada y permanencia. Una duración aquí cortaría
        # el tramo antes de recorrer la geometría común.
        if seg.duration is not None and st not in ("waypoint", "line"):
            sub_cfg["duration"] = float(seg.duration)
        sequence.append(sub_cfg)

    return {
        "type": "composite",
        "transition_speed": float(mission.transition_speed),
        "sequence": sequence,
    }


def _preview_sampling_slack_s(mission: MissionConfigRequest, dt: float) -> float:
    """
    El seguidor nominal avanza a pasos fijos. Al cerrar cada tramo recto puede
    descartar hasta un paso; sin ese margen el último punto no entra en la muestra.
    """
    legs = 0
    if mission.mode != "composite":
        if mission.family.value in ("waypoint", "line"):
            legs = max(0, len(mission.params.get("waypoints") or []) - 1)
    else:
        for seg in mission.segments or []:
            if str(seg.type).lower() in ("waypoint", "line"):
                legs += max(0, len((seg.params or {}).get("waypoints") or []) - 1)
        legs += max(0, len(mission.segments or []) - 1)
    return legs * dt


def compute_preview(mission: MissionConfigRequest) -> PreviewResponse:
    """
    Muestrea la ruta nominal de la misión y genera información accesible y de límites.
    """
    traj_cfg = build_trajectory_config(mission)
    traj = instantiate_trajectory(traj_cfg)

    # La previsualización usa la duración prevista de la misión, no un plazo fijo
    # asignado a los tramos waypoint. El tope evita muestrear entradas extremas.
    dt = 0.05
    planned = planned_duration_s(mission)
    if not np.isfinite(planned) or planned <= 0.0:
        planned = dt
    dur = float(min(max(planned + _preview_sampling_slack_s(mission, dt), dt), SIMPLE_DURATION_MAX_S))
    times = np.arange(0.0, dur + (0.5 * dt), dt)
    if len(times) < 2:
        times = np.array([0.0, dt])

    ref0 = traj.get_reference(0.0)
    init_pos = [float(round(c, 4)) for c in ref0.position_W_m]

    nominal_state = VehicleState(
        position_W_m=ref0.position_W_m.copy(),
        velocity_W_m_s=ref0.velocity_W_m_s.copy() if hasattr(ref0, "velocity_W_m_s") else np.zeros(3),
        orientation_WB=np.array([1.0, 0.0, 0.0, 0.0]),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=0.0,
    )

    pts: List[List[float]] = []
    is_transitions: List[bool] = []
    seg_indices: List[int] = []

    for t in times:
        if hasattr(traj, "get_reference_for_state"):
            ref = traj.get_reference_for_state(float(t), nominal_state)
        else:
            ref = traj.get_reference(float(t))

        pts.append([float(round(coord, 4)) for coord in ref.position_W_m])

        is_trans = bool(getattr(traj, "in_transition", False))
        seg_idx = int(getattr(traj, "active_index", 0))

        is_transitions.append(is_trans)
        seg_indices.append(seg_idx)

        nominal_state.position_W_m = ref.position_W_m.copy()
        nominal_state.velocity_W_m_s = ref.velocity_W_m_s.copy() if hasattr(ref, "velocity_W_m_s") else np.zeros(3)
        nominal_state.time_s = float(t)
        if hasattr(traj, "check_completion"):
            traj.check_completion(float(t), nominal_state, dt)

    pts_arr = np.array(pts)
    min_z = float(np.min(pts_arr[:, 2]))
    max_z = float(np.max(pts_arr[:, 2]))
    max_r = float(np.max(np.linalg.norm(pts_arr[:, :2], axis=1)))

    pid_fam, pid_exp, _ = select_pid_for_mission(
        mission.mode, mission.family.value, mission.params, mission.segments
    )

    summary_text = (
        f"Misión {mission.family.value} ({mission.mode}). "
        f"Punto inicial: [{init_pos[0]:.2f}, {init_pos[1]:.2f}, {init_pos[2]:.2f}] m. "
        f"Cotas de altura Z: [{min_z:.2f}, {max_z:.2f}] m. "
        f"Radio horizontal máximo: {max_r:.2f} m. "
        f"Duración estimada: {dur:.1f} s. {pid_exp}"
    )

    return PreviewResponse(
        points=pts,
        time_series=[float(round(t, 3)) for t in times],
        is_transition=is_transitions,
        segment_indices=seg_indices,
        initial_position=init_pos,
        bounds={"min_z": min_z, "max_z": max_z, "max_horiz_radius": max_r},
        total_duration_s=float(dur),
        accessibility_summary=summary_text,
        selected_pid_family=pid_fam,
        selected_pid_explanation=pid_exp,
    )


def build_scenario_for_simulation(
    mission: MissionConfigRequest,
    run_dir: Path,
    verifier: Optional[BundleVerifier] = None,
) -> Tuple[Dict[str, Any], str, str]:
    """
    Construye el escenario YAML/dict ejecutable por SimulationRunner.
    Devuelve: (scenario_config, selected_pid_family, selected_pid_explanation).
    """
    if verifier is None:
        verifier = BundleVerifier()

    # 1. Validar envolvente
    is_valid, errors, _, _ = validate_mission_envelope(mission)
    if not is_valid:
        raise ValueError(f"Misión no válida para simulación: {'; '.join(errors)}")

    # 2. Seleccionar PD congelado
    pid_fam, pid_exp, _ = select_pid_for_mission(
        mission.mode, mission.family.value, mission.params, mission.segments
    )
    pid_path = verifier.get_pid_path(pid_fam)
    with open(pid_path, "r", encoding="utf-8") as f:
        pid_cfg = yaml.safe_load(f)

    # 3. Configuración de trayectoria
    traj_cfg = build_trajectory_config(mission)
    traj_inst = instantiate_trajectory(traj_cfg)
    ref0 = traj_inst.get_reference(0.0)

    # 4. Perturbación de viento
    w_rad = np.deg2rad(mission.wind.direction_deg)
    w_x = mission.wind.magnitude_m_s * np.cos(w_rad)
    w_y = mission.wind.magnitude_m_s * np.sin(w_rad)

    # 5. Duración de simulación, alineada con la duración prevista de la previsualización
    sim_duration = simulation_duration_s(mission)

    # 6. Escenario completo
    scenario_cfg = {
        "name": f"neuroflight_{mission.family.value}_{mission.seed}",
        "seed": int(mission.seed),
        "vehicle": {
            "mass_kg": BASE_VEHICLE["mass_kg"],
            "inertia_B_kg_m2": BASE_VEHICLE["inertia_B_kg_m2"],
            "gravity_m_s2": BASE_VEHICLE["gravity_m_s2"],
            "linear_drag_coefficient": [0.05, 0.05, 0.02],
            "rotors": STANDARD_ROTORS,
        },
        "initial_state": {
            "position_W_m": [float(c) for c in ref0.position_W_m],
            "velocity_W_m_s": [0.0, 0.0, 0.0],
            "orientation_WB": None,
            "yaw_rad": float(ref0.yaw_rad),
            "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
        },
        "trajectory": traj_cfg,
        "controller": {
            "type": "classic",
            "Kp_pos": pid_cfg["Kp_pos"],
            "Kd_pos": pid_cfg["Kd_pos"],
            "Kp_att": pid_cfg["Kp_att"],
            "Kd_att": pid_cfg["Kd_att"],
            "max_body_moments_Nm": pid_cfg.get("max_body_moments_Nm", [10.0, 10.0, 2.0]),
        },
        "perturbations": {
            "constant_wind_W_m_s": [float(round(w_x, 4)), float(round(w_y, 4)), 0.0],
            "pos_std_m": 0.0,
            "vel_std_m_s": 0.0,
        },
        "timing": {
            "physics_dt_s": 0.01,
            "control_dt_s": 0.02,
            "telemetry_dt_s": 0.05,
        },
        "termination": {
            "max_duration_s": float(sim_duration),
            "z_min_m": 0.0,
            "max_attitude_angle_rad": 1.256,
            "max_saturation_duration_s": 2.0,
        },
        "output": {
            "dir": str(run_dir.resolve()),
            "telemetry_file": "telemetry.json",
            "metrics_file": "metrics.json",
        },
    }

    validate_scenario_config(scenario_cfg)
    return scenario_cfg, pid_fam, pid_exp
