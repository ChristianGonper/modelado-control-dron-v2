import os
import yaml
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
from simulador_quad.core.fs import atomic_write_directory
from simulador_quad.scenarios.loader import instantiate_trajectory

# --- Constants v1 ---

FAMILIES = ["hold", "circle", "lissajous", "waypoint"]

INITIAL_PIDS = {
    "hold": {"Kp_pos": [2.0, 2.0, 5.0], "Kd_pos": [1.0, 1.0, 2.0], "Kp_att": [4.0, 4.0, 1.0], "Kd_att": [1.5, 1.5, 0.5]},
    "circle": {"Kp_pos": [2.0, 2.0, 5.0], "Kd_pos": [1.0, 1.0, 2.0], "Kp_att": [4.0, 4.0, 1.0], "Kd_att": [1.5, 1.5, 0.5]},
    "lissajous": {"Kp_pos": [2.0, 2.0, 5.0], "Kd_pos": [1.0, 1.0, 2.0], "Kp_att": [4.0, 4.0, 1.0], "Kd_att": [1.5, 1.5, 0.5]},
    "waypoint": {
        "Kp_pos": [2.0, 2.0, 5.0],
        "Kd_pos": [1.2, 1.2, 2.4],
        "Kp_att": [4.8, 4.8, 1.2],
        "Kd_att": [1.2, 1.2, 0.4],
    }
}

DIAGNOSTIC_PROFILES = ["P0_nominal", "P2_wind_east", "P5_combined"]

SLOW_DEMANDING_GEOM = {
    "hold": ("g01", "g06"),
    "circle": ("g01", "g08"),
    "lissajous": ("g01", "g08"),
    "waypoint": ("g01", "g06"),
}

PROFILES = {
    "P0_nominal": {
        "drag": [0.10, 0.10, 0.05],
        "wind": [0.0, 0.0, 0.0],
        "pos_std": 0.0,
        "vel_std": 0.0,
        "actuators": {"time_constant_s": 0.03, "delay_s": 0.01}
    },
    "P1_drag_high": {
        "drag": [0.20, 0.20, 0.10],
        "wind": [0.0, 0.0, 0.0],
        "pos_std": 0.0,
        "vel_std": 0.0,
        "actuators": {"time_constant_s": 0.03, "delay_s": 0.01}
    },
    "P2_wind_east": {
        "drag": [0.10, 0.10, 0.05],
        "wind": [1.0, 0.0, 0.0],
        "pos_std": 0.0,
        "vel_std": 0.0,
        "actuators": {"time_constant_s": 0.03, "delay_s": 0.01}
    },
    "P3_wind_ne": {
        "drag": [0.10, 0.10, 0.05],
        "wind": [1.0, 1.0, 0.0],
        "pos_std": 0.0,
        "vel_std": 0.0,
        "actuators": {"time_constant_s": 0.03, "delay_s": 0.01}
    },
    "P4_noise_low": {
        "drag": [0.10, 0.10, 0.05],
        "wind": [0.0, 0.0, 0.0],
        "pos_std": 0.02,
        "vel_std": 0.03,
        "actuators": {"time_constant_s": 0.03, "delay_s": 0.01}
    },
    "P5_combined": {
        "drag": [0.20, 0.20, 0.10],
        "wind": [1.5, 1.0, 0.0],
        "pos_std": 0.05,
        "vel_std": 0.08,
        "actuators": {"time_constant_s": 0.05, "delay_s": 0.02}
    }
}

BASE_VEHICLE = {
    "mass_kg": 1.0,
    "inertia_B_kg_m2": [[0.05, 0, 0], [0, 0.05, 0], [0, 0, 0.1]],
    "gravity_m_s2": 9.81,
    "rotor_template": {
        "k_f": 1.0e-4,
        "k_m": 1.0e-6,
        "omega_max_rad_s": 1500.0
    }
}

BASE_TIMING = {
    "physics_dt_s": 0.01,
    "control_dt_s": 0.02,
    "telemetry_dt_s": 0.1
}

BASE_TERMINATION = {
    "max_duration_s": 45.0, # Sufficient for all families
    "z_min_m": 0.0,
    "max_attitude_angle_rad": 1.256, # ~72 deg
    "max_saturation_duration_s": 2.0
}

WAYPOINT_TERMINATION = {
    **BASE_TERMINATION,
    "max_duration_s": 60.0,
}

WAYPOINT_STOP_DEFAULTS = {
    "max_speed_m_s": 0.6,
    "max_acceleration_m_s2": 0.5,
    "waypoint_tolerance_m": 0.20,
    "waypoint_speed_tolerance_m_s": 0.20,
    "dwell_time_s": 0.40,
}

# --- Helper Functions ---

def build_pid_id(family: str, version: str) -> str:
    return f"pid_{family}_{version}"

def build_scenario_id(family: str, geometry_id: str, perturbation_id: str, seed: int) -> str:
    return f"{family}_{geometry_id}_{perturbation_id}_s{seed}"

def get_base_rotors(actuators: Dict[str, float]) -> List[Dict[str, Any]]:
    positions = [
        [0.17, 0.17, 0], [0.17, -0.17, 0], [-0.17, 0.17, 0], [-0.17, -0.17, 0]
    ]
    directions = [-1, 1, 1, -1]
    rotors = []
    for pos, direct in zip(positions, directions):
        r = BASE_VEHICLE["rotor_template"].copy()
        r["position_B_m"] = pos
        r["turning_direction"] = direct
        r["time_constant_s"] = actuators["time_constant_s"]
        r["delay_s"] = actuators["delay_s"]
        rotors.append(r)
    return rotors

def initial_state_from_trajectory_config(trajectory_cfg: Dict[str, Any]) -> Dict[str, Any]:
    trajectory = instantiate_trajectory(trajectory_cfg)
    ref0 = trajectory.get_reference(0.0)
    return {
        "position_W_m": ref0.position_W_m.tolist(),
        "velocity_W_m_s": [0.0, 0.0, 0.0],
        "orientation_WB": None,
        "yaw_rad": float(ref0.yaw_rad),
        "angular_velocity_B_rad_s": [0.0, 0.0, 0.0],
    }

def build_scenario_config(
    scenario_id: str,
    family: str,
    trajectory_cfg: Dict[str, Any],
    profile_id: str,
    pid_config: Dict[str, Any],
    seed: int,
    output_root: str
) -> Dict[str, Any]:
    profile = PROFILES[profile_id]

    config = {
        "name": scenario_id,
        "seed": seed,
        "vehicle": {
            "mass_kg": BASE_VEHICLE["mass_kg"],
            "inertia_B_kg_m2": BASE_VEHICLE["inertia_B_kg_m2"],
            "gravity_m_s2": BASE_VEHICLE["gravity_m_s2"],
            "linear_drag_coefficient": profile["drag"],
            "rotors": get_base_rotors(profile["actuators"])
        },
        "initial_state": initial_state_from_trajectory_config(trajectory_cfg),
        "trajectory": trajectory_cfg,
        "controller": {
            "type": "classic",
            **pid_config
        },
        "perturbations": {
            "constant_wind_W_m_s": profile["wind"],
            "pos_std_m": profile["pos_std"],
            "vel_std_m_s": profile["vel_std"]
        },
        "timing": BASE_TIMING,
        "termination": WAYPOINT_TERMINATION if family == "waypoint" else BASE_TERMINATION,
        "output": {
            "dir": os.path.join(output_root, "results", family, scenario_id),
            "telemetry_file": "telemetry.json",
            "metrics_file": "metrics.json"
        }
    }
    return config

# --- Dataset Specification v1 ---

def get_geometry_variants(family: str) -> List[Tuple[str, Dict[str, Any]]]:
    if family == "hold":
        # 6 refs: (id, cfg)
        variants = []
        altitudes = [1.5, 2.0, 3.0]
        offsets = [[0,0], [1,0], [0,1]] # [x,y]
        yaws = [0.0, np.pi/4]

        idx = 1
        # representation of the spec
        for z in altitudes:
            for xy in offsets[0:1]: # centered
                variants.append((f"g{idx:02d}", {"type": "hold", "position_W_m": [float(xy[0]), float(xy[1]), z], "yaw_rad": float(yaws[0])}))
                idx += 1
        # Add a yaw variant for centered hold
        for xy in offsets[0:1]:
            variants.append((f"g{idx:02d}", {"type": "hold", "position_W_m": [float(xy[0]), float(xy[1]), altitudes[1]], "yaw_rad": float(yaws[1])}))
            idx += 1
        for xy in offsets[1:]:
            variants.append((f"g{idx:02d}", {"type": "hold", "position_W_m": [float(xy[0]), float(xy[1]), altitudes[1]], "yaw_rad": float(yaws[1])}))
            idx += 1
        return variants[:6]

    elif family == "circle":
        # 8 geometry variants
        variants = []
        radii = [1.0, 1.5, 2.0, 2.5]
        omegas = [0.35, 0.5, 0.65]
        heights = [2.0, 3.0, 4.0]

        # Representative configurations
        idx = 1
        combos = [
            (radii[1], omegas[1], heights[0]), (radii[1], omegas[0], heights[1]),
            (radii[2], omegas[1], heights[1]), (radii[0], omegas[2], heights[0]),
            (radii[3], omegas[0], heights[2]), (radii[0], omegas[0], heights[0]),
            (radii[2], omegas[2], heights[1]), (radii[1], omegas[2], heights[2])
        ]
        for r, w, h in combos:
            variants.append((f"g{idx:02d}", {
                "type": "circle", "center_W_m": [0.0, 0.0, h], "radius_m": r, "omega_rad_s": w, "yaw_mode": "forward"
            }))
            idx += 1
        return variants

    elif family == "lissajous":
        # 8 geometry variants
        variants = []
        amplitudes = [
            [1.5, 1.5, 0.5], [1.0, 2.0, 0.3], [2.5, 1.0, 0.7], [2.0, 2.0, 0.5],
            [1.2, 1.2, 0.2], [0.8, 0.8, 0.8], [2.0, 0.5, 0.4], [1.5, 2.5, 0.6]
        ]
        omegas = [
            [0.5, 0.7, 0.3], [0.4, 0.6, 0.2], [0.3, 0.5, 0.4], [0.5, 0.5, 0.5],
            [0.6, 0.8, 0.4], [0.3, 0.3, 0.3], [0.4, 0.9, 0.5], [0.7, 0.4, 0.2]
        ]
        centers = [
            [0, 0, 2.5], [0, 0, 3.0], [0, 0, 2.0], [1, 1, 3.0],
            [0, 0, 2.5], [0, 0, 3.5], [0, 0, 2.2], [0, 0, 2.8]
        ]

        idx = 1
        # Avoid identical frequencies to avoid degenerate paths
        for amps, oms, center in zip(amplitudes, omegas, centers):
            # Ensure omegas are not identical
            if oms[0] == oms[1]: oms[1] += 0.01
            variants.append((f"g{idx:02d}", {
                "type": "lissajous", "center_W_m": center, "amplitudes": amps, "omegas": oms
            }))
            idx += 1
        return variants

    elif family == "waypoint":
        # 6 waypoint_stop missions. The legacy `times` field is intentionally
        # not generated: waypoint progression is governed by position, speed
        # and dwell criteria inside the trajectory.
        names = ["square", "rect", "zigzag", "stairs", "diag3d", "closed"]
        waypoints = [
            [[0,0,2], [2,0,2], [2,2,2], [0,2,2], [0,0,2]],
            [[0,0,2], [3,0,2], [3,1,2], [0,1,2], [0,0,2]],
            [[0,0,2], [1,1,2], [2,0,2], [3,1,2], [4,0,2]],
            [[0,0,1], [1,0,1.5], [2,0,2], [3,0,2.5], [4,0,3]],
            [[0,0,1], [2,2,3]],
            [[0,0,2], [1,1,3], [0,2,2], [-1,1,3], [0,0,2]]
        ]

        variants = []
        for i, (name, wp) in enumerate(zip(names, waypoints)):
            variants.append((f"g{i+1:02d}", {
                "type": "waypoint",
                "waypoints": wp,
                **WAYPOINT_STOP_DEFAULTS,
            }))
        return variants

    return []

def get_dataset_manifest_data(version: str = "v1") -> List[Dict[str, Any]]:
    manifest = []
    base_seed = 1042

    family_splits = {
        "hold": ["train"] * 12 + ["val"] * 3 + ["test"] * 3,
        "circle": ["train"] * 34 + ["val"] * 7 + ["test"] * 7,
        "lissajous": ["train"] * 34 + ["val"] * 7 + ["test"] * 7,
        "waypoint": ["train"] * 25 + ["val"] * 5 + ["test"] * 6
    }

    rng = np.random.RandomState(base_seed)

    for family in FAMILIES:
        geometries = get_geometry_variants(family)
        slow_g, demand_g = SLOW_DEMANDING_GEOM[family]

        if family == "hold":
            profiles_to_use = ["P0_nominal", "P2_wind_east", "P5_combined"]
        else:
            profiles_to_use = list(PROFILES.keys())

        scenarios = []
        for g_id, g_cfg in geometries:
            for p_id in profiles_to_use:
                is_diag = (g_id in (slow_g, demand_g)) and (p_id in DIAGNOSTIC_PROFILES)
                scenarios.append({
                    "g_id": g_id,
                    "g_cfg": g_cfg,
                    "p_id": p_id,
                    "is_diag": is_diag
                })

        diag_scenarios = [s for s in scenarios if s["is_diag"]]
        n_diag = len(diag_scenarios)

        total_train = family_splits[family].count("train")
        total_val = family_splits[family].count("val")
        total_test = family_splits[family].count("test")

        diag_splits = ["train"] * n_diag
        non_diag_splits = ["train"] * (total_train - n_diag) + ["val"] * total_val + ["test"] * total_test

        rng.shuffle(non_diag_splits)

        diag_idx = 0
        non_diag_idx = 0
        for s in scenarios:
            if s["is_diag"]:
                s["split"] = diag_splits[diag_idx]
                diag_idx += 1
            else:
                s["split"] = non_diag_splits[non_diag_idx]
                non_diag_idx += 1

        for s in scenarios:
            seed = base_seed + len(manifest)
            scenario_id = build_scenario_id(family, s["g_id"], s["p_id"], seed)

            manifest.append({
                "scenario_id": scenario_id,
                "family": family,
                "geometry_id": s["g_id"],
                "perturbation_id": s["p_id"],
                "pid_id": build_pid_id(family, version),
                "seed": seed,
                "split": s["split"],
                "trajectory_cfg": s["g_cfg"]
            })

    return manifest

def write_dataset_files(version: str, output_root: str, overwrite: bool = False, reset_pids: bool = False):
    if os.path.exists(output_root) and not overwrite:
        raise FileExistsError(f"Directory {output_root} already exists. Use overwrite=True to force.")

    # Read existing gains if they exist (before entering atomic write)
    existing_pid_configs = {}
    for family in FAMILIES:
        pid_id = build_pid_id(family, version)
        pid_path = os.path.join(output_root, "pids", f"{pid_id}.yaml")
        if os.path.exists(pid_path) and not reset_pids:
            try:
                with open(pid_path, 'r') as f:
                    pid_all = yaml.safe_load(f)
                    pid_fields = ["Kp_pos", "Kd_pos", "Kp_att", "Kd_att", "max_body_moments_Nm"]
                    existing_pid_configs[family] = {k: pid_all[k] for k in pid_fields if k in pid_all}
            except Exception:
                pass

    manifest_data = get_dataset_manifest_data(version=version)

    def write_dataset(temp_dir):
        os.makedirs(os.path.join(temp_dir, "pids"), exist_ok=True)
        pid_configs = {}
        for family in FAMILIES:
            pid_id = build_pid_id(family, version)
            pid_path = os.path.join(temp_dir, "pids", f"{pid_id}.yaml")

            # Reuse existing if we read it successfully
            if family in existing_pid_configs:
                pid_data = {
                    "pid_id": pid_id,
                    "family": family,
                    "version": version,
                    "source": "restored_existing",
                    **existing_pid_configs[family]
                }
            else:
                pid_data = {
                    "pid_id": pid_id,
                    "family": family,
                    "version": version,
                    "source": "default_initial",
                    **INITIAL_PIDS[family]
                }

            with open(pid_path, 'w') as f:
                yaml.dump(pid_data, f, sort_keys=False)

            pid_fields = ["Kp_pos", "Kd_pos", "Kp_att", "Kd_att", "max_body_moments_Nm"]
            pid_configs[family] = {k: pid_data[k] for k in pid_fields if k in pid_data}

        # Write scenarios
        for row in manifest_data:
            family_dir = os.path.join(temp_dir, "scenarios", row["family"])
            os.makedirs(family_dir, exist_ok=True)

            pid_config = pid_configs[row["family"]]

            scenario_config = build_scenario_config(
                row["scenario_id"], row["family"], row["trajectory_cfg"],
                row["perturbation_id"], pid_config, row["seed"], output_root
            )

            yaml_path = os.path.join(family_dir, f"{row['scenario_id']}.yaml")
            with open(yaml_path, 'w') as f:
                yaml.dump(scenario_config, f, sort_keys=False)

            row["scenario_path"] = os.path.relpath(yaml_path, temp_dir)
            row["result_dir"] = os.path.relpath(scenario_config["output"]["dir"], output_root)

        # Write manifest.csv
        import csv
        manifest_csv = os.path.join(temp_dir, "manifest.csv")
        with open(manifest_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "scenario_id", "family", "geometry_id", "perturbation_id",
                "pid_id", "seed", "split", "scenario_path", "result_dir"
            ])
            writer.writeheader()
            for row in manifest_data:
                # Filter keys for CSV
                writer.writerow({k: row[k] for k in writer.fieldnames})

        # Write README.md
        with open(os.path.join(temp_dir, "README.md"), 'w') as f:
            f.write(f"# Classic Dataset {version}\n\nGenerated automatically.\nTotal episodes: {len(manifest_data)}\n")

    atomic_write_directory(output_root, write_dataset, overwrite)

# --- PID Selection / Scoring ---

def attitude_rms_rad_from_telemetry(telemetry: List[Any]) -> float:
    from simulador_quad.core.attitude import quaternion_to_euler_enu_frd
    rolls, pitches, yaws = [], [], []
    for sample in telemetry:
        r, p, y = quaternion_to_euler_enu_frd(sample.state.orientation_WB)
        rolls.append(r)
        pitches.append(p)
        yaws.append(y)

    rolls = np.array(rolls)
    pitches = np.array(pitches)
    yaws = np.array(yaws)

    norm_sq = rolls**2 + pitches**2 + yaws**2
    return float(np.sqrt(np.mean(norm_sq)))

def pid_candidate_score(metrics: Dict[str, Any], telemetry: List[Any], family: str) -> float:
    # Check for finite values to avoid NaN scores
    required_metrics = [
        "position_rmse_m", "position_max_err_m", "saturation_percentage",
        "degradation_percentage", "collective_thrust_mean_N", "body_moment_norm_mean_Nm"
    ]
    for k in required_metrics:
        if not np.isfinite(metrics.get(k, np.nan)):
            return 1e9 # Penalty for non-finite metrics

    pos_rmse = metrics["position_rmse_m"]
    pos_max = metrics["position_max_err_m"]
    att_rms = attitude_rms_rad_from_telemetry(telemetry)

    # Normalized control effort
    weight_N = BASE_VEHICLE["mass_kg"] * BASE_VEHICLE["gravity_m_s2"]
    moment_scale_Nm = 0.1

    effort_thrust = metrics["collective_thrust_mean_N"] / weight_N
    effort_moment = metrics["body_moment_norm_mean_Nm"] / moment_scale_Nm
    effort_norm = effort_thrust + effort_moment

    sat_frac = metrics["saturation_percentage"] / 100.0
    deg_frac = metrics["degradation_percentage"] / 100.0

    score = (
        1.00 * pos_rmse +
        0.50 * pos_max +
        0.20 * att_rms +
        0.10 * effort_norm +
        2.00 * sat_frac +
        2.00 * deg_frac
    )
    return float(score)

def passes_hard_filters(metrics: Dict[str, Any], family: str) -> Tuple[bool, str]:
    # Check for finite values first for ALL metrics used in score or filters
    required_metrics = [
        "position_rmse_m", "position_max_err_m", "saturation_percentage",
        "degradation_percentage", "collective_thrust_mean_N", "body_moment_norm_mean_Nm"
    ]
    for k in required_metrics:
        val = metrics.get(k)
        if val is None or not np.isfinite(val):
            return False, f"Non-finite or missing metric: {k}"

    from simulador_quad.metrics.success import is_control_success

    if not is_control_success(metrics["termination_reason"], family=family):
        return False, f"Invalid termination: {metrics['termination_reason']}"

    if metrics["saturation_percentage"] > 2.0:
        return False, f"Saturation too high: {metrics['saturation_percentage']:.2f}%"

    if metrics["degradation_percentage"] > 2.0:
        return False, f"Degradation too high: {metrics['degradation_percentage']:.2f}%"

    limits = {
        "hold": 0.40,
        "circle": 0.75,
        "lissajous": 0.90,
        "waypoint": 0.80
    }
    if metrics["position_max_err_m"] > limits.get(family, 1.0):
        return False, f"Max position error too high: {metrics['position_max_err_m']:.2f} m"

    return True, "OK"


# --- PID tuning / diagnostic support ---


def get_diagnostic_cases(dataset_root: str) -> Dict[str, List[Dict[str, Any]]]:
    """Build the fixed diagnostic set: only train split rows.
    Per family: the two chosen geoms + the three DIAGNOSTIC_PROFILES.
    Returns {family: [case_dict, ...]} where case has keys for build_scenario_config + seed/split info.
    Selection is deterministic (no shuffle).
    """
    import csv
    manifest_path = os.path.join(dataset_root, "manifest.csv")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found for diagnostic set: {manifest_path}")
    rows_by_key = {}
    with open(manifest_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["split"] != "train":
                continue
            key = (row["family"], row["geometry_id"], row["perturbation_id"])
            rows_by_key[key] = row

    cases: Dict[str, List[Dict[str, Any]]] = {f: [] for f in FAMILIES}
    for family in FAMILIES:
        slow_g, demand_g = SLOW_DEMANDING_GEOM[family]
        for g in (slow_g, demand_g):
            for p in DIAGNOSTIC_PROFILES:
                key = (family, g, p)
                if key not in rows_by_key:
                    # For hold only 3 profs are generated; skip missing combinations gracefully
                    # (non-hold should have P0/P2/P5 in their train rows)
                    continue
                r = rows_by_key[key]
                # Reconstruct trajectory_cfg from geometry_id (manifest csv does not embed full dict)
                geoms = {gg[0]: gg[1] for gg in get_geometry_variants(family)}
                tcfg = geoms.get(g, geoms[list(geoms.keys())[0]])
                cases[family].append({
                    "family": family,
                    "geometry_id": g,
                    "perturbation_id": p,
                    "trajectory_cfg": tcfg,
                    "seed": int(r["seed"]),
                    "scenario_id": r["scenario_id"],
                })
        # Fallback for unit tests / minimal manifests without the exact (g,p) rows: synthesize
        if not cases[family]:
            geoms = {gg[0]: gg[1] for gg in get_geometry_variants(family)}
            for g in (slow_g, demand_g):
                if g not in geoms:
                    g = list(geoms.keys())[0]
                tcfg = geoms[g]
                for p in DIAGNOSTIC_PROFILES:
                    if p in PROFILES:
                        cases[family].append({
                            "family": family,
                            "geometry_id": g,
                            "perturbation_id": p,
                            "trajectory_cfg": tcfg,
                            "seed": 1042 + len(cases[family]),
                            "scenario_id": f"{family}_{g}_{p}_s{1042}",
                        })
    return cases


def aggregate_diagnostic(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-case results into mean_rmse, mean_score, hard_fails count, effort etc.
    results: list of {'metrics':, 'score':, 'passed': bool, 'reason':, 'effort':? }
    """
    if not results:
        return {"mean_rmse": float("inf"), "mean_score": float("inf"), "hard_fails": 999, "n_cases": 0}
    rmses = [r["metrics"]["position_rmse_m"] for r in results if "metrics" in r and np.isfinite(r["metrics"].get("position_rmse_m", np.nan))]
    scores = [r.get("score", 1e9) for r in results]
    passed = [r.get("passed", False) for r in results]
    hard_fails = sum(1 for p in passed if not p)
    # effort proxy from first valid or mean of available
    efforts = []
    for r in results:
        m = r.get("metrics", {})
        if m:
            w = BASE_VEHICLE["mass_kg"] * BASE_VEHICLE["gravity_m_s2"]
            e = (m.get("collective_thrust_mean_N", 0)/w) + (m.get("body_moment_norm_mean_Nm", 0)/0.1)
            efforts.append(e)
    mean_effort = float(np.mean(efforts)) if efforts else 1e9
    return {
        "mean_rmse": float(np.mean(rmses)) if rmses else float("inf"),
        "mean_score": float(np.mean(scores)) if scores else float("inf"),
        "hard_fails": hard_fails,
        "n_cases": len(results),
        "mean_effort": mean_effort,
        "all_passed": all(passed),
    }


def needs_tuning(agg: Dict[str, Any], family: str, rmse_thresh: float) -> Tuple[bool, str]:
    """Decision: retune if ANY hard filter fail in diagnostic OR mean_rmse > family thresh."""
    if agg.get("hard_fails", 0) > 0:
        return True, f"hard_filter_fail ({agg['hard_fails']}/{agg['n_cases']})"
    if agg.get("mean_rmse", float("inf")) > rmse_thresh:
        return True, f"mean_rmse_exceeds_thresh ({agg['mean_rmse']:.4f} > {rmse_thresh})"
    return False, "initial_ok"


def generate_progressive_candidates(
    base_gains: Dict[str, List[float]],
    seed: int = 1042,
    n_initial: int = 32,
    n_refinement: int = 16,
    mult_lo: float = 0.5,
    mult_hi: float = 2.0,
) -> List[Dict[str, Any]]:
    """Deterministic progressive search.
    Always includes [1,1,1,1] first.
    Then n_initial log-uniform samples (stratified via fixed RandomState + log spacing influence).
    Then local refinement of 16 around best survivors (small log perturbations).
    Returns list of {'multipliers': [4 floats], 'pid_config': gains dict }
    Reproducible for same seed.
    """
    rng = np.random.RandomState(seed)
    log_lo = np.log(mult_lo)
    log_hi = np.log(mult_hi)
    keys = ["Kp_pos", "Kd_pos", "Kp_att", "Kd_att"]

    cands: List[Dict[str, Any]] = []

    def mult_to_pid(mults: List[float]) -> Dict[str, List[float]]:
        return {k: (np.array(base_gains[k], dtype=float) * m).tolist() for k, m in zip(keys, mults)}

    # 1. Always include initial
    m0 = [1.0, 1.0, 1.0, 1.0]
    cands.append({"multipliers": m0, "pid_config": mult_to_pid(m0)})

    # 2. First round: 32 log-uniform (use uniform on log for log-uniform; spread via rng + some stratification by sorting later)
    sampled = []
    for _ in range(n_initial):
        ms = np.exp(rng.uniform(log_lo, log_hi, 4)).tolist()
        sampled.append(ms)
    # Simple stratification effect: sort sampled by product (log geometric mean) and pick evenly spaced if more
    sampled.sort(key=lambda ms: float(np.prod(ms)))
    for ms in sampled[:n_initial]:
        cands.append({"multipliers": ms, "pid_config": mult_to_pid(ms)})

    # 3+4. Refinement will be done after first eval in caller (select top, then generate around them)
    # Here we also pre-generate a pool of refinement-style around [1,1,1,1] and around a spread; caller uses after first pass.
    # For full 48 budget, caller will call again with refined centers.
    # Pre-populate some local around initial for simplicity in single call
    for i in range(n_refinement):
        # small log pert ~ uniform [-0.2,0.2] clipped
        pert = np.exp(rng.uniform(-0.20, 0.20, 4))
        ms = [max(mult_lo, min(mult_hi, 1.0 * p)) for p in pert]
        cands.append({"multipliers": ms, "pid_config": mult_to_pid(ms)})

    # Dedup close candidates (keep first)
    seen = set()
    unique_cands = []
    for c in cands:
        key = tuple(round(x, 6) for x in c["multipliers"])
        if key not in seen:
            seen.add(key)
            unique_cands.append(c)
    return unique_cands[: (1 + n_initial + n_refinement)]


def select_final_pid(
    initial_pid: Dict[str, Any],
    evaluated: List[Dict[str, Any]],
    initial_mult: List[float] = (1.0, 1.0, 1.0, 1.0),
) -> Dict[str, Any]:
    """Select per spec: best mean score among safe (all hard passed in diag), then within 5% lowest effort, then closest to initial.
    evaluated: list of per-cand {'multipliers':, 'pid_config':, 'agg': agg_dict_from_aggregate, 'results': [...] }
    Returns dict with chosen, source, reason, metrics etc.
    """
    safe = [e for e in evaluated if e.get("agg", {}).get("all_passed", False) and e.get("agg", {}).get("hard_fails", 1) == 0]
    if not safe:
        # No safe at all
        return {"chosen": None, "reason": "no_safe_candidate", "source": "none"}

    # best by mean_score (lower better)
    safe_sorted = sorted(safe, key=lambda e: e["agg"]["mean_score"])
    best = safe_sorted[0]
    best_score = best["agg"]["mean_score"]
    thresh = best_score * 1.05

    within = [e for e in safe_sorted if e["agg"]["mean_score"] <= thresh]

    # among within, lowest effort
    within.sort(key=lambda e: e["agg"].get("mean_effort", 1e9))
    best_eff = within[0]["agg"].get("mean_effort", 1e9)
    lowest_eff = [e for e in within if abs(e["agg"].get("mean_effort", 1e9) - best_eff) < 1e-6]

    # among those, closest to initial (L2 on multipliers)
    def dist_to_init(e):
        m = np.array(e["multipliers"], dtype=float)
        i = np.array(initial_mult, dtype=float)
        return float(np.linalg.norm(m - i))

    lowest_eff.sort(key=dist_to_init)
    chosen = lowest_eff[0]

    # Determine if initial was selected
    is_initial = np.allclose(chosen["multipliers"], [1.,1.,1.,1.], atol=1e-6)
    source = "default_initial_accepted" if is_initial else "tuned_progressive_search"
    reason = "initial_passed_all_and_best_or_accepted" if is_initial else "progressive_search_selected"

    return {
        "chosen_pid": chosen["pid_config"],
        "chosen_multipliers": chosen["multipliers"],
        "source": source,
        "reason": reason,
        "initial_metrics": evaluated[0]["agg"] if evaluated else {},
        "chosen_metrics": chosen["agg"],
        "results": chosen.get("results"),
        "n_evaluated": len(evaluated),
        "best_score": best_score,
    }
