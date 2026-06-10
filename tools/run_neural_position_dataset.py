"""
Ejecuta un conjunto de escenarios con controlador neuronal de lazo externo.
"""
import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

from run_neural_position_scenario import resolve_architecture, run_neural_position_scenario


def _run_row(row, dataset, checkpoint, normalization, architecture, device, no_visualization, rerun):
    scenario_id = row["scenario_id"]
    scenario_path = os.path.join(dataset, row["scenario_path"])
    out_dir = os.path.join(dataset, row["result_dir"] + f"_neural_position_{architecture}")
    metrics_file = os.path.join(out_dir, "metrics.json")

    if os.path.exists(metrics_file) and not rerun:
        return {"scenario_id": scenario_id, "status": "SKIPPED", "result_dir": out_dir}

    try:
        run_neural_position_scenario(
            scenario_path=scenario_path,
            checkpoint_path=checkpoint,
            normalization_path=normalization,
            architecture_override=architecture,
            device=device,
            out_dir=out_dir,
            visualization=not no_visualization,
        )
        status = "SUCCESS"
    except Exception as exc:
        status = f"FAILED: {exc}"
    return {"scenario_id": scenario_id, "status": status, "result_dir": out_dir}


def main():
    parser = argparse.ArgumentParser(description="Run dataset scenarios with a neural position-loop controller.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory with manifest.csv.")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--normalization", type=str, required=True)
    parser.add_argument("--architecture", type=str, choices=["mlp", "gru", "lstm"], help="Override architecture from config.yaml.")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--family", type=str, help="Filter by family")
    parser.add_argument("--split", type=str, help="Filter by split")
    parser.add_argument("--scenario-id", type=str, help="Filter by specific scenario ID")
    parser.add_argument("--limit", type=int, help="Limit number of simulations")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel scenario processes.")
    parser.add_argument("--no-visualization", action="store_true", help="Disable visualizations")
    parser.add_argument("--rerun", action="store_true", help="Rerun already completed simulations")
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first error (only when --workers 1; ignored in parallel mode).",
    )
    args = parser.parse_args()

    if args.workers < 1:
        raise ValueError("--workers must be >= 1")
    if args.workers > 1 and args.fail_fast:
        raise ValueError("--fail-fast requires --workers 1")
    if args.workers > 1 and args.device == "cuda":
        print("Warning: multiple workers will load independent model copies on the same CUDA device.")

    manifest_path = os.path.join(args.dataset, "manifest.csv")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")

    architecture = resolve_architecture(args.checkpoint, args.architecture)
    df = pd.read_csv(manifest_path)
    if args.family:
        df = df[df["family"] == args.family]
    if args.split:
        df = df[df["split"] == args.split]
    if args.scenario_id:
        df = df[df["scenario_id"] == args.scenario_id]
    if args.limit:
        df = df.head(args.limit)

    rows = [row.to_dict() for _, row in df.iterrows()]
    total = len(rows)
    print(f"Total scenarios to run: {total}")
    print(f"Using architecture={architecture}, device={args.device}, workers={args.workers}")

    report = []
    if args.workers == 1:
        for index, row in enumerate(rows, start=1):
            print(f"[{index}/{total}] Running {row['scenario_id']}...")
            result = _run_row(
                row,
                args.dataset,
                args.checkpoint,
                args.normalization,
                architecture,
                args.device,
                args.no_visualization,
                args.rerun,
            )
            print(f"[{index}/{total}] {result['scenario_id']}: {result['status']}")
            report.append(result)
            if result["status"].startswith("FAILED") and args.fail_fast:
                break
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(
                    _run_row,
                    row,
                    args.dataset,
                    args.checkpoint,
                    args.normalization,
                    architecture,
                    args.device,
                    args.no_visualization,
                    args.rerun,
                )
                for row in rows
            ]
            for index, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                print(f"[{index}/{total}] {result['scenario_id']}: {result['status']}")
                report.append(result)

    report_path = os.path.join(args.dataset, f"run_report_neural_position_{architecture}.csv")
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
