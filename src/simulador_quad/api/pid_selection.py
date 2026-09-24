"""
Deterministic PID selection for simple and composite missions.
Implements the NeuroFlight product decision: single PID for entire composite mission
based on dominant nominal path length.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from simulador_quad.trajectories.analytic import (
    CircleTrajectory,
    HoldTrajectory,
    LemniscateTrajectory,
    LissajousTrajectory,
)


def compute_segment_length(seg_type: str, params: Dict[str, Any], duration: float = 5.0) -> float:
    """Calcula la longitud nominal 3D recorrida por un tramo."""
    fam = seg_type.lower()
    if fam == "hold":
        return 0.0

    elif fam in ("waypoint", "line"):
        wps = params.get("waypoints", [])
        if len(wps) < 2:
            return 0.0
        wps_arr = np.asarray(wps, dtype=float)
        diffs = np.diff(wps_arr, axis=0)
        segment_lengths = np.linalg.norm(diffs, axis=1)
        return float(np.sum(segment_lengths))

    elif fam == "circle":
        r = float(params.get("radius_m", 1.5))
        w = float(params.get("omega_rad_s", 0.6))
        # En un círculo, velocidad tangencial constante v = R * w
        return float(r * w * duration)

    elif fam == "lissajous":
        c = np.array(params.get("center_W_m", [0.0, 0.0, 2.5]), dtype=float)
        amps = np.array(params.get("amplitudes", [1.5, 1.5, 0.5]), dtype=float)
        omegas = np.array(params.get("omegas", [0.5, 0.7, 0.3]), dtype=float)
        traj = LissajousTrajectory(c, amps, omegas)
        times = np.linspace(0.0, duration, 200)
        pts = np.array([traj.get_reference(t).position_W_m for t in times])
        diffs = np.diff(pts, axis=0)
        return float(np.sum(np.linalg.norm(diffs, axis=1)))

    elif fam == "lemniscate":
        c = np.array(params.get("center_W_m", [0.0, 0.0, 2.0]), dtype=float)
        a = float(params.get("a", 2.0))
        b = float(params.get("b", 1.0))
        w = float(params.get("omega_rad_s", 0.35))
        z_amp = float(params.get("z_amp", 0.0))
        z_omega = float(params.get("z_omega_rad_s", 0.0))
        traj = LemniscateTrajectory(c, a, b, w, z_amp=z_amp, z_omega_rad_s=z_omega, warmup_s=0.0)
        times = np.linspace(0.0, duration, 200)
        pts = np.array([traj.get_reference(t).position_W_m for t in times])
        diffs = np.diff(pts, axis=0)
        return float(np.sum(np.linalg.norm(diffs, axis=1)))

    return 0.0


def select_pid_for_mission(
    mode: str,
    family: str,
    params: Dict[str, Any],
    segments: Optional[List[Any]] = None
) -> Tuple[str, str, Dict[str, float]]:
    """
    Selecciona el PD congelado único y produce una explicación.
    Devuelve: (pid_family_file, explanation_text, lengths_by_family).
    """
    if mode == "simple":
        fam = family.lower()
        if fam == "lemniscate":
            return (
                "lissajous",
                "Lemniscata utiliza el PD congelado de Lissajous conforme a la regla de producto y el ensayo OOD.",
                {"lemniscate": 1.0}
            )
        elif fam in ("waypoint", "line"):
            return (
                "waypoint",
                "Misión waypoint: utiliza el PD congelado de ruta por puntos.",
                {"waypoint": 1.0}
            )
        elif fam in ("hold", "circle", "lissajous"):
            return (
                fam,
                f"Misión {fam}: utiliza el PD congelado optimizado para esta familia.",
                {fam: 1.0}
            )
        return ("hold", "PD de mantener posición por defecto.", {"hold": 1.0})

    # Modo compuesto
    if not segments:
        return ("hold", "Sin tramos especificados: fallback a PD de hold.", {})

    lengths: Dict[str, float] = {}
    first_seen: Dict[str, int] = {}

    for idx, seg in enumerate(segments):
        seg_type = seg.type if hasattr(seg, "type") else seg.get("type", "hold")
        seg_type = seg_type.lower()
        if seg_type == "line":
            seg_type = "waypoint"

        seg_params = seg.params if hasattr(seg, "params") else seg.get("params", {})
        seg_duration = seg.duration if hasattr(seg, "duration") else seg.get("duration", 5.0)
        if seg_duration is None:
            seg_duration = 5.0

        length = compute_segment_length(seg_type, seg_params, float(seg_duration))
        lengths[seg_type] = lengths.get(seg_type, 0.0) + length
        if seg_type not in first_seen:
            first_seen[seg_type] = idx

    total_len = sum(lengths.values())

    # Caso toda la composición es estacionaria
    if total_len <= 1e-6:
        return (
            "hold",
            "Toda la composición es estacionaria (longitud 0 m); se utiliza el PD congelado de hold.",
            lengths
        )

    # Ordenar por longitud descendente; en caso de empate, por índice de primera aparición
    # Nota: la regla de desempate prefiere menor first_seen
    sorted_families = sorted(
        lengths.keys(),
        key=lambda f: (-lengths[f], first_seen[f])
    )

    dominant_family = sorted_families[0]
    dom_length = lengths[dominant_family]
    pct = (dom_length / total_len * 100.0) if total_len > 0 else 100.0

    # Comprobar si hubo empate en primer lugar
    has_tie = False
    if len(sorted_families) > 1 and np.isclose(lengths[sorted_families[0]], lengths[sorted_families[1]], atol=1e-3):
        has_tie = True

    if dominant_family == "lemniscate":
        target_pid = "lissajous"
        tie_str = " (desempate por primera aparición)" if has_tie else ""
        explanation = (
            f"Familia dominante: Lemniscata con {dom_length:.1f} m ({pct:.0f}% de longitud nominal){tie_str}. "
            f"Se asocia al PD congelado de Lissajous conforme a la regla de producto."
        )
    else:
        target_pid = dominant_family
        tie_str = " (desempate por primera aparición)" if has_tie else ""
        explanation = (
            f"Familia dominante: {dominant_family.capitalize()} con {dom_length:.1f} m "
            f"({pct:.0f}% de longitud nominal){tie_str}. Se utiliza su PD congelado para toda la misión."
        )

    return target_pid, explanation, lengths
