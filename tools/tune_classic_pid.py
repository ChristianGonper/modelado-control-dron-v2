"""
tools/tune_classic_pid.py

Diagnostico + tuneo progresivo reproducible de PID base por familia.
Orientado a dataset completo, usa solo train, diagnostica todas (o --family),
tunea solo las necesarias, escritura atomica de artefactos solo tras eval completa exitosa.
No modifica filtros duros ni score (fuentes de verdad en classic.py).
"""
import argparse
import os
import sys
import yaml
import json
import csv
import datetime
import tempfile
import shutil
from typing import Dict, Any, List, Tuple
import numpy as np

from simulador_quad.datasets.classic import (
    FAMILIES,
    PROFILES,
    BASE_VEHICLE,
    build_scenario_config,
    get_geometry_variants,
    get_diagnostic_cases,
    aggregate_diagnostic,
    needs_tuning,
    generate_progressive_candidates,
    select_final_pid,
    pid_candidate_score,
    passes_hard_filters,
)
from simulador_quad.scenarios.loader import instantiate_scenario
from simulador_quad.runner import SimulationRunner
from simulador_quad.metrics.report import compute_metrics


DEFAULT_RMSE_THRESH = {
    "hold": 0.25,
    "circle": 0.35,
    "lissajous": 0.45,
    "waypoint": 0.40,
}


def _run_pid_on_case(
    pid_config: Dict[str, Any],
    case: Dict[str, Any],
    family: str,
    output_root: str,
    seed_override: int = None,
) -> Tuple[List[Any], Dict[str, Any]]:
    """Run one closed-loop sim for (family, pid, case) and return (telemetry, metrics)."""
    traj = case["trajectory_cfg"]
    prof = case["perturbation_id"]
    sd = int(seed_override or case.get("seed", 1042))
    scenario_id = f"tune_{family}_{case.get('geometry_id','gxx')}_{prof}_s{sd}"
    config = build_scenario_config(
        scenario_id, family, traj, prof, pid_config, sd, output_root
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
        z_min_m=config["termination"].get("z_min_m", 0.0),
        max_attitude_angle_rad=config["termination"].get("max_attitude_angle_rad", 1.256),
        max_saturation_duration_s=config["termination"].get("max_saturation_duration_s", 2.0),
    )
    result = runner.run(initial_state, controller.compute_control, trajectory)
    metrics = compute_metrics(result["telemetry"], result["termination_reason"])
    return result["telemetry"], metrics


def _load_base_pid_gains(pid_yaml_path: str) -> Dict[str, List[float]]:
    with open(pid_yaml_path, "r") as f:
        data = yaml.safe_load(f) or {}
    keys = ["Kp_pos", "Kd_pos", "Kp_att", "Kd_att"]
    source = data.get("source", "default_initial")
    if source != "default_initial":
        family = data.get("family")
        print(f"  [INFO] PID at {pid_yaml_path} was already tuned (source={source}). Reverting base gains to default_initial for tuning.")
        from simulador_quad.datasets.classic import INITIAL_PIDS
        return {k: list(INITIAL_PIDS[family][k]) for k in keys}
    return {k: list(data[k]) for k in keys if k in data}


def _write_atomic_yaml(path: str, data: Dict[str, Any]):
    """Atomic write: .tmp then replace."""
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        yaml.dump(data, f, sort_keys=False)
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose initial PIDs and (conditionally) tune base PID per family using progressive deterministic search. "
                    "Uses only train split diagnostic set. Writes frozen pid yamls + reports only on full success."
    )
    parser.add_argument("--dataset", required=True, help="Classic dataset root (contains manifest.csv and pids/)")
    parser.add_argument("--out", required=True, help="Output dir for pid_<family>_v1.yaml (usually data/.../pids)")
    parser.add_argument("--family", type=str, default=None, choices=FAMILIES + [None], help="Tune/diagnose only this family (default: all)")
    parser.add_argument("--force", action="store_true", help="Force search even if initial PID passes criteria")
    parser.add_argument("--seed", type=int, default=1042, help="Seed for candidate generation (default 1042 for repro)")
    parser.add_argument("--initial-candidates", type=int, default=32, help="First round log-uniform candidates")
    parser.add_argument("--refinement-candidates", type=int, default=16, help="Local refinement candidates")
    parser.add_argument("--rmse-hold", type=float, default=DEFAULT_RMSE_THRESH["hold"])
    parser.add_argument("--rmse-circle", type=float, default=DEFAULT_RMSE_THRESH["circle"])
    parser.add_argument("--rmse-lissajous", type=float, default=DEFAULT_RMSE_THRESH["lissajous"])
    parser.add_argument("--rmse-waypoint", type=float, default=DEFAULT_RMSE_THRESH["waypoint"])
    parser.add_argument("--version", type=str, default="v1")

    args = parser.parse_args()

    rmse_thresh = {
        "hold": args.rmse_hold,
        "circle": args.rmse_circle,
        "lissajous": args.rmse_lissajous,
        "waypoint": args.rmse_waypoint,
    }

    dataset_root = args.dataset
    pids_out_dir = args.out
    os.makedirs(pids_out_dir, exist_ok=True)

    pid_tuning_dir = os.path.join(os.path.dirname(pids_out_dir.rstrip("/\\")) or dataset_root, "pid_tuning")
    os.makedirs(pid_tuning_dir, exist_ok=True)

    families = [args.family] if args.family else FAMILIES

    # Load diagnostic cases (only train)
    try:
        all_cases = get_diagnostic_cases(dataset_root)
    except Exception as exc:
        print(f"ERROR: cannot build diagnostic set from {dataset_root}: {exc}", file=sys.stderr)
        sys.exit(2)

    # Per-family results for reports (collected before any final pid write)
    family_reports: Dict[str, Dict[str, Any]] = {}
    all_diagnostic_rows = []
    candidates_rows_global: Dict[str, List[Dict]] = {f: [] for f in families}

    had_failure = False
    failure_reasons: Dict[str, str] = {}
    pid_writes_deferred = []

    with tempfile.TemporaryDirectory(prefix="tune_pid_") as tmp_root:
        for family in families:
            print(f"\n=== Diagnosing family: {family} (seed={args.seed}) ===")
            base_pid_path = os.path.join(dataset_root, "pids", f"pid_{family}_{args.version}.yaml")
            if not os.path.exists(base_pid_path):
                print(f"ERROR: base pid not found: {base_pid_path}", file=sys.stderr)
                had_failure = True
                failure_reasons[family] = "missing_base_pid"
                continue

            try:
                base_gains = _load_base_pid_gains(base_pid_path)
            except Exception as exc:
                print(f"ERROR loading base pid for {family}: {exc}", file=sys.stderr)
                had_failure = True
                failure_reasons[family] = str(exc)
                continue

            initial_pid_config = {
                "Kp_pos": base_gains["Kp_pos"],
                "Kd_pos": base_gains["Kd_pos"],
                "Kp_att": base_gains["Kp_att"],
                "Kd_att": base_gains["Kd_att"],
            }

            cases = all_cases.get(family, [])
            if len(cases) < 3:
                print(f"WARNING: very few diagnostic cases for {family}: {len(cases)} (continuing)")

            # Evaluate INITIAL on full diagnostic set for this family
            initial_results: List[Dict[str, Any]] = []
            for case in cases:
                try:
                    tel, met = _run_pid_on_case(initial_pid_config, case, family, tmp_root)
                    passed, reason = passes_hard_filters(met, family)
                    sc = pid_candidate_score(met, tel, family)
                    initial_results.append({
                        "case": case,
                        "metrics": met,
                        "telemetry": tel,
                        "passed": passed,
                        "score": sc,
                        "reason": reason,
                    })
                    # also record for global diagnostic report
                    all_diagnostic_rows.append({
                        "family": family,
                        "geometry_id": case["geometry_id"],
                        "perturbation_id": case["perturbation_id"],
                        "scenario_id": case.get("scenario_id", ""),
                        "phase": "initial",
                        "position_rmse_m": met.get("position_rmse_m"),
                        "position_max_err_m": met.get("position_max_err_m"),
                        "saturation_percentage": met.get("saturation_percentage"),
                        "degradation_percentage": met.get("degradation_percentage"),
                        "termination_reason": met.get("termination_reason"),
                        "passed_hard": passed,
                        "hard_reason": reason,
                        "score": sc,
                    })
                except Exception as exc:
                    print(f"  ERROR running initial on {case}: {exc}")
                    had_failure = True
                    failure_reasons[family] = f"initial_eval_error: {exc}"
                    initial_results.append({"case": case, "metrics": {"position_rmse_m": 999}, "passed": False, "score": 1e9, "reason": str(exc)})

            init_agg = aggregate_diagnostic(initial_results)
            do_tune, tune_reason = needs_tuning(init_agg, family, rmse_thresh[family])
            do_tune = do_tune or args.force

            evaluated: List[Dict[str, Any]] = [{
                "multipliers": [1.0, 1.0, 1.0, 1.0],
                "pid_config": initial_pid_config,
                "agg": init_agg,
                "results": initial_results,
            }]

            chosen_info = None
            if not do_tune:
                print(f"  Initial PID acceptable (mean_rmse={init_agg['mean_rmse']:.4f}, hard_fails={init_agg['hard_fails']}). Accepting.")
                chosen_info = {
                    "chosen_pid": initial_pid_config,
                    "chosen_multipliers": [1.0, 1.0, 1.0, 1.0],
                    "source": "default_initial_accepted",
                    "reason": "initial_ok_no_tune_needed",
                    "initial_metrics": init_agg,
                    "chosen_metrics": init_agg,
                    "n_evaluated": 1,
                    "best_score": init_agg["mean_score"],
                }
            else:
                print(f"  Requires tuning: {tune_reason}. Running progressive search (budget ~{1+args.initial_candidates+args.refinement_candidates}) ...")
                # Generate and eval first round (incl initial already in)
                cands = generate_progressive_candidates(
                    base_gains=base_gains,
                    seed=args.seed,
                    n_initial=args.initial_candidates,
                    n_refinement=args.refinement_candidates,
                )
                # Eval up to initial+32
                first_round = cands[:1 + args.initial_candidates]
                for ci, cand in enumerate(first_round):
                    if ci == 0:
                        continue  # already have initial
                    res_list = []
                    for case in cases:
                        try:
                            tel, met = _run_pid_on_case(cand["pid_config"], case, family, tmp_root)
                            passed, reason = passes_hard_filters(met, family)
                            sc = pid_candidate_score(met, tel, family)
                            res_list.append({"case": case, "metrics": met, "passed": passed, "score": sc, "reason": reason})
                        except Exception as exc:
                            res_list.append({"case": case, "metrics": {"position_rmse_m": 999}, "passed": False, "score": 1e9, "reason": str(exc)})
                    agg = aggregate_diagnostic(res_list)
                    evaluated.append({
                        "multipliers": cand["multipliers"],
                        "pid_config": cand["pid_config"],
                        "agg": agg,
                        "results": res_list,
                    })
                    # record candidate row
                    candidates_rows_global[family].append({
                        "multipliers": str(cand["multipliers"]),
                        "mean_rmse": agg["mean_rmse"],
                        "mean_score": agg["mean_score"],
                        "hard_fails": agg["hard_fails"],
                        "all_passed": agg["all_passed"],
                        "mean_effort": agg.get("mean_effort"),
                        "n_cases": agg["n_cases"],
                    })

                # Local refinement around top safe from first round
                safe_first = [e for e in evaluated if e["agg"]["all_passed"]]
                if safe_first:
                    safe_first.sort(key=lambda e: e["agg"]["mean_score"])
                    topk = safe_first[: min(3, len(safe_first))]
                    rng = np.random.RandomState(args.seed + 1)
                    added = 0
                    while added < args.refinement_candidates:
                        for t in topk:
                            if added >= args.refinement_candidates:
                                break
                            m0 = np.array(t["multipliers"])
                            pert = np.exp(rng.uniform(-0.18, 0.18, 4))
                            ms = np.clip(m0 * pert, 0.5, 2.0).tolist()
                            cand = {"multipliers": ms, "pid_config": {
                                k: (np.array(base_gains[k], dtype=float) * m).tolist()
                                for k, m in zip(["Kp_pos","Kd_pos","Kp_att","Kd_att"], ms)
                            }}
                            res_list = []
                            for case in cases:
                                try:
                                    tel, met = _run_pid_on_case(cand["pid_config"], case, family, tmp_root)
                                    passed, reason = passes_hard_filters(met, family)
                                    sc = pid_candidate_score(met, tel, family)
                                    res_list.append({"case": case, "metrics": met, "passed": passed, "score": sc, "reason": reason})
                                except Exception as exc:
                                    res_list.append({"case": case, "metrics": {"position_rmse_m": 999}, "passed": False, "score": 1e9, "reason": str(exc)})
                            agg = aggregate_diagnostic(res_list)
                            evaluated.append({
                                "multipliers": cand["multipliers"],
                                "pid_config": cand["pid_config"],
                                "agg": agg,
                                "results": res_list,
                            })
                            candidates_rows_global[family].append({
                                "multipliers": str(cand["multipliers"]),
                                "mean_rmse": agg["mean_rmse"],
                                "mean_score": agg["mean_score"],
                                "hard_fails": agg["hard_fails"],
                                "all_passed": agg["all_passed"],
                                "mean_effort": agg.get("mean_effort"),
                                "n_cases": agg["n_cases"],
                            })
                            added += 1

                # Final selection
                chosen_info = select_final_pid(initial_pid_config, evaluated)
                if chosen_info.get("chosen_pid") is None:
                    had_failure = True
                    failure_reasons[family] = "no_safe_candidate_after_search"
                    print(f"  ERROR: no safe candidate found for {family} after search.")
                    # record the tried candidates for report
                    for e in evaluated:
                        candidates_rows_global[family].append({
                            "multipliers": str(e["multipliers"]),
                            "mean_rmse": e["agg"]["mean_rmse"],
                            "mean_score": e["agg"]["mean_score"],
                            "hard_fails": e["agg"]["hard_fails"],
                            "all_passed": e["agg"]["all_passed"],
                            "mean_effort": e["agg"].get("mean_effort"),
                            "n_cases": e["agg"]["n_cases"],
                        })

            if chosen_info and chosen_info.get("chosen_pid") is not None:
                ch_pid = chosen_info.get("chosen_pid") or initial_pid_config
                family_reports[family] = {
                    "family": family,
                    "source": chosen_info["source"],
                    "reason": chosen_info.get("reason", tune_reason if do_tune else "accepted"),
                    "initial_agg": init_agg,
                    "chosen_agg": chosen_info.get("chosen_metrics", init_agg),
                    "chosen_pid": ch_pid,
                    "chosen_multipliers": chosen_info.get("chosen_multipliers"),
                    "n_cases": len(cases),
                    "search": {
                        "seed": args.seed,
                        "initial_candidates": args.initial_candidates,
                        "refinement_candidates": args.refinement_candidates,
                        "mult_range": [0.5, 2.0],
                        "rmse_thresh_used": rmse_thresh[family],
                    },
                    "diagnostic_cases": [
                        {
                            "geometry_id": c["geometry_id"],
                            "perturbation_id": c["perturbation_id"],
                            "initial_rmse": r["metrics"].get("position_rmse_m"),
                            "initial_passed": r["passed"],
                        }
                        for c, r in zip(cases, initial_results)
                    ],
                    "date": datetime.datetime.now().isoformat(),
                }

                pid_id = f"pid_{family}_{args.version}"
                pid_path = os.path.join(pids_out_dir, f"{pid_id}.yaml")
                pid_data = {
                    "pid_id": pid_id,
                    "family": family,
                    "version": args.version,
                    "source": family_reports[family]["source"],
                    "Kp_pos": ch_pid["Kp_pos"],
                    "Kd_pos": ch_pid["Kd_pos"],
                    "Kp_att": ch_pid["Kp_att"],
                    "Kd_att": ch_pid["Kd_att"],
                    "tuning_info": {
                        "date": family_reports[family]["date"],
                        "source": family_reports[family]["source"],
                        "reason": family_reports[family]["reason"],
                        "search_config": family_reports[family]["search"],
                        "initial_metrics": family_reports[family]["initial_agg"],
                        "chosen_metrics": family_reports[family].get("chosen_metrics", family_reports[family]["chosen_agg"]),
                        "diagnostic_set_size": family_reports[family]["n_cases"],
                        "diagnostic_geoms_profiles": [(c["geometry_id"], c["perturbation_id"]) for c in family_reports[family]["diagnostic_cases"]],
                    },
                }
                pid_writes_deferred.append((pid_path, pid_data))
                # also append chosen phase rows for diagnostic report
                for c, r in zip(cases, (chosen_info.get("results") or initial_results)):
                    # if we have per-cand results use them; else reuse initial for accepted
                    met = r["metrics"] if isinstance(r, dict) and "metrics" in r else r.get("metrics", {})
                    all_diagnostic_rows.append({
                        "family": family,
                        "geometry_id": c["geometry_id"],
                        "perturbation_id": c["perturbation_id"],
                        "scenario_id": c.get("scenario_id", ""),
                        "phase": "chosen",
                        "position_rmse_m": met.get("position_rmse_m") if isinstance(met, dict) else None,
                        "position_max_err_m": met.get("position_max_err_m") if isinstance(met, dict) else None,
                        "saturation_percentage": met.get("saturation_percentage") if isinstance(met, dict) else None,
                        "degradation_percentage": met.get("degradation_percentage") if isinstance(met, dict) else None,
                        "termination_reason": met.get("termination_reason") if isinstance(met, dict) else None,
                        "passed_hard": r.get("passed", True) if isinstance(r, dict) else True,
                        "hard_reason": r.get("reason", "OK") if isinstance(r, dict) else "OK",
                        "score": r.get("score") if isinstance(r, dict) else 0.0,
                    })

                # Per-family candidates csv (append what we have)
                if family not in candidates_rows_global or not candidates_rows_global[family]:
                    # at least record the initial
                    candidates_rows_global[family] = [{
                        "multipliers": "[1.0, 1.0, 1.0, 1.0]",
                        "mean_rmse": init_agg["mean_rmse"],
                        "mean_score": init_agg["mean_score"],
                        "hard_fails": init_agg["hard_fails"],
                        "all_passed": init_agg["all_passed"],
                        "mean_effort": init_agg.get("mean_effort"),
                        "n_cases": init_agg["n_cases"],
                    }]

            else:
                # failure already flagged
                pass

    # After all evals: decide on writes (atomic, only on success for processed families)
    if had_failure:
        # Write failure summary but do NOT write/overwrite any pid_<family> yamls
        fail_report = {
            "status": "partial_or_failed",
            "failures": failure_reasons,
            "date": datetime.datetime.now().isoformat(),
            "note": "No pid yamls were (re)written for failing families. Existing defaults (if any) remain.",
        }
        with open(os.path.join(pid_tuning_dir, "tune_failure_report.json"), "w") as f:
            json.dump(fail_report, f, indent=2)
        print("\nERROR: one or more families had no safe selectable PID. See tune_failure_report.json", file=sys.stderr)
        # Still write the diagnostic/candidates collected so far for inspection
        if all_diagnostic_rows:
            with open(os.path.join(pid_tuning_dir, "diagnostic_report.csv"), "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(all_diagnostic_rows[0].keys()))
                writer.writeheader()
                writer.writerows(all_diagnostic_rows)
        for fam, crows in candidates_rows_global.items():
            if crows:
                with open(os.path.join(pid_tuning_dir, f"candidates_{fam}.csv"), "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=list(crows[0].keys()))
                    writer.writeheader()
                    writer.writerows(crows)
        sys.exit(1)

    # SUCCESS: write the deferred PIDs
    for pid_path, pid_data in pid_writes_deferred:
        _write_atomic_yaml(pid_path, pid_data)
        print(f"  Wrote frozen PID: {pid_path} (source={pid_data['source']})")

    print("Writing shared diagnostic reports and summary...")

    # Write shared reports (diagnostic + per family candidates + summary)
    if all_diagnostic_rows:
        diag_csv = os.path.join(pid_tuning_dir, "diagnostic_report.csv")
        with open(diag_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_diagnostic_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_diagnostic_rows)
        print(f"Wrote {diag_csv}")

    for fam, crows in candidates_rows_global.items():
        if crows:
            cpath = os.path.join(pid_tuning_dir, f"candidates_{fam}.csv")
            with open(cpath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(crows[0].keys()))
                writer.writeheader()
                writer.writerows(crows)
            print(f"Wrote {cpath}")

    summary = {
        "version": args.version,
        "seed": args.seed,
        "date": datetime.datetime.now().isoformat(),
        "families_processed": list(family_reports.keys()),
        "thresholds": rmse_thresh,
        "per_family": {f: {"source": r["source"], "reason": r["reason"], "mean_rmse_chosen": r["chosen_metrics"]["mean_rmse"]} for f, r in family_reports.items()},
    }
    with open(os.path.join(pid_tuning_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {os.path.join(pid_tuning_dir, 'summary.json')}")

    print("\nTune/diagnostic complete. All requested families have a safe frozen PID.")
    # Exit 0


if __name__ == "__main__":
    main()
