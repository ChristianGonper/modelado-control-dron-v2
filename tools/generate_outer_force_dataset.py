"""
Generate outer_force_dataset from source classic + outer pid bank.
Selects one expert PID per scenario (RMSE +5% + conservative).
Writes manifest.csv + scenarios/ + results/ (telemetry copies) + README.
"""

import argparse
import csv
import os
import json
import shutil
import yaml
import pandas as pd
import numpy as np
import ast
from simulador_quad.core.fs import atomic_write_directory

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dataset", required=True)
    parser.add_argument("--pid-bank", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--allow-synthetic-placeholder", action="store_true")
    args = parser.parse_args()

    # We read inputs BEFORE entering the atomic write block
    src_m = os.path.join(args.source_dataset, "manifest.csv")
    if not os.path.exists(src_m):
        if args.allow_synthetic_placeholder:
            src_manifest = pd.DataFrame([{
                "scenario_id": "synth1",
                "family": "hold",
                "split": "train",
                "result_dir": "results/s1",
                "scenario_path": "scenarios/hold/s1.yaml"
            }])
        else:
            raise FileNotFoundError(
                f"Source classic dataset manifest not found at: {src_m}. "
                "Please generate the classic dataset first, or pass --allow-synthetic-placeholder."
            )
    else:
        src_manifest = pd.read_csv(src_m)

    bank_manifest_path = os.path.join(args.pid_bank, "pid_bank_manifest.csv")
    if not os.path.exists(bank_manifest_path):
        if args.allow_synthetic_placeholder:
            # Create a mock/empty bank manifest dataframe
            bank_manifest = pd.DataFrame(columns=[
                "pid_id", "source_scenario_id", "family", "variant", "pid_path",
                "result_dir", "mean_score", "position_rmse_m", "control_effort",
                "valid_cases", "total_cases", "Kp_pos", "Kd_pos", "passed_filter"
            ])
        else:
            raise FileNotFoundError(
                f"PID bank manifest not found at: {bank_manifest_path}. "
                "Please generate the outer force PID bank first, or pass --allow-synthetic-placeholder."
            )
    else:
        bank_manifest = pd.read_csv(bank_manifest_path)

    # Let's perform all evaluations and reads first (strict validations)
    rows_to_generate = []

    for _, srow in src_manifest.iterrows():
        # Validate source manifest row required fields
        required_fields = ["scenario_id", "family", "scenario_path", "result_dir", "split"]
        missing_fields = [f for f in required_fields if f not in srow or pd.isna(srow[f])]
        if missing_fields:
            if not args.allow_synthetic_placeholder:
                raise ValueError(
                    f"Source manifest row has missing required field(s): {missing_fields}. "
                    f"Row content: {srow.to_dict()}"
                )

        fam = srow.get("family", "hold")
        source_sid = srow.get("scenario_id", "unknown")

        # Verify source scenario file
        src_scen = os.path.join(args.source_dataset, str(srow.get("scenario_path", "")))
        if not os.path.exists(src_scen):
            if not args.allow_synthetic_placeholder:
                raise FileNotFoundError(
                    f"Source scenario file not found at: {src_scen} for scenario '{source_sid}'."
                )

        # Retrieve candidates
        candidates = bank_manifest[bank_manifest.get("source_scenario_id", "") == source_sid]
        if len(candidates) == 0:
            if args.allow_synthetic_placeholder:
                # Stub candidate
                chosen = {
                    "pid_id": f"outer_{source_sid}_synthetic",
                    "variant": "base",
                    "pid_path": None,
                    "Kp_pos": [2.0, 2.0, 5.0],
                    "Kd_pos": [1.0, 1.0, 2.0],
                    "passed_filter": True,
                    "result_dir": "results/synth"
                }
            else:
                raise ValueError(
                    f"No PID candidates found with exact source_scenario_id '{source_sid}' in the bank manifest."
                )
        else:
            # Expert selection
            def _select_expert_spec(cands):
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
                        c["control_effort"] = c.get("mean_score", 999)

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

        # Parse Kp/Kd POS
        chosen_kp = None
        chosen_kd = None

        # authoritative check in bank pids/ folder
        if "pid_path" in chosen and pd.notna(chosen["pid_path"]) and chosen["pid_path"]:
            pid_yaml_path = os.path.join(args.pid_bank, chosen["pid_path"])
            if os.path.exists(pid_yaml_path):
                with open(pid_yaml_path) as pf:
                    pid_data = yaml.safe_load(pf) or {}
                chosen_kp = pid_data.get("Kp_pos")
                chosen_kd = pid_data.get("Kd_pos")
            elif not args.allow_synthetic_placeholder:
                raise FileNotFoundError(
                    f"PID candidate gains file not found at: {pid_yaml_path} for PID '{chosen.get('pid_id')}'."
                )

        # Fallback to manifest columns
        if chosen_kp is None or chosen_kd is None:
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

        # Strict checks
        def validate_gains(gains):
            if gains is None:
                return False
            if not isinstance(gains, list) or len(gains) != 3:
                return False
            if not all(isinstance(x, (int, float)) for x in gains):
                return False
            return True

        if not (validate_gains(chosen_kp) and validate_gains(chosen_kd)):
            if args.allow_synthetic_placeholder:
                chosen_kp = chosen_kp or [2.0, 2.0, 5.0]
                chosen_kd = chosen_kd or [1.0, 1.0, 2.0]
            else:
                raise ValueError(
                    f"Could not retrieve valid 3-element float lists for Kp_pos ({chosen_kp}) "
                    f"and Kd_pos ({chosen_kd}) from bank or manifest for scenario '{source_sid}'."
                )

        # Check telemetry file
        bank_result_dir = chosen.get("result_dir")
        expert_telemetry_source_path = None
        if bank_result_dir and pd.notna(bank_result_dir):
            bank_res = os.path.join(args.pid_bank, bank_result_dir)
            if os.path.isdir(bank_res):
                # Look inside subfolders (exec_*) first
                for sub in sorted(os.listdir(bank_res)):
                    cand = os.path.join(bank_res, sub, "telemetry.json")
                    if os.path.exists(cand):
                        expert_telemetry_source_path = cand
                        break
            if expert_telemetry_source_path is None:
                cand = os.path.join(bank_res, "telemetry.json")
                if os.path.exists(cand):
                    expert_telemetry_source_path = cand

        if expert_telemetry_source_path is None:
            if args.allow_synthetic_placeholder:
                # Minimal fallback or stub minimal telemetry (only in synthetic mode)
                src_res = os.path.join(args.source_dataset, str(srow.get("result_dir", "")), "telemetry.json")
                if os.path.exists(src_res):
                    expert_telemetry_source_path = src_res
            else:
                raise FileNotFoundError(
                    f"Expert telemetry file not found in bank result directory '{bank_result_dir}' "
                    f"for candidate '{chosen.get('pid_id')}' in scenario '{source_sid}'."
                )

        # If we reached here, the inputs for this row are valid and complete!
        rows_to_generate.append({
            "srow": srow,
            "fam": fam,
            "sid": source_sid,
            "chosen": chosen,
            "chosen_kp": chosen_kp,
            "chosen_kd": chosen_kd,
            "src_scen": src_scen,
            "expert_telemetry_source_path": expert_telemetry_source_path
        })

    # Now define the write_func for atomic replacement
    def write_dataset(temp_dir):
        os.makedirs(os.path.join(temp_dir, "scenarios"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "results"), exist_ok=True)

        manifest_rows = []
        for item in rows_to_generate:
            srow = item["srow"]
            fam = item["fam"]
            sid = item["sid"]
            chosen = item["chosen"]
            chosen_kp = item["chosen_kp"]
            chosen_kd = item["chosen_kd"]
            src_scen = item["src_scen"]
            telemetry_path = item["expert_telemetry_source_path"]

            out_scenario_id = f"{sid}_outer_expert"
            out_scen_dir = os.path.join(temp_dir, "scenarios", fam)
            os.makedirs(out_scen_dir, exist_ok=True)
            out_scen = os.path.join(out_scen_dir, f"{out_scenario_id}.yaml")

            # Copy scenario inject gains
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
                # Fallback only for synthetic placeholder
                with open(out_scen, "w") as f:
                    yaml.dump({
                        "vehicle": {"mass_kg": 1.0, "gravity_m_s2": 9.81},
                        "controller": {"Kp_pos": chosen_kp, "Kd_pos": chosen_kd}
                    }, f)

            # Copy telemetry
            res_dir = os.path.join(temp_dir, "results", out_scenario_id)
            os.makedirs(res_dir, exist_ok=True)

            if telemetry_path and os.path.exists(telemetry_path):
                shutil.copy(telemetry_path, os.path.join(res_dir, "telemetry.json"))
            else:
                # Stub only in synthetic mode
                stub = [
                    {"time_s": 0.0, "observation": {"position_W_m": [0,0,1], "velocity_W_m_s": [0,0,0], "orientation_WB": [1,0,0,0], "angular_velocity_B_rad_s": [0,0,0]}, "reference": {"position_W_m": [0,0,1], "velocity_W_m_s": [0,0,0], "acceleration_W_m_s2": [0,0,0], "yaw_rad": 0.0}},
                    {"time_s": 0.1, "observation": {"position_W_m": [0.01,0,1], "velocity_W_m_s": [0.1,0,0], "orientation_WB": [1,0,0,0], "angular_velocity_B_rad_s": [0,0,0]}, "reference": {"position_W_m": [0,0,1], "velocity_W_m_s": [0,0,0], "acceleration_W_m_s2": [0,0,0], "yaw_rad": 0.0}},
                ]
                with open(os.path.join(res_dir, "telemetry.json"), "w") as f:
                    json.dump(stub, f)

            manifest_rows.append({
                "scenario_id": out_scenario_id,
                "source_scenario_id": sid,
                "family": fam,
                "chosen_pid_id": chosen["pid_id"],
                "chosen_variant": chosen["variant"],
                "split": srow.get("split", "train"),
                "scenario_path": os.path.relpath(out_scen, temp_dir),
                "result_dir": os.path.relpath(res_dir, temp_dir),
                "Kp_pos": chosen_kp,
                "Kd_pos": chosen_kd,
            })

        # Save manifest.csv
        pd.DataFrame(manifest_rows).to_csv(os.path.join(temp_dir, "manifest.csv"), index=False)

        # Save README.md
        with open(os.path.join(temp_dir, "README.md"), "w") as f:
            f.write("# Outer force dataset\n\n")
            f.write("Generated from TFG post-audit strict script.\n")
            f.write(f"Source: {args.source_dataset}\nBank: {args.pid_bank}\nN episodes: {len(manifest_rows)}\n")
            if args.allow_synthetic_placeholder:
                f.write("Note: Generated in --allow-synthetic-placeholder mode.\n")

    # Call atomic write directory
    atomic_write_directory(args.out, write_dataset, args.overwrite)
    print(f"Outer force dataset written to {args.out}")

if __name__ == "__main__":
    main()
