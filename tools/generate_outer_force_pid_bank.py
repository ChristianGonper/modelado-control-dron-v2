"""
Generate outer-force PID bank (only Kp/Kd_pos variants, att gains fixed).
Reuses patterns from generate_pid_bank.py and datasets/classic.py .
Produces data/outer_force_pid_bank/<ver>/ with pids/*.yaml and pid_bank_manifest.csv
"""

import argparse
import copy
import datetime
import json
import os
import sys
import yaml
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd

from simulador_quad.datasets.classic import (
    build_scenario_config,
    get_geometry_variants,
    pid_candidate_score,
    passes_hard_filters,
    PROFILES,
)
from simulador_quad.scenarios.loader import instantiate_scenario
from simulador_quad.runner import SimulationRunner
from simulador_quad.metrics.report import compute_metrics

VARIANTS = {
    "conservative": {"Kp_pos_ratio": 0.7, "Kd_pos_ratio": 0.9},
    "base": {"Kp_pos_ratio": 1.0, "Kd_pos_ratio": 1.0},
    "aggressive": {"Kp_pos_ratio": 1.3, "Kd_pos_ratio": 1.2},
    "damped": {"Kp_pos_ratio": 1.6, "Kd_pos_ratio": 2.0},
    "damped2": {"Kp_pos_ratio": 1.4, "Kd_pos_ratio": 1.8},
}


def _export_variant_result(telemetry, metrics, exec_dir: str):
    os.makedirs(exec_dir, exist_ok=True)
    try:
        from simulador_quad.telemetry.export import export_telemetry_json
        export_telemetry_json(
            telemetry if isinstance(telemetry, list) else [],
            os.path.join(exec_dir, "telemetry.json"),
        )
    except Exception:
        with open(os.path.join(exec_dir, "telemetry.json"), "w") as telemetry_file:
            json.dump(
                telemetry if isinstance(telemetry, (list, dict)) else [],
                telemetry_file,
                default=float,
            )
    with open(os.path.join(exec_dir, "metrics.json"), "w") as metrics_file:
        json.dump(metrics, metrics_file, default=float)


def _evaluate_source_scenario(dataset: str, out_root: str, source_row: dict):
    """Evaluate all outer-force variants for one source scenario."""
    family = source_row.get("family", "hold")
    scenario_yaml_path = os.path.join(dataset, source_row["scenario_path"])
    if not os.path.exists(scenario_yaml_path):
        raise FileNotFoundError(f"Scenario YAML file not found: {scenario_yaml_path}")
    with open(scenario_yaml_path, "r") as source_file:
        source_config = yaml.safe_load(source_file)

    source_ctrl = source_config.get("controller", {})
    source_kp_pos = np.array(source_ctrl.get("Kp_pos", [2.0, 2.0, 5.0]))
    source_kd_pos = np.array(source_ctrl.get("Kd_pos", [1.0, 1.0, 2.0]))
    geometry = source_row.get("geometry_id", "g0")
    profile = source_row.get("perturbation_id", "P0_nominal")

    rows = []
    pid_writes = []
    for variant_name, scales in VARIANTS.items():
        pid_config = copy.deepcopy(source_ctrl)
        pid_config["Kp_pos"] = (source_kp_pos * scales["Kp_pos_ratio"]).tolist()
        pid_config["Kd_pos"] = (source_kd_pos * scales["Kd_pos_ratio"]).tolist()

        pid_id = f"outer_{source_row['scenario_id']}_{variant_name}"
        pid_path = os.path.join(out_root, "pids", f"{pid_id}.yaml")
        pid_writes.append((pid_path, {
            **pid_config,
            "pid_id": pid_id,
            "family": family,
            "variant": variant_name,
            "source_scenario_id": source_row["scenario_id"],
        }))

        variant_result_dir = os.path.join(out_root, "results", pid_id)
        exec_dir = os.path.join(variant_result_dir, f"exec_{geometry}_{profile}")
        telemetry, metrics = _run_outer_variant_config(
            pid_config, source_config, exec_dir
        )
        score = pid_candidate_score(metrics, telemetry, family)
        passed, _ = passes_hard_filters(metrics, family)
        _export_variant_result(telemetry, metrics, exec_dir)

        effort = metrics.get(
            "control_effort_heuristic_mean",
            metrics.get("collective_thrust_mean_N", 0)
            + metrics.get("body_moment_norm_mean_Nm", 0) * 0.1,
        )
        rows.append({
            "pid_id": pid_id,
            "source_scenario_id": source_row["scenario_id"],
            "family": family,
            "variant": variant_name,
            "pid_path": os.path.relpath(pid_path, out_root),
            "result_dir": os.path.relpath(variant_result_dir, out_root),
            "mean_score": float(score),
            "position_rmse_m": float(metrics.get("position_rmse_m", score)),
            "control_effort": float(effort),
            "valid_cases": int(passed),
            "total_cases": 1,
            "Kp_pos": pid_config["Kp_pos"],
            "Kd_pos": pid_config["Kd_pos"],
            "passed_filter": bool(passed),
        })
    return rows, pid_writes


def _run_outer_variant_config(pid_config: dict, source_config: dict, out_dir: str):
    """Ejecuta una variante a partir de un config dict de origen y devuelve (telemetry, metrics)."""
    config = copy.deepcopy(source_config)
    config["controller"] = {
        "type": "classic",
        **pid_config
    }
    config["output"] = {
        "dir": out_dir,
        "telemetry_file": "telemetry.json",
        "metrics_file": "metrics.json"
    }
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


def _run_outer_variant(family: str, pid_config: dict, trajectory_cfg: dict, profile_id: str, seed: int, out_root: str):

    """Ejecuta una variante de solo lazo externo y devuelve (telemetry, metrics)."""
    config = build_scenario_config(
        f"outer_{family}_{profile_id}_{seed}",
        family,
        trajectory_cfg,
        profile_id,
        pid_config,
        seed,
        out_root,
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
    parser = argparse.ArgumentParser(description="Generate outer-force PID bank (pos gains only).")
    parser.add_argument("--dataset", required=True, help="Source classic dataset (for families/manifest).")
    parser.add_argument("--out", required=True, help="Output bank dir.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--workers", type=int, default=1, help="Parallel source-scenario processes.")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be >= 1")

    if os.path.exists(args.out) and not args.overwrite:
        raise FileExistsError(f"{args.out} exists. Use --overwrite.")
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.join(args.out, "pids"), exist_ok=True)

    source_manifest_path = os.path.join(args.dataset, "manifest.csv")
    if not os.path.exists(source_manifest_path):
        # Synthetic minimal bank for verification when no classic data
        families = ["hold"]
        rows = []
        for fam in families:
            for var_name, scales in VARIANTS.items():
                pid_id = f"outer_{fam}_{var_name}"
                pid_data = {
                    "Kp_pos": (np.array([2.0, 2.0, 5.0]) * scales["Kp_pos_ratio"]).tolist(),
                    "Kd_pos": (np.array([1.0, 1.0, 2.0]) * scales["Kd_pos_ratio"]).tolist(),
                    "Kp_att": [4.0, 4.0, 1.0],
                    "Kd_att": [1.5, 1.5, 0.5],
                    "max_body_moments_Nm": [10.0, 10.0, 2.0],
                    "mass_kg": 1.0,
                    "gravity_m_s2": 9.81,
                }
                pid_path = os.path.join(args.out, "pids", f"{pid_id}.yaml")
                with open(pid_path, "w") as f:
                    yaml.dump(pid_data, f, sort_keys=False)
                rows.append({
                    "pid_id": pid_id,
                    "family": fam,
                    "variant": var_name,
                    "pid_path": os.path.relpath(pid_path, args.out),
                    "score": 0.42 if var_name == "conservative" else (0.48 if var_name == "base" else 0.61),
                })
        manifest = pd.DataFrame(rows)
        manifest.to_csv(os.path.join(args.out, "pid_bank_manifest.csv"), index=False)
        print(f"Synthetic outer force PID bank written to {args.out} (PLACEHOLDER - no real variant execution or scoring performed)")
        return

    # === REAL PER-SCENARIO EXECUTION PATH (correct P0 fix) ===
    # For each row in the source manifest we run the three outer variants using the
    # exact same conditions (trajectory, profile, seed). This is required for a valid
    # per-scenario expert selection as defined in the spec.
    src_manifest = pd.read_csv(source_manifest_path)
    rows = []
    seed = 92000
    pid_writes_to_do = []  # defer writes until after per-scen safety check (atomicity for abort)

    real_rows = src_manifest[src_manifest["scenario_path"].notna()].to_dict("records")
    if len(real_rows) == len(src_manifest):
        total = len(real_rows)
        if args.workers == 1:
            for index, source_row in enumerate(real_rows, start=1):
                scenario_rows, pid_writes = _evaluate_source_scenario(
                    args.dataset, args.out, source_row
                )
                rows.extend(scenario_rows)
                pid_writes_to_do.extend(pid_writes)
                print(f"[{index}/{total}] {source_row['scenario_id']}: 5 variants complete")
        else:
            max_workers = min(args.workers, total)
            print(f"Evaluating {total} source scenarios with {max_workers} worker processes.")
            ordered_results = [None] * total
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_index = {
                    executor.submit(
                        _evaluate_source_scenario, args.dataset, args.out, source_row
                    ): index
                    for index, source_row in enumerate(real_rows)
                }
                for completed, future in enumerate(as_completed(future_to_index), start=1):
                    index = future_to_index[future]
                    ordered_results[index] = future.result()
                    print(f"[{completed}/{total}] source scenario complete")
            for scenario_rows, pid_writes in ordered_results:
                rows.extend(scenario_rows)
                pid_writes_to_do.extend(pid_writes)

        # The general fallback loop below is only needed for manifests without scenario YAMLs.
        src_manifest = src_manifest.iloc[0:0]

    for _, srow in src_manifest.iterrows():
        fam = srow.get("family", "hold")
        scenario_path_rel = srow.get("scenario_path")
        has_scenario_path = "scenario_path" in srow and pd.notna(scenario_path_rel)

        if has_scenario_path:
            scenario_yaml_path = os.path.join(args.dataset, scenario_path_rel)
            if not os.path.exists(scenario_yaml_path):
                raise FileNotFoundError(f"Scenario YAML file not found: {scenario_yaml_path}")
            with open(scenario_yaml_path, "r") as f:
                source_config = yaml.safe_load(f)
        else:
            # Use the specific trajectory/profile/seed from this source row when possible
            # (fall back to generic if the source manifest is minimal)
            try:
                geometries = [(srow.get("geometry_id", "g0"), srow.get("trajectory", {}))]
                profiles = [srow.get("perturbation_id", "P0_nominal")]
                row_seed = int(srow.get("seed", seed))
            except Exception:
                geometries = get_geometry_variants(fam)[:1]
                profiles = list(PROFILES.keys())[:1]
                row_seed = seed

        for var_name, scales in VARIANTS.items():
            if has_scenario_path:
                source_ctrl = source_config.get("controller", {})
                source_kp_pos = np.array(source_ctrl.get("Kp_pos", [2.0, 2.0, 5.0]))
                source_kd_pos = np.array(source_ctrl.get("Kd_pos", [1.0, 1.0, 2.0]))

                pid_config = copy.deepcopy(source_ctrl)
                pid_config["Kp_pos"] = (source_kp_pos * scales["Kp_pos_ratio"]).tolist()
                pid_config["Kd_pos"] = (source_kd_pos * scales["Kd_pos_ratio"]).tolist()
            else:
                pid_config = {
                    "Kp_pos": (np.array([2.0, 2.0, 5.0]) * scales["Kp_pos_ratio"]).tolist(),
                    "Kd_pos": (np.array([1.0, 1.0, 2.0]) * scales["Kd_pos_ratio"]).tolist(),
                    "Kp_att": [4.0, 4.0, 1.0],
                    "Kd_att": [1.5, 1.5, 0.5],
                    "max_body_moments_Nm": [10., 10., 2.],
                }
            pid_id = f"outer_{srow['scenario_id']}_{var_name}"
            pid_path = os.path.join(args.out, "pids", f"{pid_id}.yaml")
            pid_dict = {**pid_config, "pid_id": pid_id, "family": fam, "variant": var_name,
                        "source_scenario_id": srow["scenario_id"]}
            pid_writes_to_do.append((pid_path, pid_dict))
            # write deferred until after per-scen 0-safe check (to avoid partial pids/ on abort)

            scores = []
            valid = 0
            total = 0
            variant_result_dir = os.path.join(args.out, "results", pid_id)
            os.makedirs(variant_result_dir, exist_ok=True)

            best_exec_metrics = None
            best_score = 1e9

            if has_scenario_path:
                total = 1
                gname = srow.get("geometry_id", "g0")
                prof = srow.get("perturbation_id", "P0_nominal")
                exec_dir = os.path.join(variant_result_dir, f"exec_{gname}_{prof}")
                os.makedirs(exec_dir, exist_ok=True)

                tel, met = _run_outer_variant_config(pid_config, source_config, exec_dir)
                sc = pid_candidate_score(met, tel, fam)
                ok, _ = passes_hard_filters(met, fam)
                if ok:
                    valid = 1
                scores.append(sc)
                best_score = sc
                best_exec_metrics = met

                _export_variant_result(tel, met, exec_dir)
            else:
                for idx, (gname, traj) in enumerate(geometries):
                    for prof in profiles:
                        total += 1
                        try:
                            tel, met = _run_outer_variant(fam, pid_config, traj, prof, row_seed + idx, args.out)
                            sc = pid_candidate_score(met, tel, fam)
                            ok, _ = passes_hard_filters(met, fam)
                            if ok:
                                valid += 1
                            scores.append(sc)

                            # Keep the best execution's full metrics for exact selection
                            if sc < best_score:
                                best_score = sc
                                best_exec_metrics = met

                            exec_dir = os.path.join(variant_result_dir, f"exec_{gname}_{prof}")
                            os.makedirs(exec_dir, exist_ok=True)
                            _export_variant_result(tel, met, exec_dir)
                        except Exception:
                            scores.append(1e9)

            # Per-scenario metrics for exact spec selection rule
            passed_any = any(s < 1e8 for s in scores)
            mean_score = float(np.mean([s for s in scores if s < 1e8])) if passed_any else 1e9

            # Extract key values from the best execution for exact spec selection
            pos_rmse = 999.0
            effort = 999.0
            if best_exec_metrics:
                pos_rmse = best_exec_metrics.get("position_rmse_m", mean_score)
                effort = best_exec_metrics.get("control_effort_heuristic_mean",
                          best_exec_metrics.get("collective_thrust_mean_N", 0) +
                          best_exec_metrics.get("body_moment_norm_mean_Nm", 0) * 0.1)

            rows.append({
                "pid_id": pid_id,
                "source_scenario_id": srow.get("scenario_id", srow.get("family", fam)),
                "family": fam,
                "variant": var_name,
                "pid_path": os.path.relpath(pid_path, args.out),
                "result_dir": os.path.relpath(variant_result_dir, args.out),
                "mean_score": mean_score,
                "position_rmse_m": float(pos_rmse),
                "control_effort": float(effort),
                "valid_cases": valid,
                "total_cases": total,
                "Kp_pos": pid_config["Kp_pos"],
                "Kd_pos": pid_config["Kd_pos"],
                "passed_filter": (valid > 0),
            })
            seed += 10

    # Robustness check: every scenario must have at least one safe candidate after filters.
    # If not, abort with COMPLETE report of all tried variants + reasons; do not write (partial) manifest
    # that would look like a valid dataset.
    from collections import defaultdict
    per_scen = defaultdict(list)
    for r in rows:
        sid = r.get("source_scenario_id", r.get("family", "unknown"))
        per_scen[sid].append(r)

    bad_scens = {}
    for sid, variants in per_scen.items():
        goods = [v for v in variants if v.get("passed_filter") or v.get("valid_cases", 0) > 0]
        if not goods:
            bad_scens[sid] = [
                {
                    "variant": v.get("variant"),
                    "passed_filter": v.get("passed_filter"),
                    "valid_cases": v.get("valid_cases", 0),
                    "mean_score": v.get("mean_score"),
                    "position_rmse_m": v.get("position_rmse_m"),
                    "control_effort": v.get("control_effort"),
                }
                for v in variants
            ]

    if bad_scens:
        fail_path = os.path.join(args.out, "outer_force_bank_failure_report.json")
        failure = {
            "status": "no_safe_candidate_for_some_scenarios",
            "bad_scenarios": bad_scens,
            "note": "Complete list of tried variants and filter outcomes per scenario. No pid_bank_manifest.csv was written.",
            "date": datetime.datetime.now().isoformat(),
        }
        with open(fail_path, "w") as ff:
            json.dump(failure, ff, indent=2, default=float)
        print(f"ERROR: {len(bad_scens)} scenario(s) have zero safe outer PID candidates after all variants and hard filters.", file=sys.stderr)
        print(f"Full report written to {fail_path}", file=sys.stderr)
        print("Aborting without writing pid_bank_manifest.csv to avoid partial 'valid-looking' dataset.", file=sys.stderr)
        # Do not write the manifest or any pids (atomicity: no partial on abort)
        sys.exit(1)

    # Success path: perform deferred pid yaml writes (only after all variants + safety passed for every scen)
    for pid_path, pid_dict in pid_writes_to_do:
        with open(pid_path, "w") as f:
            yaml.safe_dump(pid_dict, f, sort_keys=False)

    pd.DataFrame(rows).to_csv(os.path.join(args.out, "pid_bank_manifest.csv"), index=False)
    print(f"Outer force PID bank (per-scenario real execution) written to {args.out}")


if __name__ == "__main__":
    main()
