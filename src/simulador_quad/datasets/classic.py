import os
import yaml
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
from simulador_quad.scenarios.loader import instantiate_trajectory

# --- Constants v1 ---

FAMILIES = ["hold", "circle", "lissajous", "waypoint"]

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
    "max_duration_s": 15.0, # Sufficient for all families
    "z_min_m": 0.0,
    "max_attitude_angle_rad": 1.256, # ~72 deg
    "max_saturation_duration_s": 2.0
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
        "termination": BASE_TERMINATION,
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
        # 6 patterns
        names = ["square", "rect", "zigzag", "stairs", "diag3d", "closed"]
        waypoints = [
            [[0,0,2], [2,0,2], [2,2,2], [0,2,2], [0,0,2]],
            [[0,0,2], [3,0,2], [3,1,2], [0,1,2], [0,0,2]],
            [[0,0,2], [1,1,2], [2,0,2], [3,1,2], [4,0,2]],
            [[0,0,1], [1,0,1.5], [2,0,2], [3,0,2.5], [4,0,3]],
            [[0,0,1], [2,2,3]],
            [[0,0,2], [1,1,3], [0,2,2], [-1,1,3], [0,0,2]]
        ]
        times = [
            [0, 4, 8, 12, 16],
            [0, 5, 7, 12, 14],
            [0, 3, 6, 9, 12],
            [0, 3, 6, 9, 12],
            [0, 10],
            [0, 4, 8, 12, 16]
        ]
        
        variants = []
        for i, (name, wp, ts) in enumerate(zip(names, waypoints, times)):
            variants.append((f"g{i+1:02d}", {
                "type": "waypoint", "waypoints": wp, "times": ts
            }))
        return variants
    
    return []

def get_dataset_manifest_data(version: str = "v1") -> List[Dict[str, Any]]:
    manifest = []
    base_seed = 1042
    
    # Stratified splits per family to ensure balance
    family_splits = {
        "hold": ["train"] * 12 + ["val"] * 3 + ["test"] * 3,
        "circle": ["train"] * 34 + ["val"] * 7 + ["test"] * 7,
        "lissajous": ["train"] * 34 + ["val"] * 7 + ["test"] * 7,
        "waypoint": ["train"] * 25 + ["val"] * 5 + ["test"] * 6
    }
    
    # Shuffle splits for each family
    rng = np.random.RandomState(base_seed)
    for f in family_splits:
        rng.shuffle(family_splits[f])
    
    family_counters = {f: 0 for f in FAMILIES}
    
    for family in FAMILIES:
        geometries = get_geometry_variants(family)
        
        if family == "hold":
            profiles_to_use = ["P0_nominal", "P2_wind_east", "P5_combined"]
        else:
            profiles_to_use = list(PROFILES.keys())
            
        for g_id, g_cfg in geometries:
            for p_id in profiles_to_use:
                seed = base_seed + len(manifest)
                scenario_id = build_scenario_id(family, g_id, p_id, seed)
                
                f_idx = family_counters[family]
                split = family_splits[family][f_idx]
                family_counters[family] += 1
                
                manifest.append({
                    "scenario_id": scenario_id,
                    "family": family,
                    "geometry_id": g_id,
                    "perturbation_id": p_id,
                    "pid_id": build_pid_id(family, version),
                    "seed": seed,
                    "split": split,
                    "trajectory_cfg": g_cfg
                })
                
    return manifest

def write_dataset_files(version: str, output_root: str, overwrite: bool = False):
    if os.path.exists(output_root) and not overwrite:
        raise FileExistsError(f"Directory {output_root} already exists. Use overwrite=True to force.")
    
    os.makedirs(output_root, exist_ok=True)
    manifest_data = get_dataset_manifest_data(version=version)
    
    os.makedirs(os.path.join(output_root, "pids"), exist_ok=True)
    initial_pids = {
        "hold": {"Kp_pos": [2.0, 2.0, 5.0], "Kd_pos": [1.0, 1.0, 2.0], "Kp_att": [4.0, 4.0, 1.0], "Kd_att": [1.5, 1.5, 0.5]},
        "circle": {"Kp_pos": [2.0, 2.0, 5.0], "Kd_pos": [1.0, 1.0, 2.0], "Kp_att": [4.0, 4.0, 1.0], "Kd_att": [1.5, 1.5, 0.5]},
        "lissajous": {"Kp_pos": [2.0, 2.0, 5.0], "Kd_pos": [1.0, 1.0, 2.0], "Kp_att": [4.0, 4.0, 1.0], "Kd_att": [1.5, 1.5, 0.5]},
        "waypoint": {"Kp_pos": [2.0, 2.0, 5.0], "Kd_pos": [1.0, 1.0, 2.0], "Kp_att": [4.0, 4.0, 1.0], "Kd_att": [1.5, 1.5, 0.5]}
    }
    
    pid_configs = {}
    for family in FAMILIES:
        pid_id = build_pid_id(family, version)
        pid_path = os.path.join(output_root, "pids", f"{pid_id}.yaml")
        if not os.path.exists(pid_path):
            pid_data = {
                "pid_id": pid_id,
                "family": family,
                "version": version,
                "source": "default_initial",
                **initial_pids[family]
            }
            with open(pid_path, 'w') as f:
                yaml.dump(pid_data, f, sort_keys=False)
        
        with open(pid_path, 'r') as f:
            pid_all = yaml.safe_load(f)
            pid_configs[family] = {k: pid_all[k] for k in ["Kp_pos", "Kd_pos", "Kp_att", "Kd_att"] if k in pid_all}

    # Write scenarios
    for row in manifest_data:
        family_dir = os.path.join(output_root, "scenarios", row["family"])
        os.makedirs(family_dir, exist_ok=True)
        
        pid_config = pid_configs[row["family"]]
        
        scenario_config = build_scenario_config(
            row["scenario_id"], row["family"], row["trajectory_cfg"], 
            row["perturbation_id"], pid_config, row["seed"], output_root
        )
        
        yaml_path = os.path.join(family_dir, f"{row['scenario_id']}.yaml")
        with open(yaml_path, 'w') as f:
            yaml.dump(scenario_config, f, sort_keys=False)
            
        row["scenario_path"] = os.path.relpath(yaml_path, output_root)
        row["result_dir"] = os.path.relpath(scenario_config["output"]["dir"], output_root)

    # Write manifest.csv
    import csv
    manifest_csv = os.path.join(output_root, "manifest.csv")
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
    with open(os.path.join(output_root, "README.md"), 'w') as f:
        f.write(f"# Classic Dataset {version}\n\nGenerated automatically.\nTotal episodes: {len(manifest_data)}\n")

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

    valid_terminations = ["Time limit reached"]
    if family == "waypoint":
        valid_terminations.append("Trajectory completed")

    if metrics["termination_reason"] not in valid_terminations:
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
