import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
from simulador_quad.app import run_simulation


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
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
