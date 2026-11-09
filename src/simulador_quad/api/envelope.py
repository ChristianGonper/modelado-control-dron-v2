"""
Validation of the NeuroFlight product envelope.
Enforces physical and demonstration safety limits before simulations are executed.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from simulador_quad.api.models import (
    MissionConfigRequest,
    TrajectoryFamily,
    CompositeSegmentConfig,
)

# Límites efectivos de la demostración. Quedan por debajo de las protecciones
# internas del simulador y cubren los presets de la aplicación.
WIND_MAX_M_S = 1.4
SIMPLE_DURATION_MAX_S = 180.0
SEGMENT_DURATION_MAX_S = 90.0
COMPOSITE_DURATION_MAX_S = 180.0
SIM_LATE_MARGIN_S = 10.0
WAYPOINT_SPEED_MIN_M_S = 0.2
WAYPOINT_SPEED_MAX_M_S = 1.0
WAYPOINT_ACC_MIN_M_S2 = 0.2
WAYPOINT_ACC_MAX_M_S2 = 0.8
WAYPOINT_PATH_MAX_M = 60.0
WAYPOINT_POINTS_MAX = 16
LISSAJOUS_AMP_MAX_M = 4.0
LISSAJOUS_OMEGA_MIN = 0.1
LISSAJOUS_OMEGA_MAX = 1.2
LISSAJOUS_SPEED_MAX_M_S = 1.5
LISSAJOUS_ACC_MAX_M_S2 = 1.1
HORIZONTAL_EXTENT_MAX_M = 50.0
ALTITUDE_MIN_M = 0.3
ALTITUDE_MAX_M = 50.0
VERTICAL_SPAN_MAX_M = 20.0
TRANSITION_ACC_M_S2 = 0.5
TRANSITION_GAP_M = 0.05

_CONTINUOUS_FAMILIES = ("hold", "circle", "lissajous", "lemniscate")
_DEFAULT_DURATION_S = {
    "hold": 10.0,
    "circle": 15.0,
    "lissajous": 20.0,
    "lemniscate": 18.0,
}

# Geometrías g01-g06 de classic dataset (presentes en train/test del TFG)
DATASET_WAYPOINTS_G01_G06 = [
    [[0.0, 0.0, 2.0], [2.0, 0.0, 2.0], [2.0, 2.0, 2.0], [0.0, 2.0, 2.0], [0.0, 0.0, 2.0]], # g01 square
    [[0.0, 0.0, 2.0], [3.0, 0.0, 2.0], [3.0, 1.0, 2.0], [0.0, 1.0, 2.0], [0.0, 0.0, 2.0]], # g02 rect
    [[0.0, 0.0, 2.0], [1.0, 1.0, 2.0], [2.0, 0.0, 2.0], [3.0, 1.0, 2.0], [4.0, 0.0, 2.0]], # g03 zigzag
    [[0.0, 0.0, 1.0], [1.0, 0.0, 1.5], [2.0, 0.0, 2.0], [3.0, 0.0, 2.5], [4.0, 0.0, 3.0]], # g04 stairs
    [[0.0, 0.0, 1.0], [2.0, 2.0, 3.0]], # g05 diag3d
    [[0.0, 0.0, 2.0], [1.0, 1.0, 3.0], [0.0, 2.0, 2.0], [-1.0, 1.0, 3.0], [0.0, 0.0, 2.0]], # g06 closed
]


def is_waypoint_geometry_in_dataset(waypoints: List[List[float]]) -> bool:
    """Verifica si la lista de waypoints coincide exactamente con alguna geometría g01-g06."""
    wps_arr = np.asarray(waypoints, dtype=float)
    for ds_wps in DATASET_WAYPOINTS_G01_G06:
        ds_arr = np.asarray(ds_wps, dtype=float)
        if wps_arr.shape == ds_arr.shape and np.allclose(wps_arr, ds_arr, atol=1e-3):
            return True
    return False


def get_initial_position(family: str, params: Dict[str, Any]) -> List[float]:
    """Calcula la posición inicial exacta que fija la trayectoria."""
    fam = family.lower()
    if fam == "hold":
        pos = params.get("position_W_m", [0.0, 0.0, 1.5])
        return [float(pos[0]), float(pos[1]), float(pos[2])]

    elif fam == "circle":
        c = params.get("center_W_m", [0.0, 0.0, 2.0])
        r = float(params.get("radius_m", 1.5))
        tilt_deg = float(params.get("tilt_deg", 0.0))
        plane_yaw_deg = float(params.get("plane_yaw_deg", 0.0))
        tilt_rad = np.deg2rad(tilt_deg)
        plane_yaw_rad = np.deg2rad(plane_yaw_deg)

        # En t=0, p_plane = [r, 0, 0]
        # Rotación Rz(plane_yaw) * Ry(tilt)
        p_plane = np.array([r, 0.0, 0.0])
        cy, sy = np.cos(plane_yaw_rad), np.sin(plane_yaw_rad)
        ct, st = np.cos(tilt_rad), np.sin(tilt_rad)
        R = np.array([
            [cy*ct, -sy, cy*st],
            [sy*ct,  cy, sy*st],
            [-st,   0.0,    ct]
        ])
        pos = np.array(c, dtype=float) + R @ p_plane
        return [float(pos[0]), float(pos[1]), float(pos[2])]

    elif fam == "lissajous":
        c = params.get("center_W_m", [0.0, 0.0, 2.5])
        # En t=0, sin(0) = 0, luego pos = center
        return [float(c[0]), float(c[1]), float(c[2])]

    elif fam in ("waypoint", "line"):
        wps = params.get("waypoints", [[0.0, 0.0, 1.5], [1.0, 1.0, 1.5]])
        if wps:
            return [float(wps[0][0]), float(wps[0][1]), float(wps[0][2])]
        return [0.0, 0.0, 1.5]

    elif fam == "lemniscate":
        c = params.get("center_W_m", [0.0, 0.0, 2.0])
        # En t=0, sin(0) = 0, luego pos = center
        return [float(c[0]), float(c[1]), float(c[2])]

    return [0.0, 0.0, 1.5]


def trapezoidal_duration_s(length_m: float, v_max: float, a_max: float) -> float:
    """Tiempo de un tramo recto que arranca y frena a velocidad cero."""
    if length_m <= 1e-9:
        return 0.0
    if v_max <= 0.0 or a_max <= 0.0:
        return float("inf")
    t_acc = v_max / a_max
    d_acc = 0.5 * a_max * t_acc ** 2
    if 2.0 * d_acc <= length_m:
        return 2.0 * t_acc + (length_m - 2.0 * d_acc) / v_max
    return 2.0 * float(np.sqrt(length_m / a_max))


def estimate_waypoint_motion_s(params: Dict[str, Any]) -> float:
    """
    Duración nominal de una ruta por puntos: perfil trapezoidal de cada tramo
    más la permanencia en el punto. No usa una duración fija de interfaz.
    """
    waypoints = params.get("waypoints") or []
    speed = float(params.get("max_speed_m_s", 0.6))
    accel = float(params.get("max_acceleration_m_s2", 0.5))
    dwell = float(params.get("dwell_time_s", 0.40))
    if dwell < 0.0 or speed <= 0.0 or accel <= 0.0:
        return float("inf")
    total = 0.0
    for idx in range(len(waypoints) - 1):
        length = float(np.linalg.norm(
            np.asarray(waypoints[idx + 1], dtype=float) - np.asarray(waypoints[idx], dtype=float)
        ))
        total += trapezoidal_duration_s(length, speed, accel) + dwell
    return total


def _boundary_position(seg_type: str, params: Dict[str, Any], duration: Optional[float], at_end: bool) -> np.ndarray:
    """Posición de inicio o fin geométrico de un tramo, con el mismo contrato que el simulador."""
    fam = seg_type.lower()
    if fam in ("waypoint", "line"):
        waypoints = params.get("waypoints") or [[0.0, 0.0, 1.5]]
        chosen = waypoints[-1] if at_end else waypoints[0]
        return np.asarray(chosen, dtype=float)

    from simulador_quad.scenarios.loader import instantiate_trajectory

    cfg = {"type": fam, **params}
    cfg.pop("duration", None)
    cfg.pop("times", None)
    trajectory = instantiate_trajectory(cfg)
    sample_t = float(duration or 0.0) if at_end else 0.0
    return np.asarray(trajectory.get_reference(sample_t).position_W_m, dtype=float)


def planned_duration_s(mission: MissionConfigRequest) -> float:
    """
    Duración prevista de la misión: duración explícita de los tramos continuos,
    tiempo nominal de waypoint y transiciones automáticas entre extremos.
    """
    if mission.mode != "composite":
        fam = mission.family.value
        if fam in ("waypoint", "line"):
            return estimate_waypoint_motion_s(mission.params)
        return float(mission.params.get("duration", _DEFAULT_DURATION_S.get(fam, 15.0)))

    segments = mission.segments or []
    total = 0.0
    for seg in segments:
        if seg.type.lower() in ("waypoint", "line"):
            total += estimate_waypoint_motion_s(seg.params)
        else:
            total += float(seg.duration or 0.0)

    speed = float(mission.transition_speed)
    for idx in range(len(segments) - 1):
        current = segments[idx]
        nxt = segments[idx + 1]
        end = _boundary_position(current.type, current.params, current.duration, at_end=True)
        start = _boundary_position(nxt.type, nxt.params, nxt.duration, at_end=False)
        gap = float(np.linalg.norm(end - start))
        if gap > TRANSITION_GAP_M:
            total += trapezoidal_duration_s(gap, speed, TRANSITION_ACC_M_S2)
    return float(total)


def simulation_duration_s(mission: MissionConfigRequest) -> float:
    """
    Tope de simulación. En familias continuas coincide con la duración pedida.
    En waypoint y composición añade un margen de llegada y no supera el tope de la demo.
    """
    planned = planned_duration_s(mission)
    if not np.isfinite(planned) or planned <= 0.0:
        return SIMPLE_DURATION_MAX_S
    fam = mission.family.value if mission.mode != "composite" else ""
    if mission.mode != "composite" and fam not in ("waypoint", "line"):
        return float(min(SIMPLE_DURATION_MAX_S, planned))
    return float(min(COMPOSITE_DURATION_MAX_S, planned + SIM_LATE_MARGIN_S))


def validate_single_segment(
    seg_type: str,
    params: Dict[str, Any],
    prefix: str = "",
    is_composite: bool = False,
    duration: Optional[float] = None,
) -> Tuple[List[str], List[str]]:
    """Valida los parámetros de un tramo o misión simple contra la envolvente."""
    errors = []
    warnings = []
    p = prefix + (" " if prefix else "")

    # Viento (si está presente en params)
    if "wind" in params:
        w_mag = float(params["wind"].get("magnitude_m_s", 0.0))
        if w_mag > 1.4:
            errors.append(f"{p}Viento horizontal de {w_mag:.1f} m/s excede el límite de 1.4 m/s de la demostración.")

    fam = seg_type.lower()

    if is_composite and fam != "waypoint":
        if duration is None or duration <= 0:
            errors.append(f"{p}El tramo '{fam}' continuo requiere una duración positiva explícita.")
        elif duration > SEGMENT_DURATION_MAX_S:
            errors.append(
                f"{p}La duración del tramo ({duration:.1f} s) excede el máximo por tramo "
                f"({SEGMENT_DURATION_MAX_S:.0f} s). Reduzca ese tramo."
            )
    elif not is_composite and fam in _CONTINUOUS_FAMILIES and "duration" in params and params.get("duration") is not None:
        simple_duration = float(params["duration"])
        if not np.isfinite(simple_duration) or simple_duration <= 0.0 or simple_duration > SIMPLE_DURATION_MAX_S:
            errors.append(
                f"{p}La duración prevista ({params.get('duration')} s) debe ser mayor que 0 "
                f"y no superar {SIMPLE_DURATION_MAX_S:.0f} s."
            )

    if fam == "hold":
        pos = params.get("position_W_m")
        if not pos or len(pos) != 3:
            errors.append(f"{p}Posición 'position_W_m' debe ser un vector [x, y, z] de 3 elementos.")
        else:
            z = float(pos[2])
            if z < ALTITUDE_MIN_M:
                errors.append(f"{p}Altura {z:.2f} m inferior al despeje mínimo al suelo ({ALTITUDE_MIN_M} m).")
            elif z > ALTITUDE_MAX_M:
                errors.append(f"{p}Altura {z:.2f} m excede el techo operacional ({ALTITUDE_MAX_M:.0f} m).")
            if abs(float(pos[0])) > HORIZONTAL_EXTENT_MAX_M or abs(float(pos[1])) > HORIZONTAL_EXTENT_MAX_M:
                errors.append(f"{p}Posición horizontal [{pos[0]:.1f}, {pos[1]:.1f}] fuera del área de vuelo ({HORIZONTAL_EXTENT_MAX_M:.0f} m).")

    elif fam == "circle":
        c = params.get("center_W_m", [0.0, 0.0, 2.0])
        r = float(params.get("radius_m", 1.5))
        w = float(params.get("omega_rad_s", 0.6))
        tilt_deg = float(params.get("tilt_deg", 0.0))

        if r < 0.5 or r > 4.0:
            errors.append(f"{p}Radio del círculo ({r:.2f} m) fuera del rango admitido (0.5 a 4.0 m).")
        if w <= 0.0:
            errors.append(f"{p}Velocidad angular omega ({w:.2f} rad/s) debe ser positiva.")

        v_tang = r * w
        if v_tang > 1.5001:
            errors.append(f"{p}Velocidad tangencial (R × ω = {v_tang:.2f} m/s) excede el límite de 1.5 m/s.")

        a_centr = r * (w ** 2)
        if a_centr > 1.0001:
            errors.append(f"{p}Aceleración centrípeta (R × ω² = {a_centr:.2f} m/s²) excede el límite de 1.0 m/s².")

        if tilt_deg < 0.0 or tilt_deg > 30.0:
            errors.append(f"{p}Inclinación del plano ({tilt_deg:.1f}°) fuera del rango admitido (0° a 30°).")

        cx = float(c[0]) if len(c) > 0 else 0.0
        cy = float(c[1]) if len(c) > 1 else 0.0
        if abs(cx) > HORIZONTAL_EXTENT_MAX_M or abs(cy) > HORIZONTAL_EXTENT_MAX_M:
            errors.append(
                f"{p}El centro del círculo [{cx:.1f}, {cy:.1f}] supera el área de vuelo ({HORIZONTAL_EXTENT_MAX_M:.0f} m)."
            )

        # Cota de altura del círculo inclinado relativa al suelo y al techo operacional
        tilt_rad = np.deg2rad(tilt_deg)
        delta_z = r * np.sin(tilt_rad)
        cz = float(c[2]) if len(c) > 2 else 2.0
        min_z = cz - delta_z
        max_z = cz + delta_z
        if min_z < ALTITUDE_MIN_M:
            errors.append(f"{p}La altura mínima del círculo inclinado ({min_z:.2f} m) cae por debajo del despeje al suelo ({ALTITUDE_MIN_M} m).")
        if max_z > ALTITUDE_MAX_M:
            errors.append(f"{p}La altura máxima del círculo inclinado ({max_z:.2f} m) supera el techo operacional ({ALTITUDE_MAX_M:.0f} m).")

    elif fam == "lissajous":
        c = params.get("center_W_m", [0.0, 0.0, 2.5])
        amps = params.get("amplitudes", [1.5, 1.5, 0.5])
        omegas = params.get("omegas", [0.5, 0.7, 0.3])

        if len(amps) != 3 or len(omegas) != 3:
            errors.append(f"{p}Lissajous requiere amplitudes y omegas de 3 componentes [x, y, z].")
        else:
            cz = float(c[2]) if len(c) > 2 else 2.5
            az = float(amps[2])
            min_z = cz - az
            max_z = cz + az
            if min_z < ALTITUDE_MIN_M:
                errors.append(f"{p}La oscilación inferior de Lissajous ({min_z:.2f} m) cae por debajo del despeje al suelo ({ALTITUDE_MIN_M} m).")
            if max_z > ALTITUDE_MAX_M:
                errors.append(f"{p}La altura máxima de Lissajous ({max_z:.2f} m) supera el techo operacional ({ALTITUDE_MAX_M:.0f} m).")

            cx = float(c[0]) if len(c) > 0 else 0.0
            cy = float(c[1]) if len(c) > 1 else 0.0
            if abs(cx) > HORIZONTAL_EXTENT_MAX_M or abs(cy) > HORIZONTAL_EXTENT_MAX_M:
                errors.append(
                    f"{p}El centro de Lissajous [{cx:.1f}, {cy:.1f}] supera el área de vuelo ({HORIZONTAL_EXTENT_MAX_M:.0f} m)."
                )

            for ax, a_val, w_val in zip(["X", "Y", "Z"], amps, omegas):
                amp = float(a_val)
                omega = float(w_val)
                if amp <= 0.0 or amp > LISSAJOUS_AMP_MAX_M:
                    errors.append(
                        f"{p}Amplitud en {ax} ({amp:.2f} m) fuera de (0, {LISSAJOUS_AMP_MAX_M:.1f}] m."
                    )
                if omega < LISSAJOUS_OMEGA_MIN or omega > LISSAJOUS_OMEGA_MAX:
                    errors.append(
                        f"{p}Frecuencia omega en {ax} ({w_val} rad/s) fuera de "
                        f"[{LISSAJOUS_OMEGA_MIN}, {LISSAJOUS_OMEGA_MAX}] rad/s."
                    )
                peak_speed = abs(amp * omega)
                peak_acc = abs(amp * omega ** 2)
                if peak_speed > LISSAJOUS_SPEED_MAX_M_S:
                    errors.append(
                        f"{p}Velocidad de Lissajous en {ax} (A·ω = {peak_speed:.2f} m/s) "
                        f"excede {LISSAJOUS_SPEED_MAX_M_S:.1f} m/s. Baje amplitud o frecuencia."
                    )
                if peak_acc > LISSAJOUS_ACC_MAX_M_S2:
                    errors.append(
                        f"{p}Aceleración de Lissajous en {ax} (A·ω² = {peak_acc:.2f} m/s²) "
                        f"excede {LISSAJOUS_ACC_MAX_M_S2:.1f} m/s². Baje amplitud o frecuencia."
                    )

            # Comprobar degeneración exacta en el plano horizontal
            if abs(float(omegas[0]) - float(omegas[1])) < 1e-4:
                warnings.append(f"{p}Frecuencias idénticas en X e Y pueden colapsar Lissajous a un segmento lineal.")

    elif fam in ("waypoint", "line"):
        wps = params.get("waypoints", [])
        if not wps or len(wps) < 2:
            errors.append(f"{p}Ruta por puntos requiere al menos 2 waypoints.")
        else:
            z_vals = []
            for idx, wp in enumerate(wps):
                if len(wp) != 3:
                    errors.append(f"{p}Waypoint #{idx+1} debe tener coordenadas [X, Y, Z].")
                    continue
                z = float(wp[2])
                z_vals.append(z)
                if z < ALTITUDE_MIN_M:
                    errors.append(f"{p}Waypoint #{idx+1} altura {z:.2f} m inferior al despeje al suelo ({ALTITUDE_MIN_M} m).")
                elif z > ALTITUDE_MAX_M:
                    errors.append(f"{p}Waypoint #{idx+1} altura {z:.2f} m excede el techo operacional ({ALTITUDE_MAX_M:.0f} m).")
                if abs(float(wp[0])) > HORIZONTAL_EXTENT_MAX_M or abs(float(wp[1])) > HORIZONTAL_EXTENT_MAX_M:
                    errors.append(f"{p}Waypoint #{idx+1} fuera del área de vuelo ({HORIZONTAL_EXTENT_MAX_M:.0f} m).")

            if z_vals:
                v_span = max(z_vals) - min(z_vals)
                if v_span > VERTICAL_SPAN_MAX_M:
                    errors.append(f"{p}El rango vertical relativo de la ruta ({v_span:.1f} m) excede el máximo permitido ({VERTICAL_SPAN_MAX_M:.1f} m).")

            # Comprobar paso mínimo entre consecutivos
            for idx in range(len(wps) - 1):
                p1 = np.array(wps[idx], dtype=float)
                p2 = np.array(wps[idx+1], dtype=float)
                dist = np.linalg.norm(p2 - p1)
                if dist < 0.05:
                    errors.append(f"{p}Distancia entre waypoints #{idx+1} y #{idx+2} ({dist:.2f} m) es demasiado pequeña (< 0.05 m).")

        speed = float(params.get("max_speed_m_s", 0.6))
        acc = float(params.get("max_acceleration_m_s2", 0.5))
        if speed < WAYPOINT_SPEED_MIN_M_S or speed > WAYPOINT_SPEED_MAX_M_S:
            errors.append(
                f"{p}Velocidad máxima ({speed:.2f} m/s) fuera de "
                f"[{WAYPOINT_SPEED_MIN_M_S:.1f}, {WAYPOINT_SPEED_MAX_M_S:.1f}] m/s."
            )
        if acc < WAYPOINT_ACC_MIN_M_S2 or acc > WAYPOINT_ACC_MAX_M_S2:
            errors.append(
                f"{p}Aceleración máxima ({acc:.2f} m/s²) fuera de "
                f"[{WAYPOINT_ACC_MIN_M_S2:.1f}, {WAYPOINT_ACC_MAX_M_S2:.1f}] m/s²."
            )
        if wps and len(wps) > WAYPOINT_POINTS_MAX:
            errors.append(
                f"{p}La ruta tiene {len(wps)} puntos y el máximo de la demo es {WAYPOINT_POINTS_MAX}."
            )
        if wps and len(wps) >= 2 and all(len(wp) == 3 for wp in wps):
            path_length = float(sum(
                np.linalg.norm(np.asarray(wps[idx + 1], dtype=float) - np.asarray(wps[idx], dtype=float))
                for idx in range(len(wps) - 1)
            ))
            if path_length > WAYPOINT_PATH_MAX_M:
                errors.append(
                    f"{p}La longitud de la ruta ({path_length:.1f} m) supera {WAYPOINT_PATH_MAX_M:.0f} m. "
                    "Acorte la trayectoria."
                )
            speed_ok = WAYPOINT_SPEED_MIN_M_S <= speed <= WAYPOINT_SPEED_MAX_M_S
            acc_ok = WAYPOINT_ACC_MIN_M_S2 <= acc <= WAYPOINT_ACC_MAX_M_S2
            if speed_ok and acc_ok:
                motion_s = estimate_waypoint_motion_s(params)
                if not np.isfinite(motion_s) or motion_s > SIMPLE_DURATION_MAX_S:
                    shown = "no finita" if not np.isfinite(motion_s) else f"{motion_s:.1f} s"
                    errors.append(
                        f"{p}La duración nominal de la ruta por puntos ({shown}) supera "
                        f"{SIMPLE_DURATION_MAX_S:.0f} s. Acorte la ruta."
                    )

    elif fam == "lemniscate":
        c = params.get("center_W_m", [0.0, 0.0, 2.0])
        a = float(params.get("a", 2.0))
        b = float(params.get("b", 1.0))
        w = float(params.get("omega_rad_s", 0.35))
        z_amp = float(params.get("z_amp", 0.0))

        if a < 0.5 or a > 4.0:
            errors.append(f"{p}Semieje 'a' de lemniscata ({a:.2f} m) fuera de rango (0.5 a 4.0 m).")
        if b < 0.3 or b > 2.5:
            errors.append(f"{p}Semieje 'b' de lemniscata ({b:.2f} m) fuera de rango (0.3 a 2.5 m).")
        if w < 0.15 or w > 0.6:
            errors.append(f"{p}Velocidad angular ({w:.2f} rad/s) fuera de rango (0.15 a 0.6 rad/s).")

        cx = float(c[0]) if len(c) > 0 else 0.0
        cy = float(c[1]) if len(c) > 1 else 0.0
        cz = float(c[2]) if len(c) > 2 else 2.0
        if abs(cx) > HORIZONTAL_EXTENT_MAX_M or abs(cy) > HORIZONTAL_EXTENT_MAX_M:
            errors.append(
                f"{p}El centro de lemniscata [{cx:.1f}, {cy:.1f}] supera el área de vuelo ({HORIZONTAL_EXTENT_MAX_M:.0f} m)."
            )

        min_z = cz - z_amp
        max_z = cz + z_amp
        if min_z < ALTITUDE_MIN_M:
            errors.append(f"{p}La altura mínima de lemniscata ({min_z:.2f} m) cae por debajo del despeje al suelo ({ALTITUDE_MIN_M} m).")
        if max_z > ALTITUDE_MAX_M:
            errors.append(f"{p}La altura máxima de lemniscata ({max_z:.2f} m) supera el techo operacional ({ALTITUDE_MAX_M:.0f} m).")

    return errors, warnings


def validate_mission_envelope(
    mission: MissionConfigRequest
) -> Tuple[bool, List[str], List[str], List[float]]:
    """
    Valida la misión completa (simple o compuesta) y devuelve:
    (es_válida, lista_errores, lista_advertencias, posicion_inicial).
    """
    errors: List[str] = []
    warnings: List[str] = []

    wind_mag = float(mission.wind.magnitude_m_s)
    if not np.isfinite(wind_mag) or wind_mag < 0.0:
        errors.append(
            f"La magnitud del viento ({mission.wind.magnitude_m_s} m/s) debe estar entre 0 y {WIND_MAX_M_S:.1f} m/s."
        )
    elif wind_mag > WIND_MAX_M_S:
        errors.append(f"Viento horizontal de {wind_mag:.2f} m/s excede el límite de {WIND_MAX_M_S:.1f} m/s.")

    initial_pos = [0.0, 0.0, 1.5]

    if mission.mode == "simple":
        fam_str = mission.family.value
        initial_pos = get_initial_position(fam_str, mission.params)
        seg_errors, seg_warnings = validate_single_segment(fam_str, mission.params, prefix=fam_str.capitalize())
        errors.extend(seg_errors)
        warnings.extend(seg_warnings)

    elif mission.mode == "composite":
        if not mission.segments or len(mission.segments) < 2 or len(mission.segments) > 4:
            errors.append(f"La composición debe contener entre 2 y 4 tramos (recibidos: {len(mission.segments) if mission.segments else 0}).")
        else:
            first_seg = mission.segments[0]
            initial_pos = get_initial_position(first_seg.type, first_seg.params)

            for idx, seg in enumerate(mission.segments):
                prefix = f"Tramo #{idx+1} ({seg.type})"
                seg_errors, seg_warnings = validate_single_segment(
                    seg.type, seg.params, prefix=prefix, is_composite=True, duration=seg.duration
                )
                errors.extend(seg_errors)
                warnings.extend(seg_warnings)
            if not any(err.startswith("Tramo #") or err.startswith("La composición") for err in errors):
                planned = planned_duration_s(mission)
                if not np.isfinite(planned) or planned > COMPOSITE_DURATION_MAX_S:
                    shown = "no finita" if not np.isfinite(planned) else f"{planned:.1f} s"
                    errors.append(
                        f"La duración prevista, transiciones incluidas ({shown}), excede el máximo "
                        f"de la demo ({COMPOSITE_DURATION_MAX_S:.0f} s)."
                    )

    is_valid = len(errors) == 0
    return is_valid, errors, warnings, initial_pos
