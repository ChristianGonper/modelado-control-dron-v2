"""
Aggregate neural outer-force sensitivity study results vs v1 baseline.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import pandas as pd
import yaml

from simulador_quad.metrics.success import evaluate_termination_outcome, resolve_trajectory_type

DATASET = "data/outer_force_dataset/v1"
OOD_DATASET = "data/neural_ood/battery_v1"
NEURAL_CONTROL_ROOT = "data/neural_control"
ABLATION_REPORTS = "data/neural_ablation/reports"
OUT_DIR = "results/neural_sensitivity"

BASELINE_TAG = "v1_baseline"

VARIANTS = [
    {"tag": "h128", "block": "h128", "architectures": ["mlp", "gru", "lstm"]},
    {"tag": "L10", "block": "L10", "architectures": ["gru", "lstm"]},
    {"tag": "L40", "block": "L40", "architectures": ["gru", "lstm"]},
    {"tag": "seed7", "block": "seed7", "architectures": ["mlp"]},
    {"tag": "seed123", "block": "seed123", "architectures": ["mlp"]},
]


def _load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _load_config(run_dir: str) -> dict:
    path = os.path.join(run_dir, "config.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _run_dir_for(tag: str, architecture: str) -> str:
    if tag == BASELINE_TAG:
        return os.path.join(NEURAL_CONTROL_ROOT, f"outer_force_{architecture}_min_v1")
    return os.path.join(NEURAL_CONTROL_ROOT, f"outer_force_{architecture}_min_v1_{tag}")


def _report_path(tag: str, architecture: str, split: str) -> str | None:
    if tag == BASELINE_TAG:
        dataset = OOD_DATASET if split == "ood" else DATASET
        path = os.path.join(dataset, f"run_report_neural_{architecture}.csv")
        return path if os.path.exists(path) else None
    path = os.path.join(ABLATION_REPORTS, f"run_report_{tag}_{architecture}_{split}.csv")
    return path if os.path.exists(path) else None


def _result_suffix(architecture: str, tag: str) -> str:
    suffix = f"_neural_{architecture}"
    if tag != BASELINE_TAG:
        suffix += f"_{tag}"
    return suffix


def collect_supervised_rows() -> list[dict]:
    rows: list[dict] = []
    specs: list[tuple[str, str, str]] = []

    for arch in ("mlp", "gru", "lstm"):
        specs.append((BASELINE_TAG, "baseline", arch))
    for variant in VARIANTS:
        for arch in variant["architectures"]:
            specs.append((variant["tag"], variant["block"], arch))

    for tag, block, arch in specs:
        run_dir = _run_dir_for(tag, arch)
        config = _load_config(run_dir)
        for split in ("train", "val", "test"):
            metrics_path = os.path.join(run_dir, "metrics", f"{split}_force_metrics.json")
            metrics = _load_json(metrics_path)
            if not metrics:
                continue
            rows.append({
                "variant_tag": tag,
                "block": block,
                "architecture": arch,
                "controller": f"neural_outer_force_{arch}",
                "split": split,
                "hidden_dim": config.get("hidden_dim"),
                "sequence_length": config.get("sequence_length"),
                "seed": config.get("seed"),
                "mse_normalized": metrics.get("mse_normalized"),
                "rmse_force_norm_N": metrics.get("rmse_force_norm_N"),
                "run_dir": run_dir,
            })
    return rows


def _closed_loop_rows_for(tag: str, block: str, architecture: str, split: str, dataset: str) -> list[dict]:
    report_path = _report_path(tag, architecture, split)
    if not report_path:
        return []

    manifest_path = os.path.join(dataset, "manifest.csv")
    manifest = pd.read_csv(manifest_path) if os.path.exists(manifest_path) else pd.DataFrame()
    report = pd.read_csv(report_path)
    suffix = _result_suffix(architecture, tag)
    rows: list[dict] = []

    for _, report_row in report.iterrows():
        if not str(report_row.get("status", "")).startswith("SUCCESS"):
            continue
        scenario_id = report_row["scenario_id"]
        result_dir = report_row["result_dir"]
        if not os.path.isabs(result_dir):
            if not os.path.exists(result_dir):
                result_dir = os.path.join(dataset, result_dir)
        metrics = _load_json(os.path.join(result_dir, "metrics.json"))
        if not metrics:
            continue

        family = "unknown"
        if not manifest.empty and "scenario_id" in manifest.columns:
            match = manifest[manifest["scenario_id"] == scenario_id]
            if not match.empty:
                family = match.iloc[0]["family"]

        trajectory_type = resolve_trajectory_type(family=family)
        outcome = evaluate_termination_outcome(
            metrics.get("termination_reason"),
            trajectory_type=trajectory_type,
            family=family,
        )
        rows.append({
            "variant_tag": tag,
            "block": block,
            "architecture": architecture,
            "controller": f"neural_outer_force_{architecture}",
            "split": split,
            "scenario_id": scenario_id,
            "family": family,
            "mission_success": outcome["mission_success"],
            "safety_success": outcome["safety_success"],
            "position_rmse_m": metrics.get("position_rmse_m"),
            "saturation_percentage": metrics.get("saturation_percentage"),
            "degradation_percentage": metrics.get("degradation_percentage"),
            "force_norm_clip_percentage": metrics.get("force_norm_clip_percentage", 0.0),
            "force_tilt_clip_percentage": metrics.get("force_tilt_clip_percentage", 0.0),
            "result_dir": result_dir,
        })
    return rows


def collect_closed_loop_rows() -> list[dict]:
    rows: list[dict] = []
    specs: list[tuple[str, str, str]] = []
    for arch in ("mlp", "gru", "lstm"):
        specs.append((BASELINE_TAG, "baseline", arch))
    for variant in VARIANTS:
        for arch in variant["architectures"]:
            specs.append((variant["tag"], variant["block"], arch))

    for tag, block, arch in specs:
        rows.extend(_closed_loop_rows_for(tag, block, arch, "test", DATASET))
        rows.extend(_closed_loop_rows_for(tag, block, arch, "ood", OOD_DATASET))
    return rows


def build_summary_vs_baseline(closed_df: pd.DataFrame) -> pd.DataFrame:
    if closed_df.empty:
        return pd.DataFrame()

    baseline = closed_df[closed_df["variant_tag"] == BASELINE_TAG].copy()
    variants = closed_df[closed_df["variant_tag"] != BASELINE_TAG].copy()

    agg_cols = {
        "position_rmse_m": "mean",
        "mission_success": "mean",
        "saturation_percentage": "mean",
        "force_norm_clip_percentage": "mean",
        "force_tilt_clip_percentage": "mean",
        "scenario_id": "count",
    }
    baseline_agg = (
        baseline.groupby(["architecture", "controller", "split"], as_index=False)
        .agg(agg_cols)
        .rename(columns={
            "position_rmse_m": "rmse_mean_baseline",
            "mission_success": "mission_success_rate_baseline",
            "saturation_percentage": "saturation_mean_baseline",
            "force_norm_clip_percentage": "clip_norm_mean_baseline",
            "force_tilt_clip_percentage": "clip_tilt_mean_baseline",
            "scenario_id": "count",
        })
    )

    variant_agg = (
        variants.groupby(
            ["variant_tag", "block", "architecture", "controller", "split"],
            as_index=False,
        )
        .agg(agg_cols)
        .rename(columns={
            "position_rmse_m": "rmse_mean",
            "mission_success": "mission_success_rate",
            "saturation_percentage": "saturation_mean",
            "force_norm_clip_percentage": "clip_norm_mean",
            "force_tilt_clip_percentage": "clip_tilt_mean",
            "scenario_id": "count",
        })
    )

    merged = variant_agg.merge(
        baseline_agg,
        on=["architecture", "controller", "split"],
        how="left",
    )
    merged["delta_rmse_mean"] = merged["rmse_mean"] - merged["rmse_mean_baseline"]
    merged["delta_mission_success_rate"] = (
        merged["mission_success_rate"] - merged["mission_success_rate_baseline"]
    )
    merged["delta_saturation_mean"] = merged["saturation_mean"] - merged["saturation_mean_baseline"]
    merged["delta_clip_norm_mean"] = merged["clip_norm_mean"] - merged["clip_norm_mean_baseline"]
    merged["delta_clip_tilt_mean"] = merged["clip_tilt_mean"] - merged["clip_tilt_mean_baseline"]
    return merged


def build_study_manifest(supervised_df: pd.DataFrame, closed_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    specs: list[tuple[str, str, str]] = []
    for arch in ("mlp", "gru", "lstm"):
        specs.append((BASELINE_TAG, "baseline", arch))
    for variant in VARIANTS:
        for arch in variant["architectures"]:
            specs.append((variant["tag"], variant["block"], arch))

    for tag, block, arch in specs:
        run_dir = _run_dir_for(tag, arch)
        config = _load_config(run_dir)
        supervised_ok = False
        if not supervised_df.empty:
            supervised_ok = not supervised_df[
                (supervised_df["variant_tag"] == tag) & (supervised_df["architecture"] == arch)
            ].empty
        closed_test = 0
        closed_ood = 0
        if not closed_df.empty:
            sub = closed_df[(closed_df["variant_tag"] == tag) & (closed_df["architecture"] == arch)]
            closed_test = len(sub[sub["split"] == "test"])
            closed_ood = len(sub[sub["split"] == "ood"])

        state = "missing"
        if os.path.exists(os.path.join(run_dir, "checkpoints", f"{arch}_best.pt")):
            if supervised_ok and closed_test > 0 and closed_ood > 0:
                state = "complete"
            elif supervised_ok or closed_test > 0 or closed_ood > 0:
                state = "partial"
            else:
                state = "trained_only"

        rows.append({
            "variant_tag": tag,
            "block": block,
            "architecture": arch,
            "hidden_dim": config.get("hidden_dim", 64 if tag == BASELINE_TAG else None),
            "sequence_length": config.get("sequence_length", 20 if arch != "mlp" else None),
            "seed": config.get("seed", 42 if tag == BASELINE_TAG else None),
            "run_dir": run_dir,
            "state": state,
            "supervised_splits": int(
                len(supervised_df[
                    (supervised_df["variant_tag"] == tag) & (supervised_df["architecture"] == arch)
                ]) if not supervised_df.empty else 0
            ),
            "closed_loop_test_runs": closed_test,
            "closed_loop_ood_runs": closed_ood,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize neural sensitivity study vs v1 baseline.")
    parser.add_argument("--out-dir", type=str, default=OUT_DIR)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    supervised_rows = collect_supervised_rows()
    closed_rows = collect_closed_loop_rows()

    supervised_df = pd.DataFrame(supervised_rows)
    closed_df = pd.DataFrame(closed_rows)
    summary_df = build_summary_vs_baseline(closed_df)
    manifest_df = build_study_manifest(supervised_df, closed_df)

    supervised_path = os.path.join(args.out_dir, "supervised_comparison.csv")
    closed_path = os.path.join(args.out_dir, "closed_loop_comparison.csv")
    summary_path = os.path.join(args.out_dir, "summary_vs_baseline.csv")
    manifest_path = os.path.join(args.out_dir, "study_manifest.csv")

    supervised_df.to_csv(supervised_path, index=False)
    closed_df.to_csv(closed_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    manifest_df.to_csv(manifest_path, index=False)

    print(f"Wrote {len(supervised_df)} supervised rows to {supervised_path}")
    print(f"Wrote {len(closed_df)} closed-loop rows to {closed_path}")
    print(f"Wrote {len(summary_df)} summary rows to {summary_path}")
    print(f"Wrote {len(manifest_df)} manifest rows to {manifest_path}")


if __name__ == "__main__":
    main()