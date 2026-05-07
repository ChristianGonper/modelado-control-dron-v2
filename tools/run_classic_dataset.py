import argparse
import os
import pandas as pd
from simulador_quad.app import run_simulation

def main():
    parser = argparse.ArgumentParser(description="Run classical control dataset simulations.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory (containing manifest.csv)")
    parser.add_argument("--family", type=str, help="Filter by family")
    parser.add_argument("--scenario-id", type=str, help="Filter by specific scenario ID")
    parser.add_argument("--limit", type=int, help="Limit number of simulations")
    parser.add_argument("--no-visualization", action="store_true", help="Disable visualizations")
    parser.add_argument("--rerun", action="store_true", help="Rerun already completed simulations")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first error")
    
    args = parser.parse_args()
    
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
        
    count = 0
    total = len(df)
    print(f"Total scenarios to run: {total}")
    
    report = []
    
    for _, row in df.iterrows():
        if args.limit and count >= args.limit:
            break
            
        scenario_path = os.path.join(args.dataset, row["scenario_path"])
        result_dir = os.path.join(args.dataset, row["result_dir"])
        metrics_file = os.path.join(result_dir, "metrics.json")
        
        if os.path.exists(metrics_file) and not args.rerun:
            print(f"[{count+1}/{total}] Skipping {row['scenario_id']} (already exists)")
            count += 1
            continue
            
        print(f"[{count+1}/{total}] Running {row['scenario_id']}...")
        
        try:
            run_simulation(scenario_path, visualization=not args.no_visualization)
            status = "SUCCESS"
        except Exception as e:
            print(f"Error running {row['scenario_id']}: {e}")
            status = f"FAILED: {e}"
            if args.fail_fast:
                break
        
        report.append({"scenario_id": row["scenario_id"], "status": status})
        count += 1
        
    # Save run report
    report_path = os.path.join(args.dataset, "run_report.csv")
    report_df = pd.DataFrame(report)
    if os.path.exists(report_path):
        old_report = pd.read_csv(report_path)
        report_df = pd.concat([old_report, report_df]).drop_duplicates("scenario_id", keep="last")
    
    report_df.to_csv(report_path, index=False)
    print(f"Run report saved to {report_path}")

if __name__ == "__main__":
    main()
