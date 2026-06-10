"""
Genera un banco pequeno y trazable de PIDs por familia.

El banco parte de los PIDs actuales de un dataset clasico y crea variantes
conservadora/base/agresiva. Cada variante se evalua en un subconjunto fijo de
geometrias y perturbaciones para producir un score comparable.
"""
import argparse
import csv
import os
import yaml
import numpy as np

from simulador_quad.datasets.classic import (
    build_scenario_config,
    get_geometry_variants,
    pid_candidate_score,
    passes_hard_filters,
)
from simulador_quad.scenarios.loader import instantiate_scenario
from simulador_quad.runner import SimulationRunner
from simulador_quad.metrics.report import compute_metrics


FAMILIES = ["hold", "circle", "lissajous", "waypoint"]
PROFILES = ["P0_nominal", "P2_wind_east", "P5_combined"]
# Variants modify ONLY external (pos) gains.
# Internal (att) gains and limits are taken exactly from the frozen base PID of the family.
# Extra damped variants added to cover demanding cases without touching attitude.
VARIANTS = {
    "conservative": {"Kp_pos": 0.8, "Kd_pos": 1.0},
    "base": {"Kp_pos": 1.0, "Kd_pos": 1.0},
    "aggressive": {"Kp_pos": 1.2, "Kd_pos": 1.1},
    "damped": {"Kp_pos": 0.9, "Kd_pos": 1.4},   # higher Kd for demanding wind/noise
    "damped2": {"Kp_pos": 1.0, "Kd_pos": 1.3},
}


def _load_family_pid(dataset_root: str, family: str, version: str) -> dict:
    path = os.path.join(dataset_root, "pids", f"pid_{family}_{version}.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _scale_pid(base_pid: dict, scales: dict) -> dict:
    # Only scale Kp/Kd_pos (external). Keep att exactly as in frozen base PID.
    kp_scale = scales.get("Kp_pos", 1.0)
    kd_scale = scales.get("Kd_pos", 1.0)
    return {
        "Kp_pos": (np.array(base_pid["Kp_pos"], dtype=float) * kp_scale).tolist(),
        "Kd_pos": (np.array(base_pid["Kd_pos"], dtype=float) * kd_scale).tolist(),
        "Kp_att": list(base_pid.get("Kp_att", [4.0, 4.0, 1.0])),
        "Kd_att": list(base_pid.get("Kd_att", [1.5, 1.5, 0.5])),
    }


def _run_case(family: str, pid_config: dict, trajectory_cfg: dict, profile_id: str, seed: int):
    config = build_scenario_config(
        f"pid_bank_{family}_{profile_id}_{seed}",
        family,
        trajectory_cfg,
        profile_id,
        pid_config,
        seed,
        "tmp_pid_bank",
    )
    v_params, mixer, actuators, initial_state, trajectory, controller, wind, noise = instantiate_scenario(config)
    runner = SimulationRunner(
        physics_dt_s=config["timing"]["physics_dt_s"],
        control_dt_s=config["timing"]["control_dt_s"],
        telemetry_dt_s=config["timing"]["telemetry_dt_s"],
        vehicle_params=v_params,
        mixer=mixer,
        actuators=actuators,
        wind_model=wind,
        observation_noise=noise,
        max_duration_s=config["termination"]["max_duration_s"],
        z_min_m=config["termination"]["z_min_m"],
        max_attitude_angle_rad=config["termination"].get("max_attitude_angle_rad", 1.256),
        max_saturation_duration_s=config["termination"].get("max_saturation_duration_s", 1.0),
    )
    result = runner.run(initial_state, controller, trajectory)
    metrics = compute_metrics(result["telemetry"], result["termination_reason"])
    return result["telemetry"], metrics


def main():
    parser = argparse.ArgumentParser(description="Generate a small PID bank from current family PIDs.")
    parser.add_argument("--dataset", required=True, help="Classic dataset root containing pids/")
    parser.add_argument("--out", required=True, help="Output directory for PID bank")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--geometries-per-family", type=int, default=2)
    args = parser.parse_args()

    os.makedirs(os.path.join(args.out, "pids"), exist_ok=True)
    manifest_rows = []
    seed = 9000

    for family in FAMILIES:
        base_pid = _load_family_pid(args.dataset, family, args.version)
        geometries = get_geometry_variants(family)[: args.geometries_per_family]
        for variant_name, scales in VARIANTS.items():
            pid_config = _scale_pid(base_pid, scales)
            scores = []
            valid_cases = 0
            total_cases = 0

            for _, trajectory_cfg in geometries:
                for profile_id in PROFILES:
                    total_cases += 1
                    telemetry, metrics = _run_case(family, pid_config, trajectory_cfg, profile_id, seed)
                    seed += 1
                    ok, _ = passes_hard_filters(metrics, family)
                    if ok:
                        valid_cases += 1
                    scores.append(pid_candidate_score(metrics, telemetry, family))

            pid_id = f"pid_{family}_bank_{variant_name}_{args.version}"
            pid_path = os.path.join(args.out, "pids", f"{pid_id}.yaml")
            # Record origin frozen base + the pos-only multipliers (neural_position only predicts external)
            base_origin = base_pid.get("pid_id", f"pid_{family}_{args.version}")
            with open(pid_path, "w") as f:
                yaml.dump(
                    {
                        "pid_id": pid_id,
                        "family": family,
                        "version": args.version,
                        "source": "generated_pid_bank",
                        "variant": variant_name,
                        "base_pid": base_origin,
                        "multipliers": scales,  # only pos keys are non-1.0
                        **pid_config,
                    },
                    f,
                    sort_keys=False,
                )

            manifest_rows.append({
                "pid_id": pid_id,
                "family": family,
                "variant": variant_name,
                "valid_cases": valid_cases,
                "total_cases": total_cases,
                "mean_score": float(np.mean(scores)),
                "pid_path": os.path.relpath(pid_path, args.out),
            })

    manifest_path = os.path.join(args.out, "pid_bank_manifest.csv")
    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"PID bank written to {args.out}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
