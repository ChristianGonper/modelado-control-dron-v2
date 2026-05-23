"""
Genera escenarios de entrenamiento para la red de ganancias a partir de un banco de PIDs.

El resultado conserva manifest.csv compatible con tools/run_classic_dataset.py.
Cada episodio indica el PID experto usado mediante pid_id y pid_variant.
"""
import argparse
import csv
import os
import yaml
import pandas as pd

from simulador_quad.datasets.classic import build_scenario_config


def main():
    parser = argparse.ArgumentParser(description="Generate a position-gain dataset from a PID bank.")
    parser.add_argument("--source-dataset", required=True, help="Dataset clasico base con manifest/scenarios.")
    parser.add_argument("--pid-bank", required=True, help="Directorio con pid_bank_manifest.csv y pids/")
    parser.add_argument("--out", required=True, help="Dataset de salida compatible con run_classic_dataset.py")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if os.path.exists(args.out) and not args.overwrite:
        raise FileExistsError(f"Directory {args.out} already exists. Use --overwrite to force.")
    os.makedirs(args.out, exist_ok=True)

    source_manifest = pd.read_csv(os.path.join(args.source_dataset, "manifest.csv"))
    bank_manifest = pd.read_csv(os.path.join(args.pid_bank, "pid_bank_manifest.csv"))
    rows = []

    for _, source_row in source_manifest.iterrows():
        source_scenario_path = os.path.join(args.source_dataset, source_row["scenario_path"])
        with open(source_scenario_path, "r") as f:
            source_scenario = yaml.safe_load(f)

        family = source_row["family"]
        family_pids = bank_manifest[bank_manifest["family"] == family]

        for _, bank_row in family_pids.iterrows():
            pid_path = os.path.join(args.pid_bank, bank_row["pid_path"])
            with open(pid_path, "r") as f:
                pid_data = yaml.safe_load(f)

            pid_config = {key: pid_data[key] for key in ("Kp_pos", "Kd_pos", "Kp_att", "Kd_att") if key in pid_data}
            scenario_id = f"{source_row['scenario_id']}_{bank_row['variant']}"
            scenario_config = build_scenario_config(
                scenario_id=scenario_id,
                family=family,
                trajectory_cfg=source_scenario["trajectory"],
                profile_id=source_row["perturbation_id"],
                pid_config=pid_config,
                seed=int(source_row["seed"]),
                output_root=args.out,
            )

            family_dir = os.path.join(args.out, "scenarios", family)
            os.makedirs(family_dir, exist_ok=True)
            scenario_path = os.path.join(family_dir, f"{scenario_id}.yaml")
            with open(scenario_path, "w") as f:
                yaml.dump(scenario_config, f, sort_keys=False)

            rows.append({
                "scenario_id": scenario_id,
                "source_scenario_id": source_row["scenario_id"],
                "family": family,
                "geometry_id": source_row["geometry_id"],
                "perturbation_id": source_row["perturbation_id"],
                "pid_id": bank_row["pid_id"],
                "pid_variant": bank_row["variant"],
                "seed": int(source_row["seed"]),
                "split": source_row["split"],
                "scenario_path": os.path.relpath(scenario_path, args.out),
                "result_dir": os.path.relpath(scenario_config["output"]["dir"], args.out),
            })

    with open(os.path.join(args.out, "manifest.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(os.path.join(args.out, "README.md"), "w") as f:
        f.write("# Position gain dataset from PID bank\n\n")
        f.write(f"Source dataset: {args.source_dataset}\n")
        f.write(f"PID bank: {args.pid_bank}\n")
        f.write(f"Total episodes: {len(rows)}\n")

    print(f"Position gain dataset written to {args.out}")
    print(f"Total episodes: {len(rows)}")


if __name__ == "__main__":
    main()
