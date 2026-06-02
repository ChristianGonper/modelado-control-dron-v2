"""
Aggregate closed-loop metrics.json files into comparison_closed_loop_v1.csv.

Each input row points to a result directory (relative or absolute) with metrics.json.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd


METRIC_COLUMNS = [
    "scenario_id",
    "controller",
    "split",
    "result_dir",
    "position_rmse_m",
    "position_mae_m",
    "position_max_err_m",
    "termination_reason",
    "saturation_percentage",
    "degradation_percentage",
    "force_norm_clip_percentage",
    "force_tilt_clip_percentage",
    "git_commit",
    "command",
]


def _load_metrics_row(
    scenario_id: str,
    controller: str,
    split: str,
    result_dir: str,
) -> dict | None:
    metrics_path = Path(result_dir) / "metrics.json"
    if not metrics_path.exists():
        return None
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    meta = metrics.get("metadata", {}) or {}
    return {
        "scenario_id": scenario_id,
        "controller": controller,
        "split": split,
        "result_dir": str(result_dir),
        "position_rmse_m": metrics.get("position_rmse_m"),
        "position_mae_m": metrics.get("position_mae_m"),
        "position_max_err_m": metrics.get("position_max_err_m"),
        "termination_reason": metrics.get("termination_reason"),
        "saturation_percentage": metrics.get("saturation_percentage"),
        "degradation_percentage": metrics.get("degradation_percentage"),
        "force_norm_clip_percentage": metrics.get("force_norm_clip_percentage"),
        "force_tilt_clip_percentage": metrics.get("force_tilt_clip_percentage"),
        "git_commit": meta.get("git_commit"),
        "command": meta.get("command"),
    }


def _manifest_result_dir_map(dataset_root: str) -> dict[str, str]:
    manifest_path = os.path.join(dataset_root, "manifest.csv")
    if not os.path.exists(manifest_path):
        return {}
    manifest = pd.read_csv(manifest_path)
    if "scenario_id" not in manifest.columns or "result_dir" not in manifest.columns:
        return {}
    return dict(zip(manifest["scenario_id"].astype(str), manifest["result_dir"].astype(str)))


def _resolve_result_dir(
    row: pd.Series,
    dataset_root: str,
    manifest_map: dict[str, str],
) -> str | None:
    result_dir = row.get("result_dir")
    if result_dir is not None and pd.notna(result_dir) and str(result_dir).strip():
        resolved = str(result_dir)
    else:
        scenario_id = str(row.get("scenario_id", ""))
        resolved = manifest_map.get(scenario_id)
        if not resolved:
            return None
    if not os.path.isabs(resolved):
        resolved = os.path.join(dataset_root, resolved)
    return resolved


def _rows_from_run_report(
    report_path: str,
    dataset_root: str,
    controller: str,
    split: str,
    warnings: list[str],
) -> list[dict]:
    df = pd.read_csv(report_path)
    manifest_map = _manifest_result_dir_map(dataset_root)
    rows = []
    for _, r in df.iterrows():
        if not str(r.get("status", "")).startswith("SUCCESS"):
            continue
        result_dir = _resolve_result_dir(r, dataset_root, manifest_map)
        if result_dir is None:
            warnings.append(
                f"SUCCESS row '{r['scenario_id']}' in {report_path} has no result_dir "
                f"in report or {os.path.join(dataset_root, 'manifest.csv')}"
            )
            continue
        row = _load_metrics_row(r["scenario_id"], controller, split, result_dir)
        if row:
            rows.append(row)
        else:
            warnings.append(
                f"SUCCESS row '{r['scenario_id']}' in {report_path} has no metrics.json "
                f"at {result_dir}"
            )
    return rows


def main():
    parser = argparse.ArgumentParser(description="Build comparison_closed_loop_v1.csv from metrics.json runs.")
    parser.add_argument("--out", type=str, default="results/comparison_closed_loop_v1.csv")
    parser.add_argument(
        "--classic-report",
        type=str,
        help="run_report.csv from classic dataset (controller=classic).",
    )
    parser.add_argument("--classic-dataset", type=str, default="data/classic_dataset/v1")
    parser.add_argument("--classic-split", type=str, default="test")
    parser.add_argument("--neural-report", type=str, help="run_report_neural_*.csv from outer-force batch.")
    parser.add_argument("--neural-dataset", type=str, help="Dataset root for neural report paths.")
    parser.add_argument("--neural-split", type=str, default="test")
    parser.add_argument("--neural-controller", type=str, default="neural_outer_force_mlp")
    parser.add_argument("--position-report", type=str, help="run_report_neural_position_*.csv (optional).")
    parser.add_argument("--position-dataset", type=str)
    parser.add_argument("--position-split", type=str, default="test")
    parser.add_argument("--manual-csv", type=str, help="CSV with columns scenario_id,controller,split,result_dir")
    parser.add_argument(
        "--allow-missing-metrics",
        action="store_true",
        help="Do not exit with error when SUCCESS report rows lack metrics.json (warnings still printed).",
    )
    args = parser.parse_args()

    all_rows: list[dict] = []
    load_warnings: list[str] = []

    if args.manual_csv:
        manual = pd.read_csv(args.manual_csv)
        for _, r in manual.iterrows():
            row = _load_metrics_row(
                r["scenario_id"],
                r["controller"],
                r.get("split", ""),
                r["result_dir"],
            )
            if row:
                all_rows.append(row)
            else:
                load_warnings.append(
                    f"Manual row '{r['scenario_id']}' has no metrics.json at {r['result_dir']}"
                )

    if args.classic_report:
        all_rows.extend(
            _rows_from_run_report(
                args.classic_report,
                args.classic_dataset,
                "classic",
                args.classic_split,
                load_warnings,
            )
        )

    if args.neural_report:
        ds = args.neural_dataset or os.path.dirname(args.neural_report)
        all_rows.extend(
            _rows_from_run_report(
                args.neural_report,
                ds,
                args.neural_controller,
                args.neural_split,
                load_warnings,
            )
        )

    if args.position_report:
        ds = args.position_dataset or os.path.dirname(args.position_report)
        all_rows.extend(
            _rows_from_run_report(
                args.position_report,
                ds,
                "neural_position",
                args.position_split,
                load_warnings,
            )
        )

    for msg in load_warnings:
        print(f"Warning: {msg}", file=sys.stderr)

    if load_warnings and not args.allow_missing_metrics:
        raise ValueError(
            f"{len(load_warnings)} SUCCESS row(s) missing metrics.json. "
            "Fix batch runs or pass --allow-missing-metrics to proceed."
        )

    if not all_rows:
        raise ValueError("No metrics rows collected. Provide --manual-csv and/or run reports.")

    out_df = pd.DataFrame(all_rows)
    for col in METRIC_COLUMNS:
        if col not in out_df.columns:
            out_df[col] = None
    out_df = out_df[METRIC_COLUMNS]

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {len(out_df)} rows to {args.out}")


if __name__ == "__main__":
    main()