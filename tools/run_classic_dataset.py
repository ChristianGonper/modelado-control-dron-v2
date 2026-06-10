import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import yaml
from simulador_quad.app import run_simulation


PID_FIELDS = ("Kp_pos", "Kd_pos", "Kp_att", "Kd_att", "max_body_moments_Nm")


def _find_stale_scenarios(rows, dataset):
    """Return scenarios whose embedded controller differs from their frozen PID."""
    pid_cache = {}
    stale = []
    for row in rows:
        if not row.get("pid_id"):
            continue
        pid_id = row["pid_id"]
        if pid_id not in pid_cache:
            pid_path = os.path.join(dataset, "pids", f"{pid_id}.yaml")
            with open(pid_path, encoding="utf-8") as f:
                pid_data = yaml.safe_load(f) or {}
            pid_cache[pid_id] = {key: pid_data[key] for key in PID_FIELDS if key in pid_data}

        scenario_path = os.path.join(dataset, row["scenario_path"])
        if not os.path.exists(scenario_path):
            continue
        with open(scenario_path, encoding="utf-8") as f:
            scenario = yaml.safe_load(f) or {}
        controller = scenario.get("controller", {})
        expected = pid_cache[pid_id]
        if any(controller.get(key) != value for key, value in expected.items()):
            stale.append(row["scenario_id"])
    return stale


def _run_row(row, dataset, no_visualization, rerun):
    scenario_id = row["scenario_id"]
    scenario_path = os.path.join(dataset, row["scenario_path"])
    result_dir = os.path.join(dataset, row["result_dir"])
    metrics_file = os.path.join(result_dir, "metrics.json")

    if os.path.exists(metrics_file) and not rerun:
        return {
            "scenario_id": scenario_id,
            "status": "SKIPPED",
            "result_dir": row["result_dir"],
        }

    try:
        run_simulation(scenario_path, visualization=not no_visualization)
        status = "SUCCESS"
    except Exception as exc:
        status = f"FAILED: {exc}"
    return {
        "scenario_id": scenario_id,
        "status": status,
        "result_dir": row["result_dir"],
    }


def main():
    parser = argparse.ArgumentParser(description="Run classical control dataset simulations.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory (containing manifest.csv)")
    parser.add_argument("--family", type=str, help="Filter by family")
    parser.add_argument("--scenario-id", type=str, help="Filter by specific scenario ID")
    parser.add_argument("--limit", type=int, help="Limit number of simulations")
    parser.add_argument("--no-visualization", action="store_true", help="Disable visualizations")
    parser.add_argument("--rerun", action="store_true", help="Rerun already completed simulations")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first error")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel scenario processes.")
    
    args = parser.parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be >= 1")
    if args.workers > 1 and args.fail_fast:
        raise ValueError("--fail-fast requires --workers 1")
    
    manifest_path = os.path.join(args.dataset, "manifest.csv")
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        return
        
    df = pd.read_csv(manifest_path)
    
    # Filters
    if args.family:
        df = df[df["family"] == args.family]
    if args.scenario_id:
        df = df[df["scenario_id"] == args.scenario_id]
    if args.limit:
        df = df.head(args.limit)
        
    total = len(df)
    print(f"Total scenarios to run: {total}")
    
    report = []

    rows = [row.to_dict() for _, row in df.iterrows()]
    try:
        stale_scenarios = _find_stale_scenarios(rows, args.dataset)
    except Exception as exc:
        print(f"Error validating scenario PID consistency: {exc}", file=sys.stderr)
        sys.exit(1)
    if stale_scenarios:
        examples = ", ".join(stale_scenarios[:3])
        print(
            f"Error: {len(stale_scenarios)} scenario YAML(s) do not contain their frozen PID gains "
            f"(examples: {examples}).",
            file=sys.stderr,
        )
        print(
            "Regenerate scenarios before running: "
            f"uv run python tools/generate_classic_dataset.py --version v1 --out {args.dataset} --overwrite",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.workers == 1:
        for index, row in enumerate(rows, start=1):
            print(f"[{index}/{total}] Running {row['scenario_id']}...")
            result = _run_row(row, args.dataset, args.no_visualization, args.rerun)
            if result["status"] == "SKIPPED":
                print(f"[{index}/{total}] Skipping {row['scenario_id']} (already exists)")
            elif result["status"].startswith("FAILED"):
                print(f"Error running {row['scenario_id']}: {result['status']}")
                report.append(result)
                if args.fail_fast:
                    break
                continue
            report.append(result)
    else:
        print(f"Running with {args.workers} worker processes.")
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(_run_row, row, args.dataset, args.no_visualization, args.rerun)
                for row in rows
            ]
            for index, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                print(f"[{index}/{total}] {result['scenario_id']}: {result['status']}")
                report.append(result)
        
    # Save run report
    report_path = os.path.join(args.dataset, "run_report.csv")
    report_df = pd.DataFrame(report)
    if os.path.exists(report_path):
        old_report = pd.read_csv(report_path)
        report_df = pd.concat([old_report, report_df]).drop_duplicates("scenario_id", keep="last")
    
    report_df.to_csv(report_path, index=False)
    print(f"Run report saved to {report_path}")

    # Exit with error if any scenario failed in this run
    if any(r["status"].startswith("FAILED") for r in report):
        print("Error: One or more simulation runs failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
