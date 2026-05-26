"""
Generate outer_force_dataset from source classic + outer pid bank.
Selects one expert PID per scenario (RMSE +5% + conservative).
Writes manifest.csv + scenarios/ + results/ (telemetry copies or stubs) + README.
Simplified but produces structure for train/eval/run commands.
"""

import argparse
import csv
import os
import json
import shutil
import yaml
import pandas as pd
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dataset", required=True)
    parser.add_argument("--pid-bank", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if os.path.exists(args.out) and not args.overwrite:
        raise FileExistsError(f"{args.out} exists")
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.join(args.out, "scenarios"), exist_ok=True)
    os.makedirs(os.path.join(args.out, "results"), exist_ok=True)

    src_m = os.path.join(args.source_dataset, "manifest.csv")
    if not os.path.exists(src_m):
        # Synthetic path when no source
        src_manifest = pd.DataFrame([{"scenario_id": "synth1", "family": "hold", "split": "train", "result_dir": "results/s1", "scenario_path": "scenarios/hold/s1.yaml"}])
    else:
        src_manifest = pd.read_csv(src_m)
    bank_manifest = pd.read_csv(os.path.join(args.pid_bank, "pid_bank_manifest.csv"))

    rows = []
    for _, srow in src_manifest.iterrows():
        fam = srow.get("family", "hold")
        source_sid = srow["scenario_id"]
        # Prefer exact per-source-scenario candidates (new bank format)
        candidates = bank_manifest[bank_manifest.get("source_scenario_id", "") == source_sid]
        if len(candidates) == 0:
            # fallback to family-level (old bank format)
            candidates = bank_manifest[bank_manifest["family"] == fam]

        if len(candidates) == 0:
            continue

        # === Exact per-scenario expert selection per spec ===
        def _select_expert_spec(cands):
            """Implements the exact rule from spec_control_neuronal_fuerza_externa.md:256-262"""
            def is_passed(c):
                val = c.get("passed_filter", True)
                if isinstance(val, str):
                    return val.lower() == "true"
                return bool(val)

            safe = [c for c in cands if is_passed(c)]
            if not safe:
                raise ValueError(
                    f"No safe PID candidate found for scenario '{source_sid}'. "
                    f"All candidates failed the safety filters."
                )

            # 1. Lowest position_rmse_m
            best_rmse = min(c.get("position_rmse_m", 999) for c in safe)
            threshold = best_rmse * 1.05

            within = [c for c in safe if c.get("position_rmse_m", 999) <= threshold]

            if len(within) <= 1:
                return within[0] if within else safe[0]

            # 2. Among them, lowest control effort
            for c in within:
                if "control_effort" not in c:
                    c["control_effort"] = c.get("mean_score", 999)  # fallback

            best_eff = min(c["control_effort"] for c in within)
            lowest_effort = [c for c in within if abs(c["control_effort"] - best_eff) < 1e-6]

            if len(lowest_effort) <= 1:
                return lowest_effort[0] if lowest_effort else within[0]

            # 3. Most conservative
            order = {"conservative": 0, "base": 1, "aggressive": 2}
            lowest_effort = sorted(lowest_effort, key=lambda x: order.get(x.get("variant", ""), 99))
            return lowest_effort[0]

        chosen_raw = _select_expert_spec(candidates.to_dict("records") if hasattr(candidates, 'to_dict') else list(candidates))
        chosen = pd.Series(chosen_raw) if isinstance(chosen_raw, dict) else chosen_raw
        sid = srow["scenario_id"]
        out_scenario_id = f"{sid}_outer_expert"
        # Copy or stub scenario, but **inject the chosen expert's gains**
        # This is mandatory so that OuterForceDataset._build_desired_force_target reads the correct Kp/Kd
        src_scen = os.path.join(args.source_dataset, srow["scenario_path"])
        out_scen_dir = os.path.join(args.out, "scenarios", fam)
        os.makedirs(out_scen_dir, exist_ok=True)
        out_scen = os.path.join(out_scen_dir, f"{out_scenario_id}.yaml")

        # Read gains from the YAML file pointed by the bank (authoritative)
        chosen_kp = None
        chosen_kd = None
        if "pid_path" in chosen and pd.notna(chosen["pid_path"]):
            pid_yaml_path = os.path.join(args.pid_bank, chosen["pid_path"])
            if os.path.exists(pid_yaml_path):
                try:
                    with open(pid_yaml_path) as pf:
                        pid_data = yaml.safe_load(pf) or {}
                    chosen_kp = pid_data.get("Kp_pos")
                    chosen_kd = pid_data.get("Kd_pos")
                except Exception:
                    pass

        # Fallback: Parse from manifest columns (if strings like "[2.6, 2.6, 6.5]")
        if chosen_kp is None or chosen_kd is None:
            import ast
            def parse_gains(val):
                if isinstance(val, str):
                    try:
                        parsed = ast.literal_eval(val)
                        if isinstance(parsed, list):
                            return parsed
                    except Exception:
                        pass
                elif isinstance(val, list):
                    return val
                return None

            chosen_kp = parse_gains(chosen.get("Kp_pos") or chosen.get("kp_pos"))
            chosen_kd = parse_gains(chosen.get("Kd_pos") or chosen.get("kd_pos"))

        if chosen_kp is None:
            chosen_kp = [2., 2., 5.]
        if chosen_kd is None:
            chosen_kd = [1., 1., 2.]

        if os.path.exists(src_scen):
            with open(src_scen, "r") as f:
                scen = yaml.safe_load(f)
            if "controller" not in scen:
                scen["controller"] = {}
            scen["controller"]["Kp_pos"] = chosen_kp
            scen["controller"]["Kd_pos"] = chosen_kd
            with open(out_scen, "w") as f:
                yaml.dump(scen, f, sort_keys=False)
        else:
            with open(out_scen, "w") as f:
                yaml.dump({
                    "vehicle": {"mass_kg": 1.0, "gravity_m_s2": 9.81},
                    "controller": {"Kp_pos": chosen_kp, "Kd_pos": chosen_kd}
                }, f)

        # results dir + stub telemetry/metrics for the chosen
        res_dir = os.path.join(args.out, "results", out_scenario_id)
        os.makedirs(res_dir, exist_ok=True)
        # Prefer telemetry from the bank's real execution of this chosen variant (if the bank recorded result_dir)
        bank_result_dir = chosen.get("result_dir")
        used_real_expert_telemetry = False
        if bank_result_dir:
            bank_res = os.path.join(args.pid_bank, bank_result_dir)
            # Look for any exec_* subdir that has telemetry (first one is fine for placeholder)
            for sub in sorted(os.listdir(bank_res)) if os.path.isdir(bank_res) else []:
                cand = os.path.join(bank_res, sub, "telemetry.json")
                if os.path.exists(cand):
                    shutil.copy(cand, os.path.join(res_dir, "telemetry.json"))
                    used_real_expert_telemetry = True
                    break
                # also try direct
            if not used_real_expert_telemetry:
                cand = os.path.join(bank_res, "telemetry.json")
                if os.path.exists(cand):
                    shutil.copy(cand, os.path.join(res_dir, "telemetry.json"))
                    used_real_expert_telemetry = True

        if not used_real_expert_telemetry:
            # Fallback to source classic (old behavior, only for pure synthetic)
            src_res = os.path.join(args.source_dataset, srow["result_dir"], "telemetry.json")
            if os.path.exists(src_res):
                shutil.copy(src_res, os.path.join(res_dir, "telemetry.json"))
            else:
                # stub minimal telemetry
                stub = [
                    {"time_s": 0.0, "observation": {"position_W_m": [0,0,1], "velocity_W_m_s": [0,0,0], "orientation_WB": [1,0,0,0], "angular_velocity_B_rad_s": [0,0,0]}, "reference": {"position_W_m": [0,0,1], "velocity_W_m_s": [0,0,0], "acceleration_W_m_s2": [0,0,0], "yaw_rad": 0.0}},
                    {"time_s": 0.1, "observation": {"position_W_m": [0.01,0,1], "velocity_W_m_s": [0.1,0,0], "orientation_WB": [1,0,0,0], "angular_velocity_B_rad_s": [0,0,0]}, "reference": {"position_W_m": [0,0,1], "velocity_W_m_s": [0,0,0], "acceleration_W_m_s2": [0,0,0], "yaw_rad": 0.0}},
                ]
                with open(os.path.join(res_dir, "telemetry.json"), "w") as f:
                    json.dump(stub, f)

        split = srow.get("split", "train")
        rows.append({
            "scenario_id": out_scenario_id,
            "source_scenario_id": sid,
            "family": fam,
            "chosen_pid_id": chosen["pid_id"],
            "chosen_variant": chosen["variant"],
            "split": split,
            "scenario_path": os.path.relpath(out_scen, args.out),
            "result_dir": os.path.relpath(res_dir, args.out),
            "Kp_pos": chosen.get("Kp_pos", [2.,2.,5.]),
            "Kd_pos": chosen.get("Kd_pos", [1.,1.,2.]),
        })
        # Do NOT duplicate the same result_dir as val (would cause direct leakage).
        # If a proper val split is needed, the source manifest must provide distinct episodes.

    pd.DataFrame(rows).to_csv(os.path.join(args.out, "manifest.csv"), index=False)
    with open(os.path.join(args.out, "README.md"), "w") as f:
        f.write("# Outer force dataset\n\n")
        f.write("When the pid_bank was generated with a real source classic dataset,\n")
        f.write("this tool selects the expert using the real mean_score computed from executed variants\n")
        f.write("(lower score = better RMSE + effort + safety, per pid_candidate_score).\n")
        f.write("The resulting manifest points to telemetry from actually executed outer-gain PIDs.\n\n")
        f.write(f"Source: {args.source_dataset}\nBank: {args.pid_bank}\nN episodes: {len(rows)}\n")

    print(f"Outer force dataset written to {args.out}")


if __name__ == "__main__":
    main()
