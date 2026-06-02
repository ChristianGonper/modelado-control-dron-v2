"""
Generate an Out-of-Distribution (OOD) scenario battery for closed-loop neural evaluation.

Writes manifest.csv with split=ood (compatible with run_neural_outer_force_dataset.py
and run_neural_position_dataset.py). Does not mix OOD rows into train/val/test splits.
"""
import argparse
import csv
import os

import numpy as np
import yaml

from simulador_quad.scenarios.loader import instantiate_trajectory

# Base configuration constants
BASE_VEHICLE = {
    "mass_kg": 1.0,
    "inertia_B_kg_m2": [[0.05, 0.0, 0.0], [0.0, 0.05, 0.0], [0.0, 0.0, 0.1]],
    "gravity_m_s2": 9.81,
    "rotor_template": {
        "k_f": 1.0e-4,
        "k_m": 1.0e-6,
        "omega_max_rad_s": 1500.0,
    },
}

BASE_TIMING = {
    "physics_dt_s": 0.01,
    "control_dt_s": 0.02,
    "telemetry_dt_s": 0.1,
}

BASE_TERMINATION = {
    "max_duration_s": 35.0,
    "z_min_m": 0.0,
    "max_attitude_angle_rad": 1.256,
    "max_saturation_duration_s": 2.0,
}


def get_rotors(time_constant_s: float, delay_s: float):
    positions = [
        [0.17, 0.17, 0.0],
        [0.17, -0.17, 0.0],
        [-0.17, 0.17, 0.0],
        [-0.17, -0.17, 0.0],
    ]
    directions = [-1, 1, 1, -1]
    rotors = []
    for pos, direct in zip(positions, directions):
        r = BASE_VEHICLE["rotor_template"].copy()
        r["position_B_m"] = pos
        r["turning_direction"] = direct
        r["time_constant_s"] = time_constant_s
        r["delay_s"] = delay_s
        rotors.append(r)
    return rotors


def get_initial_state(trajectory_cfg):
    traj = instantiate_trajectory(trajectory_cfg)
    ref0 = traj.get_reference(0.0)
    return {
        "position_W_m": ref0.position_W_m.tolist(),
        "velocity_W_m_s": [0.0, 0.0, 0.0],
        "orientation_WB": None,
        "yaw_rad": float(ref0.yaw_rad),
        "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
    }


def _build_scenario_definitions():
    """Return the list of OOD scenario definition dicts."""
    s1_traj = {
        "type": "lemniscate",
        "center_W_m": [0.0, 0.0, 2.5],
        "a": 2.0,
        "b": 1.0,
        "omega_rad_s": 0.35,
        "z_amp": 0.6,
        "z_omega_rad_s": 0.35,
        "yaw_mode": "forward",
        "warmup_s": 3.0,
    }

    s2_traj = {
        "type": "lemniscate",
        "center_W_m": [0.0, 0.0, 2.0],
        "a": 2.5,
        "b": 1.25,
        "omega_rad_s": 0.5,
        "z_amp": 0.0,
        "yaw_mode": "fixed",
        "warmup_s": 3.0,
    }

    s3_traj = {
        "type": "lemniscate",
        "center_W_m": [0.0, 0.0, 2.0],
        "a": 1.8,
        "b": 0.9,
        "omega_rad_s": 0.3,
        "z_amp": 0.4,
        "z_omega_rad_s": 0.6,
        "yaw_mode": "forward",
        "warmup_s": 3.0,
    }

    s4_traj = {
        "type": "lissajous",
        "center_W_m": [0.0, 0.0, 3.0],
        "amplitudes": [2.0, 1.5, 0.8],
        "omegas": [0.6, 0.9, 0.45],
    }

    s5_traj = {
        "type": "lissajous",
        "center_W_m": [0.0, 0.0, 2.5],
        "amplitudes": [1.5, 1.5, 0.5],
        "omegas": [0.4, 0.5, 0.3],
    }

    s6_traj = {
        "type": "composite",
        "transition_speed": 0.5,
        "sequence": [
            {"type": "hold", "position_W_m": [0.0, 0.0, 1.5], "duration": 3.0, "yaw_rad": 0.0},
            {
                "type": "circle",
                "center_W_m": [0.0, 0.0, 1.5],
                "radius_m": 1.5,
                "omega_rad_s": 0.6,
                "duration": 10.0,
                "yaw_mode": "forward",
            },
            {
                "type": "lemniscate",
                "center_W_m": [1.5, 0.0, 2.0],
                "a": 1.2,
                "b": 0.6,
                "omega_rad_s": 0.4,
                "z_amp": 0.0,
                "duration": 15.0,
                "yaw_mode": "forward",
            },
        ],
    }

    s7_traj = {
        "type": "composite",
        "transition_speed": 1.0,
        "sequence": [
            {"type": "hold", "position_W_m": [0.0, 0.0, 2.0], "duration": 2.0},
            {
                "type": "waypoint",
                "waypoints": [[0.0, 0.0, 2.0], [2.0, 2.0, 2.0], [2.0, 0.0, 2.0]],
                "max_speed_m_s": 0.8,
                "max_acceleration_m_s2": 0.6,
                "waypoint_tolerance_m": 0.2,
                "waypoint_speed_tolerance_m_s": 0.2,
                "dwell_time_s": 0.4,
                "duration": 8.0,
            },
            {
                "type": "circle",
                "center_W_m": [1.0, 1.0, 2.0],
                "radius_m": 1.0,
                "omega_rad_s": 0.8,
                "duration": 8.0,
                "yaw_mode": "forward",
            },
        ],
    }

    theta = np.linspace(0, 4 * np.pi, 9)
    s8_wps = [
        [float(2.0 * np.cos(t)), float(2.0 * np.sin(t)), float(1.0 + 3.0 * t / (4.0 * np.pi))]
        for t in theta
    ]
    s8_traj = {
        "type": "waypoint",
        "waypoints": s8_wps,
        "max_speed_m_s": 0.8,
        "max_acceleration_m_s2": 0.6,
        "waypoint_tolerance_m": 0.2,
        "waypoint_speed_tolerance_m_s": 0.2,
        "dwell_time_s": 0.4,
    }

    theta9 = np.linspace(0, 3 * np.pi, 8)
    s9_wps = [
        [float(1.5 * np.cos(t)), float(1.5 * np.sin(t)), float(4.0 - 3.0 * t / (3.0 * np.pi))]
        for t in theta9
    ]
    s9_traj = {
        "type": "waypoint",
        "waypoints": s9_wps,
        "max_speed_m_s": 0.6,
        "max_acceleration_m_s2": 0.4,
        "waypoint_tolerance_m": 0.2,
        "waypoint_speed_tolerance_m_s": 0.2,
        "dwell_time_s": 0.4,
    }

    theta10 = np.linspace(0, 6 * np.pi, 12)
    s10_wps = [
        [float(0.8 * np.cos(t)), float(0.8 * np.sin(t)), float(1.0 + 4.0 * t / (6.0 * np.pi))]
        for t in theta10
    ]
    s10_traj = {
        "type": "waypoint",
        "waypoints": s10_wps,
        "max_speed_m_s": 1.0,
        "max_acceleration_m_s2": 0.8,
        "waypoint_tolerance_m": 0.2,
        "waypoint_speed_tolerance_m_s": 0.2,
        "dwell_time_s": 0.4,
    }

    return [
        {
            "id": "lemniscate_3d_heavy_wind",
            "family": "lemniscate",
            "trajectory": s1_traj,
            "perturbations": {"constant_wind_W_m_s": [2.5, 1.5, 0.4], "pos_std_m": 0.0, "vel_std_m_s": 0.0},
            "drag": [0.1, 0.1, 0.05],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2001,
        },
        {
            "id": "lemniscate_fast_center_yaw",
            "family": "lemniscate",
            "trajectory": s2_traj,
            "perturbations": {"constant_wind_W_m_s": [0.0, 0.0, 0.0], "pos_std_m": 0.0, "vel_std_m_s": 0.0},
            "drag": [0.1, 0.1, 0.05],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2002,
        },
        {
            "id": "lemniscate_combined_extreme",
            "family": "lemniscate",
            "trajectory": s3_traj,
            "perturbations": {
                "constant_wind_W_m_s": [2.0, 1.0, 0.2],
                "pos_std_m": 0.08,
                "vel_std_m_s": 0.12,
            },
            "drag": [0.3, 0.3, 0.15],
            "actuators": {"time_constant_s": 0.07, "delay_s": 0.02},
            "seed": 2003,
        },
        {
            "id": "lissajous_3d_speedy",
            "family": "lissajous",
            "trajectory": s4_traj,
            "perturbations": {"constant_wind_W_m_s": [1.2, 0.8, -0.3], "pos_std_m": 0.0, "vel_std_m_s": 0.0},
            "drag": [0.15, 0.15, 0.08],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2004,
        },
        {
            "id": "lissajous_extreme_noise",
            "family": "lissajous",
            "trajectory": s5_traj,
            "perturbations": {"constant_wind_W_m_s": [0.0, 0.0, 0.0], "pos_std_m": 0.12, "vel_std_m_s": 0.20},
            "drag": [0.1, 0.1, 0.05],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2005,
        },
        {
            "id": "composite_circle_to_lemniscate",
            "family": "composite",
            "trajectory": s6_traj,
            "perturbations": {"constant_wind_W_m_s": [1.0, 1.0, 0.0], "pos_std_m": 0.0, "vel_std_m_s": 0.0},
            "drag": [0.1, 0.1, 0.05],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2006,
        },
        {
            "id": "composite_aggressive_transitions",
            "family": "composite",
            "trajectory": s7_traj,
            "perturbations": {"constant_wind_W_m_s": [1.8, -1.0, 0.2], "pos_std_m": 0.0, "vel_std_m_s": 0.0},
            "drag": [0.25, 0.25, 0.12],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2007,
        },
        {
            "id": "helix_ascending_fast",
            "family": "waypoint",
            "trajectory": s8_traj,
            "perturbations": {"constant_wind_W_m_s": [1.5, 1.5, 0.0], "pos_std_m": 0.0, "vel_std_m_s": 0.0},
            "drag": [0.1, 0.1, 0.05],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2008,
        },
        {
            "id": "helix_descending_noise_wind",
            "family": "waypoint",
            "trajectory": s9_traj,
            "perturbations": {
                "constant_wind_W_m_s": [2.0, 0.0, -0.5],
                "pos_std_m": 0.08,
                "vel_std_m_s": 0.12,
            },
            "drag": [0.2, 0.2, 0.1],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2009,
        },
        {
            "id": "helix_tight_aggressive",
            "family": "waypoint",
            "trajectory": s10_traj,
            "perturbations": {"constant_wind_W_m_s": [2.5, -2.0, 0.3], "pos_std_m": 0.0, "vel_std_m_s": 0.0},
            "drag": [0.3, 0.3, 0.15],
            "actuators": {"time_constant_s": 0.03, "delay_s": 0.01},
            "seed": 2010,
        },
    ]


def generate_battery(out_dir: str, scenario_ids: list[str] | None = None) -> int:
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "scenarios"), exist_ok=True)

    dummy_pid = {
        "Kp_pos": [2.0, 2.0, 5.0],
        "Kd_pos": [1.0, 1.0, 2.0],
        "Kp_att": [4.0, 4.0, 1.0],
        "Kd_att": [1.5, 1.5, 0.5],
    }

    scenarios = _build_scenario_definitions()
    if scenario_ids:
        scenarios = [sc for sc in scenarios if sc["id"] in scenario_ids]
        if not scenarios:
            raise ValueError(f"No matching scenario ids in {scenario_ids}")

    manifest_rows = []

    for sc in scenarios:
        sc_id = sc["id"]
        family = sc["family"]

        config = {
            "name": sc_id,
            "seed": sc["seed"],
            "vehicle": {
                "mass_kg": BASE_VEHICLE["mass_kg"],
                "inertia_B_kg_m2": BASE_VEHICLE["inertia_B_kg_m2"],
                "gravity_m_s2": BASE_VEHICLE["gravity_m_s2"],
                "linear_drag_coefficient": sc["drag"],
                "rotors": get_rotors(sc["actuators"]["time_constant_s"], sc["actuators"]["delay_s"]),
            },
            "initial_state": get_initial_state(sc["trajectory"]),
            "trajectory": sc["trajectory"],
            "controller": {"type": "classic", **dummy_pid},
            "perturbations": sc["perturbations"],
            "timing": BASE_TIMING,
            "termination": BASE_TERMINATION,
            "output": {
                "dir": f"results/{sc_id}",
                "telemetry_file": "telemetry.json",
                "metrics_file": "metrics.json",
            },
        }

        family_dir = os.path.join(out_dir, "scenarios", family)
        os.makedirs(family_dir, exist_ok=True)
        scenario_yaml_path = os.path.join(family_dir, f"{sc_id}.yaml")
        with open(scenario_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, sort_keys=False)

        rel_scenario_path = os.path.relpath(scenario_yaml_path, out_dir)
        rel_result_dir = os.path.relpath(os.path.join(out_dir, "results", sc_id), out_dir)

        manifest_rows.append(
            {
                "scenario_id": sc_id,
                "family": family,
                "split": "ood",
                "scenario_path": rel_scenario_path,
                "result_dir": rel_result_dir,
            }
        )

    manifest_path = os.path.join(out_dir, "manifest.csv")
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["scenario_id", "family", "split", "scenario_path", "result_dir"]
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    readme_path = os.path.join(out_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# OOD Evaluation Battery\n\n")
        f.write("Generated for Out-of-Distribution closed-loop testing (`split=ood`).\n")
        f.write("Do not merge this manifest into train/val/test supervised splits.\n\n")
        f.write("Regenerate with:\n\n")
        f.write("```powershell\n")
        f.write("uv run python tools/generate_ood_battery.py --out data/neural_ood/battery_v1 --overwrite\n")
        f.write("```\n\n")
        f.write("`manifest.result_dir` and each scenario `output.dir` both use `results/<scenario_id>` ")
        f.write("(paths relative to this battery root).\n\n")
        f.write("Supervised `evaluate_neural_controller.py --ood-dataset` requires telemetry under ")
        f.write("`result_dir`; use `run_neural_outer_force_dataset.py` for scenario-only batteries.\n\n")
        f.write(f"Total scenarios: {len(manifest_rows)}\n")

    return len(manifest_rows)


def main():
    parser = argparse.ArgumentParser(
        description="Generate OOD scenario battery (manifest split=ood) for neural closed-loop evaluation."
    )
    parser.add_argument(
        "--out",
        type=str,
        default="data/neural_ood/battery_v1",
        help="Output dataset root (manifest.csv + scenarios/).",
    )
    parser.add_argument(
        "--scenario-id",
        action="append",
        dest="scenario_ids",
        help="Generate only these scenario ids (repeatable). Default: all 10 scenarios.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing into an existing output directory.",
    )
    args = parser.parse_args()

    if os.path.exists(args.out) and os.listdir(args.out) and not args.overwrite:
        raise FileExistsError(f"{args.out} exists and is non-empty. Use --overwrite to replace.")

    count = generate_battery(args.out, scenario_ids=args.scenario_ids)
    print(f"Generated {count} OOD scenarios at {args.out}")


if __name__ == "__main__":
    main()