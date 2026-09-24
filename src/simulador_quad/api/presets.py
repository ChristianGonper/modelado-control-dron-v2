"""
Preset catalog and seed-based variant generator for NeuroFlight.
Guarantees that waypoint presets exclude the dataset train/test geometries g01-g06,
omits legacy times fields, and keeps all presets within the product demonstration envelope.
"""

from typing import Any, Dict, List
import numpy as np

from simulador_quad.api.envelope import is_waypoint_geometry_in_dataset


# El sorteo inicial alterna la ruta limpia y las dos hélices OOD.
# La hélice compacta queda solo como ejemplo adicional del catálogo.
INITIAL_WAYPOINT_PRESET_KEYS = (
    "waypoint_clean",
    "helix_ascending",
    "helix_descending",
)


# Waypoint preset geometries verified outside train/test
def get_waypoint_presets() -> Dict[str, Dict[str, Any]]:
    # 1. Waypoint clean (añade ascenso antes de cuadrado, descarta times)
    wp_clean = [
        [0.0, 0.0, 0.5], # Empezamos a 0.5 m para respetar la cota inferior estricta
        [0.0, 0.0, 2.0],
        [2.0, 0.0, 2.0],
        [2.0, 2.0, 2.0],
        [0.0, 2.0, 2.0],
        [0.0, 0.0, 2.0],
    ]

    # 2. Hélice ascendente OOD (9 puntos)
    th8 = np.linspace(0, 4 * np.pi, 9)
    helix_up = [
        [float(round(2.0 * np.cos(t), 3)), float(round(2.0 * np.sin(t), 3)), float(round(1.0 + 3.0 * t / (4.0 * np.pi), 3))]
        for t in th8
    ]

    # 3. Hélice descendente OOD (8 puntos)
    th9 = np.linspace(0, 3 * np.pi, 8)
    helix_down = [
        [float(round(1.5 * np.cos(t), 3)), float(round(1.5 * np.sin(t), 3)), float(round(4.0 - 3.0 * t / (3.0 * np.pi), 3))]
        for t in th9
    ]

    # 4. Hélice compacta OOD (12 puntos)
    th10 = np.linspace(0, 6 * np.pi, 12)
    helix_tight = [
        [float(round(0.8 * np.cos(t), 3)), float(round(0.8 * np.sin(t), 3)), float(round(1.0 + 4.0 * t / (6.0 * np.pi), 3))]
        for t in th10
    ]

    presets = {
        "waypoint_clean": {
            "name": "Ruta limpia con ascenso",
            "description": "Ascenso inicial y cuadrado horizontal a 2 m de altura. Sin tiempos prefijados.",
            "waypoints": wp_clean,
            "max_speed_m_s": 0.6,
            "max_acceleration_m_s2": 0.5,
            "waypoint_tolerance_m": 0.20,
            "waypoint_speed_tolerance_m_s": 0.20,
            "dwell_time_s": 0.40,
            "yaw_rad": 0.0,
        },
        "helix_ascending": {
            "name": "Hélice ascendente",
            "description": "Trayectoria espiral ascendente entre 1 m y 4 m de cota (batería OOD).",
            "waypoints": helix_up,
            "max_speed_m_s": 0.8,
            "max_acceleration_m_s2": 0.6,
            "waypoint_tolerance_m": 0.20,
            "waypoint_speed_tolerance_m_s": 0.20,
            "dwell_time_s": 0.40,
            "yaw_rad": 0.0,
        },
        "helix_descending": {
            "name": "Hélice descendente",
            "description": "Espiral descendente controlada desde 4 m hasta 1 m (batería OOD).",
            "waypoints": helix_down,
            "max_speed_m_s": 0.6,
            "max_acceleration_m_s2": 0.4,
            "waypoint_tolerance_m": 0.20,
            "waypoint_speed_tolerance_m_s": 0.20,
            "dwell_time_s": 0.40,
            "yaw_rad": 0.0,
        },
        "helix_tight": {
            "name": "Hélice compacta (exigente)",
            "description": "Hélice de radio reducido (0.8 m) y 3 vueltas completas.",
            "waypoints": helix_tight,
            "max_speed_m_s": 1.0,
            "max_acceleration_m_s2": 0.8,
            "waypoint_tolerance_m": 0.20,
            "waypoint_speed_tolerance_m_s": 0.20,
            "dwell_time_s": 0.40,
            "yaw_rad": 0.0,
        },
    }

    # Verificación de seguridad
    for k, v in presets.items():
        assert not is_waypoint_geometry_in_dataset(v["waypoints"]), f"Preset {k} coincide con geometrías de train/test!"

    return presets


def get_composite_presets() -> Dict[str, Dict[str, Any]]:
    return {
        "composite_classic": {
            "name": "Composición OOD TFG (Estacionario + Círculo + Lemniscata)",
            "description": "Secuencia representativa del experimento OOD: parada 3s, círculo 10s y lemniscata 15s.",
            "transition_speed": 0.8,
            "segments": [
                {
                    "type": "hold",
                    "duration": 3.0,
                    "params": {"position_W_m": [0.0, 0.0, 1.5], "yaw_rad": 0.0},
                },
                {
                    "type": "circle",
                    "duration": 10.0,
                    "params": {
                        "center_W_m": [0.0, 0.0, 1.5],
                        "radius_m": 1.5,
                        "omega_rad_s": 0.6,
                        "yaw_mode": "forward",
                        "tilt_deg": 0.0,
                        "plane_yaw_deg": 0.0,
                    },
                },
                {
                    "type": "lemniscate",
                    "duration": 15.0,
                    "params": {
                        "center_W_m": [1.5, 0.0, 2.0],
                        "a": 1.2,
                        "b": 0.6,
                        "omega_rad_s": 0.4,
                        "z_amp": 0.0,
                        "yaw_mode": "forward",
                    },
                },
            ],
        },
        "composite_multimode": {
            "name": "Composición Mixta (Hold + Waypoints + Círculo)",
            "description": "Secuencia variada: inicio estático, maniobra por puntos y órbita circular final.",
            "transition_speed": 1.0,
            "segments": [
                {
                    "type": "hold",
                    "duration": 2.0,
                    "params": {"position_W_m": [0.0, 0.0, 2.0], "yaw_rad": 0.0},
                },
                {
                    "type": "waypoint",
                    "params": {
                        "waypoints": [[0.0, 0.0, 2.0], [2.0, 2.0, 2.0], [2.0, 0.0, 2.0]],
                        "max_speed_m_s": 0.8,
                        "max_acceleration_m_s2": 0.6,
                        "waypoint_tolerance_m": 0.20,
                        "waypoint_speed_tolerance_m_s": 0.20,
                        "dwell_time_s": 0.40,
                    },
                },
                {
                    "type": "circle",
                    "duration": 8.0,
                    "params": {
                        "center_W_m": [1.0, 0.0, 2.0],
                        "radius_m": 1.2,
                        "omega_rad_s": 0.7,
                        "yaw_mode": "forward",
                        "tilt_deg": 0.0,
                    },
                },
            ],
        },
    }


def generate_initial_variant(family: str, seed: int = 42) -> Dict[str, Any]:
    """
    Genera una variante inicial válida y contenida para la familia dada,
    parametrizada de forma determinista mediante la semilla.
    """
    rng = np.random.default_rng(seed)
    fam = family.lower()

    if fam == "hold":
        alt = float(rng.choice([1.5, 2.0, 2.5, 3.0]))
        dx = float(rng.choice([-0.5, 0.0, 0.5, 1.0]))
        dy = float(rng.choice([-0.5, 0.0, 0.5]))
        yaw = float(rng.choice([0.0, np.pi / 4, -np.pi / 4]))
        return {
            "position_W_m": [dx, dy, alt],
            "yaw_rad": yaw,
            "duration": 10.0,
        }

    elif fam == "circle":
        r = float(rng.choice([1.2, 1.5, 1.8, 2.2]))
        w = float(rng.choice([0.4, 0.5, 0.6]))
        cz = float(rng.choice([1.8, 2.2, 2.5]))
        tilt = float(rng.choice([0.0, 10.0, 15.0, 20.0]))
        return {
            "center_W_m": [0.0, 0.0, cz],
            "radius_m": r,
            "omega_rad_s": w,
            "yaw_mode": "forward",
            "tilt_deg": tilt,
            "plane_yaw_deg": 0.0,
            "duration": 15.0,
        }

    elif fam == "lissajous":
        cz = float(rng.choice([2.0, 2.5, 3.0]))
        ax = float(rng.choice([1.2, 1.5, 1.8]))
        ay = float(rng.choice([1.0, 1.4, 1.6]))
        az = float(rng.choice([0.3, 0.5, 0.7]))
        wx = float(rng.choice([0.4, 0.5, 0.6]))
        wy = float(rng.choice([0.6, 0.7, 0.8]))
        if abs(wx - wy) < 1e-4:
            wy += 0.1
        wz = float(rng.choice([0.3, 0.4]))
        return {
            "center_W_m": [0.0, 0.0, cz],
            "amplitudes": [ax, ay, az],
            "omegas": [wx, wy, wz],
            "duration": 20.0,
        }

    elif fam in ("waypoint", "line"):
        wp_presets = get_waypoint_presets()
        choice_key = str(rng.choice(list(INITIAL_WAYPOINT_PRESET_KEYS)))
        preset_data = wp_presets[choice_key]
        return {
            "waypoints": preset_data["waypoints"],
            "max_speed_m_s": preset_data["max_speed_m_s"],
            "max_acceleration_m_s2": preset_data["max_acceleration_m_s2"],
            "waypoint_tolerance_m": preset_data["waypoint_tolerance_m"],
            "waypoint_speed_tolerance_m_s": preset_data["waypoint_speed_tolerance_m_s"],
            "dwell_time_s": preset_data["dwell_time_s"],
            "yaw_rad": 0.0,
        }

    elif fam == "lemniscate":
        cz = float(rng.choice([2.0, 2.5]))
        a = float(rng.choice([1.8, 2.0, 2.4]))
        b = float(round(a * 0.5, 2))
        w = float(rng.choice([0.3, 0.35, 0.45]))
        z_amp = float(rng.choice([0.0, 0.3, 0.5]))
        z_w = float(round(w, 2))
        return {
            "center_W_m": [0.0, 0.0, cz],
            "a": a,
            "b": b,
            "omega_rad_s": w,
            "z_amp": z_amp,
            "z_omega_rad_s": z_w,
            "yaw_mode": "forward",
            "duration": 18.0,
        }

    return {"position_W_m": [0.0, 0.0, 1.5], "yaw_rad": 0.0}
