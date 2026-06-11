import argparse
import os
import json
import re
import numpy as np
import pandas as pd
import yaml

from simulador_quad.metrics.success import (
    evaluate_termination_outcome,
    resolve_trajectory_type,
    trajectory_type_from_config,
)

PID_GAIN_FIELDS = ("Kp_pos", "Kd_pos", "Kp_att", "Kd_att")
FROZEN_PID_FAMILIES = ("hold", "circle", "lissajous", "waypoint")


def load_metrics(metrics_path):
    if not os.path.exists(metrics_path):
        return None
    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return None


def coverage_group_for_split(split: str) -> str:
    if split in ("test", "ood"):
        return "comparable"
    if split in ("train", "val"):
        return "baseline_partial"
    return "unknown"


def load_trajectory_type(dataset_root: str, scenario_path: str | None, family: str) -> str:
    if scenario_path:
        scenario_yaml = os.path.join(dataset_root, scenario_path)
        if os.path.exists(scenario_yaml):
            try:
                with open(scenario_yaml, "r", encoding="utf-8") as file:
                    config = yaml.safe_load(file)
                trajectory_type = trajectory_type_from_config(config)
                if trajectory_type:
                    return trajectory_type
            except Exception:
                pass
    return resolve_trajectory_type(family=family)


def build_record(
    *,
    scenario_id: str,
    family: str,
    split: str,
    controller: str,
    metrics: dict,
    trajectory_type: str,
) -> dict:
    termination_reason = metrics.get("termination_reason")
    outcome = evaluate_termination_outcome(
        termination_reason,
        trajectory_type=trajectory_type,
        family=family,
    )
    mission_success = outcome["mission_success"]
    safety_success = outcome["safety_success"]
    return {
        "scenario_id": scenario_id,
        "family": family,
        "split": split,
        "controller": controller,
        "trajectory_type": trajectory_type,
        "termination_reason": termination_reason,
        "mission_success": mission_success,
        "safety_success": safety_success,
        "control_success": mission_success,
        "coverage_group": coverage_group_for_split(split),
        "position_rmse_m": metrics.get("position_rmse_m"),
        "position_max_err_m": metrics.get("position_max_err_m"),
        "collective_thrust_mean_N": metrics.get("collective_thrust_mean_N"),
        "body_moment_norm_mean_Nm": metrics.get("body_moment_norm_mean_Nm"),
        "control_effort_heuristic_mean": metrics.get(
            "control_effort_heuristic_mean",
            metrics.get("control_effort_mean"),
        ),
        "saturation_percentage": metrics.get("saturation_percentage"),
        "degradation_percentage": metrics.get("degradation_percentage"),
        "force_norm_clip_percentage": metrics.get("force_norm_clip_percentage", 0.0),
        "force_tilt_clip_percentage": metrics.get("force_tilt_clip_percentage", 0.0),
        "success": float(mission_success),
    }


def build_run_record(
    *,
    scenario_id: str,
    family: str,
    split: str,
    controller: str,
    metrics: dict,
    trajectory_type: str | None = None,
) -> dict:
    """Build a comparison record while preserving the current success semantics."""
    return build_record(
        scenario_id=scenario_id,
        family=family,
        split=split,
        controller=controller,
        metrics=metrics,
        trajectory_type=trajectory_type or resolve_trajectory_type(family=family),
    )


def _is_missing(value) -> bool:
    return value is None or bool(pd.isna(value))


def _controller_gain_signature(controller_cfg: dict) -> dict | None:
    if not isinstance(controller_cfg, dict):
        return None
    gains = {field: controller_cfg[field] for field in PID_GAIN_FIELDS if field in controller_cfg}
    return gains or None


def _load_frozen_pid_signatures(classic_dataset_path: str) -> dict[str, dict]:
    signatures: dict[str, dict] = {}
    pids_dir = os.path.join(classic_dataset_path, "pids")
    for family in FROZEN_PID_FAMILIES:
        pid_path = os.path.join(pids_dir, f"pid_{family}_v1.yaml")
        if not os.path.exists(pid_path):
            continue
        with open(pid_path, encoding="utf-8") as handle:
            pid_data = yaml.safe_load(handle) or {}
        signature = _controller_gain_signature(pid_data)
        if signature:
            signatures[family] = signature
    return signatures


def _match_pid_family(controller_cfg: dict, frozen_signatures: dict[str, dict]) -> str | None:
    signature = _controller_gain_signature(controller_cfg)
    if not signature:
        return None
    for family, frozen_signature in frozen_signatures.items():
        if all(signature.get(field) == frozen_signature.get(field) for field in frozen_signature):
            return family
    return None


def resolve_classic_pid_family(row, metrics, classic_dataset_path: str, dataset_root: str) -> str | None:
    """Resolve the frozen PID family from manifest, report, metrics or scenario metadata."""
    pid_family = row.get("pid_family")
    if not _is_missing(pid_family):
        return str(pid_family)

    pid_id = row.get("pid_id")
    if not _is_missing(pid_id):
        match = re.match(r"pid_([a-z]+)_", str(pid_id))
        if match:
            return match.group(1)

    frozen_signatures = _load_frozen_pid_signatures(classic_dataset_path)
    metadata = metrics.get("metadata", {}) if metrics else {}
    controller_cfg = metadata.get("config", {}).get("controller")
    if not isinstance(controller_cfg, dict):
        controller_cfg = metadata.get("controller", {}).get("parameters", {}).get("config", {})
    matched = _match_pid_family(controller_cfg, frozen_signatures)
    if matched:
        return matched

    scenario_path = row.get("scenario_path")
    if not _is_missing(scenario_path):
        full_path = os.path.join(dataset_root, str(scenario_path))
        if os.path.exists(full_path):
            with open(full_path, encoding="utf-8") as handle:
                scenario = yaml.safe_load(handle) or {}
            return _match_pid_family(scenario.get("controller", {}), frozen_signatures)
    return None


def _format_rmse_dispersion(mean: float, std: float, count: float) -> str:
    if count > 1 and not np.isnan(std):
        return f"{mean:.3f} ({std:.3f})"
    return f"{mean:.3f}"


def main():
    parser = argparse.ArgumentParser(description="Aggregate and summarize all simulation runs for LaTeX tables.")
    parser.add_argument("--dataset-classic", type=str, default="data/classic_dataset/v1", help="Path to classic dataset")
    parser.add_argument("--dataset-neural", type=str, default="data/outer_force_dataset/v1", help="Path to neural outer force dataset")
    parser.add_argument("--dataset-position", type=str, default="data/position_gain_dataset/v1", help="Path to neural position gain dataset")
    parser.add_argument("--dataset-ood", type=str, default="data/neural_ood/battery_v1", help="Path to OOD battery dataset (optional)")
    parser.add_argument("--out-dir", type=str, default="results", help="Directory to save summary tables")

    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    # 1. Cargar manifiesto clásico para ver qué escenarios existen y sus splits
    manifest_path = os.path.join(args.dataset_classic, "manifest.csv")
    if not os.path.exists(manifest_path):
        print(f"Classic dataset manifest not found at {manifest_path}. Summary might be incomplete.")
        manifest_df = pd.DataFrame()
    else:
        manifest_df = pd.read_csv(manifest_path)

    records = []

    # Define OOD representative mapping for classic PIDs
    REPRESENTATIVE_MAPPING = {
        "hold": "hold",
        "circle": "circle",
        "lissajous": "lissajous",
        "waypoint": "waypoint",
        "lemniscate": "lissajous",
        "composite": "lissajous"
    }

    # --- A. Classic Family PID ---
    if not manifest_df.empty:
        for _, row in manifest_df.iterrows():
            scenario_id = row["scenario_id"]
            family = row["family"]
            split = row["split"]
            res_dir = os.path.join(args.dataset_classic, row["result_dir"])
            metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
            if metrics:
                trajectory_type = load_trajectory_type(
                    args.dataset_classic,
                    row.get("scenario_path"),
                    family,
                )
                base_record = build_record(
                    scenario_id=scenario_id,
                    family=family,
                    split=split,
                    controller=f"classic_pid_{family}",
                    metrics=metrics,
                    trajectory_type=trajectory_type,
                )
                records.append(base_record)
                representative_record = base_record.copy()
                representative_record["controller"] = "classic_pid_representative"
                records.append(representative_record)

    # --- B. Classic Cross PID (Transfer) ---
    if not manifest_df.empty:
        transfer_dir = os.path.join(args.dataset_classic, "results_transfer")
        if os.path.exists(transfer_dir):
            for _, row in manifest_df.iterrows():
                scenario_id = row["scenario_id"]
                family = row["family"]
                split = row["split"]
                for t_fam in ["hold", "circle", "lissajous", "waypoint"]:
                    # We skip t_fam == family because the diagonal is already loaded from Section A above
                    if t_fam == family:
                        continue
                    t_scenario_id = f"{scenario_id}_with_pid_{t_fam}"
                    res_dir = os.path.join(transfer_dir, t_scenario_id)
                    metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                    if metrics:
                        trajectory_type = load_trajectory_type(
                            args.dataset_classic,
                            row.get("scenario_path"),
                            family,
                        )
                        records.append(
                            build_record(
                                scenario_id=scenario_id,
                                family=family,
                                split=split,
                                controller=f"classic_pid_{t_fam}",
                                metrics=metrics,
                                trajectory_type=trajectory_type,
                            )
                        )

    # --- C. Oracle Outer-Force PID ---
    neural_manifest_path = os.path.join(args.dataset_neural, "manifest.csv")
    if os.path.exists(neural_manifest_path):
        neural_manifest_df = pd.read_csv(neural_manifest_path)
    else:
        neural_manifest_df = pd.DataFrame()

    if not neural_manifest_df.empty:
        for _, row in neural_manifest_df.iterrows():
            scenario_id = row["scenario_id"]
            family = row["family"]
            split = row["split"]
            res_dir = os.path.join(args.dataset_neural, row["result_dir"])
            metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
            if metrics:
                trajectory_type = load_trajectory_type(
                    args.dataset_neural,
                    row.get("scenario_path"),
                    family,
                )
                records.append(
                    build_record(
                        scenario_id=scenario_id,
                        family=family,
                        split=split,
                        controller="outer_force_oracle",
                        metrics=metrics,
                        trajectory_type=trajectory_type,
                    )
                )

    # --- D. Neural Outer Force (MLP, GRU, LSTM) ---
    if os.path.exists(args.dataset_neural):
        for arch in ["mlp", "gru", "lstm"]:
            # Buscamos en el reporte de corridas cerradas
            report_file = os.path.join(args.dataset_neural, f"run_report_neural_{arch}.csv")
            if os.path.exists(report_file):
                report_df = pd.read_csv(report_file)
                for _, r in report_df.iterrows():
                    scenario_id = r["scenario_id"]
                    # Buscar split y familia originales
                    orig_row = pd.DataFrame()
                    if not neural_manifest_df.empty:
                        orig_row = neural_manifest_df[neural_manifest_df["scenario_id"] == scenario_id]
                    if orig_row.empty:
                        clean_id = scenario_id
                        if clean_id.endswith("_outer_expert"):
                            clean_id = clean_id[:-13]
                        orig_row = manifest_df[manifest_df["scenario_id"] == clean_id]

                    scenario_path = None
                    if orig_row.empty:
                        family = "unknown"
                        split = "unknown"
                    else:
                        family = orig_row.iloc[0]["family"]
                        split = orig_row.iloc[0]["split"]
                        scenario_path = orig_row.iloc[0].get("scenario_path")

                    res_dir = r["result_dir"]
                    if not os.path.isabs(res_dir):
                        if os.path.exists(res_dir):
                            pass
                        else:
                            opt_dir = os.path.join(args.dataset_neural, res_dir)
                            if os.path.exists(opt_dir):
                                res_dir = opt_dir
                    metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                    if metrics:
                        trajectory_type = load_trajectory_type(
                            args.dataset_neural,
                            scenario_path,
                            family,
                        )
                        records.append(
                            build_record(
                                scenario_id=scenario_id,
                                family=family,
                                split=split,
                                controller=f"neural_outer_force_{arch}",
                                metrics=metrics,
                                trajectory_type=trajectory_type,
                            )
                        )

    # --- E. Neural Position (MLP, GRU, LSTM) ---
    position_manifest_path = os.path.join(args.dataset_position, "manifest.csv")
    if os.path.exists(position_manifest_path):
        position_manifest_df = pd.read_csv(position_manifest_path)
    else:
        position_manifest_df = pd.DataFrame()

    if os.path.exists(args.dataset_position):
        for arch in ["mlp", "gru", "lstm"]:
            report_file = os.path.join(args.dataset_position, f"run_report_neural_position_{arch}.csv")
            if os.path.exists(report_file):
                report_df = pd.read_csv(report_file)
                for _, r in report_df.iterrows():
                    scenario_id = r["scenario_id"]
                    orig_row = pd.DataFrame()
                    if not position_manifest_df.empty:
                        orig_row = position_manifest_df[position_manifest_df["scenario_id"] == scenario_id]
                    if orig_row.empty:
                        clean_id = scenario_id
                        for suffix in ["_conservative", "_base", "_aggressive"]:
                            if clean_id.endswith(suffix):
                                clean_id = clean_id[:-len(suffix)]
                                break
                        orig_row = manifest_df[manifest_df["scenario_id"] == clean_id]

                    scenario_path = None
                    if orig_row.empty:
                        family = "unknown"
                        split = "unknown"
                    else:
                        family = orig_row.iloc[0]["family"]
                        split = orig_row.iloc[0]["split"]
                        scenario_path = orig_row.iloc[0].get("scenario_path")

                    res_dir = r["result_dir"]
                    if not os.path.isabs(res_dir):
                        if os.path.exists(res_dir):
                            pass
                        else:
                            opt_dir = os.path.join(args.dataset_position, res_dir)
                            if os.path.exists(opt_dir):
                                res_dir = opt_dir
                    metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                    if metrics:
                        trajectory_type = load_trajectory_type(
                            args.dataset_position,
                            scenario_path,
                            family,
                        )
                        records.append(
                            build_record(
                                scenario_id=scenario_id,
                                family=family,
                                split=split,
                                controller=f"neural_position_{arch}",
                                metrics=metrics,
                                trajectory_type=trajectory_type,
                            )
                        )

    # --- F. OOD Battery Closed-Loop Runs ---
    # Si existe el dataset OOD y hay reportes ejecutados sobre él
    if os.path.exists(args.dataset_ood):
        ood_manifest = os.path.join(args.dataset_ood, "manifest.csv")
        if os.path.exists(ood_manifest):
            ood_df = pd.read_csv(ood_manifest)

            # 1. Load classic transfer matrix on OOD (including representative PIDs)
            transfer_dir = os.path.join(args.dataset_ood, "results_transfer")
            if os.path.exists(transfer_dir):
                for _, row in ood_df.iterrows():
                    scenario_id = row["scenario_id"]
                    family = row["family"]
                    rep_fam = REPRESENTATIVE_MAPPING.get(family, "lissajous")
                    for t_fam in ["hold", "circle", "lissajous", "waypoint"]:
                        t_scenario_id = f"{scenario_id}_with_pid_{t_fam}"
                        res_dir = os.path.join(transfer_dir, t_scenario_id)
                        metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                        if metrics:
                            trajectory_type = load_trajectory_type(
                                args.dataset_ood,
                                row.get("scenario_path"),
                                family,
                            )
                            transfer_record = build_record(
                                scenario_id=scenario_id,
                                family=family,
                                split="ood",
                                controller=f"classic_pid_{t_fam}",
                                metrics=metrics,
                                trajectory_type=trajectory_type,
                            )
                            records.append(transfer_record)
                            if t_fam == rep_fam:
                                representative_record = transfer_record.copy()
                                representative_record["controller"] = "classic_pid_representative"
                                records.append(representative_record)
            else:
                # Fall back to direct classic OOD runs when no transfer matrix is available.
                for _, row in ood_df.iterrows():
                    scenario_id = row["scenario_id"]
                    family = row["family"]
                    res_dir = os.path.join(args.dataset_ood, row["result_dir"])
                    metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                    if not metrics:
                        continue
                    pid_family = resolve_classic_pid_family(
                        row,
                        metrics,
                        args.dataset_classic,
                        args.dataset_ood,
                    )
                    if pid_family is None:
                        print(
                            f"Warning: could not resolve PID family for OOD classic run "
                            f"{scenario_id}; skipping row."
                        )
                        continue
                    trajectory_type = load_trajectory_type(
                        args.dataset_ood,
                        row.get("scenario_path"),
                        family,
                    )
                    records.append(
                        build_record(
                            scenario_id=scenario_id,
                            family=family,
                            split="ood",
                            controller=f"classic_pid_{pid_family}",
                            metrics=metrics,
                            trajectory_type=trajectory_type,
                        )
                    )

            # Neuronales sobre OOD
            for arch in ["mlp", "gru", "lstm"]:
                report_file = os.path.join(args.dataset_ood, f"run_report_neural_{arch}.csv")
                if os.path.exists(report_file):
                    r_df = pd.read_csv(report_file)
                    for _, r in r_df.iterrows():
                        scenario_id = r["scenario_id"]
                        orig_row = ood_df[ood_df["scenario_id"] == scenario_id]
                        if orig_row.empty:
                            family = "unknown"
                            scenario_path = None
                        else:
                            family = orig_row.iloc[0]["family"]
                            scenario_path = orig_row.iloc[0].get("scenario_path")
                        res_dir = r["result_dir"]
                        if not os.path.isabs(res_dir):
                            if os.path.exists(res_dir):
                                pass
                            else:
                                opt_dir = os.path.join(args.dataset_ood, res_dir)
                                if os.path.exists(opt_dir):
                                    res_dir = opt_dir
                        metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                        if metrics:
                            trajectory_type = load_trajectory_type(
                                args.dataset_ood,
                                scenario_path,
                                family,
                            )
                            records.append(
                                build_record(
                                    scenario_id=scenario_id,
                                    family=family,
                                    split="ood",
                                    controller=f"neural_outer_force_{arch}",
                                    metrics=metrics,
                                    trajectory_type=trajectory_type,
                                )
                            )
            # Neuronales de posición sobre OOD
            for arch in ["mlp", "gru", "lstm"]:
                report_file = os.path.join(args.dataset_ood, f"run_report_neural_position_{arch}.csv")
                if os.path.exists(report_file):
                    r_df = pd.read_csv(report_file)
                    for _, r in r_df.iterrows():
                        scenario_id = r["scenario_id"]
                        orig_row = ood_df[ood_df["scenario_id"] == scenario_id]
                        if orig_row.empty:
                            family = "unknown"
                            scenario_path = None
                        else:
                            family = orig_row.iloc[0]["family"]
                            scenario_path = orig_row.iloc[0].get("scenario_path")
                        res_dir = r["result_dir"]
                        if not os.path.isabs(res_dir):
                            if os.path.exists(res_dir):
                                pass
                            else:
                                opt_dir = os.path.join(args.dataset_ood, res_dir)
                                if os.path.exists(opt_dir):
                                    res_dir = opt_dir
                        metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                        if metrics:
                            trajectory_type = load_trajectory_type(
                                args.dataset_ood,
                                scenario_path,
                                family,
                            )
                            records.append(
                                build_record(
                                    scenario_id=scenario_id,
                                    family=family,
                                    split="ood",
                                    controller=f"neural_position_{arch}",
                                    metrics=metrics,
                                    trajectory_type=trajectory_type,
                                )
                            )

    if not records:
        print("No simulation metrics collected. Summary cannot be constructed.")
        return

    df_all = pd.DataFrame(records)

    full_runs_csv = os.path.join(args.out_dir, "comparison_all_runs_full.csv")
    df_all.to_csv(full_runs_csv, index=False)
    print(f"Saved full raw runs (all splits) to {full_runs_csv}")

    df_comparable = df_all[df_all["split"].isin(["test", "ood"])].copy()
    all_runs_csv = os.path.join(args.out_dir, "comparison_all_runs.csv")
    df_comparable.to_csv(all_runs_csv, index=False)
    print(
        f"Saved comparable raw runs (test/ood only) to {all_runs_csv} "
        f"({len(df_comparable)} rows; full dataset has {len(df_all)} rows)"
    )

    grouped = df_comparable.groupby(["controller", "split", "family"]).agg(
        mission_success_rate=("mission_success", "mean"),
        safety_success_rate=("safety_success", "mean"),
        success_rate=("success", "mean"),
        rmse_mean=("position_rmse_m", "mean"),
        rmse_std=("position_rmse_m", "std"),
        rmse_max=("position_max_err_m", "mean"),
        saturation_mean=("saturation_percentage", "mean"),
        degradation_mean=("degradation_percentage", "mean"),
        clip_norm_mean=("force_norm_clip_percentage", "mean"),
        clip_tilt_mean=("force_tilt_clip_percentage", "mean"),
        count=("scenario_id", "count")
    ).reset_index()

    # Multiplicar tasas por 100 para porcentaje
    for rate_col in ("mission_success_rate", "safety_success_rate", "success_rate"):
        grouped[rate_col] = grouped[rate_col] * 100.0

    for col in [
        "mission_success_rate",
        "safety_success_rate",
        "success_rate",
        "rmse_mean",
        "rmse_std",
        "rmse_max",
        "saturation_mean",
        "degradation_mean",
        "clip_norm_mean",
        "clip_tilt_mean",
    ]:
        grouped[col] = grouped[col].round(3)

    summary_csv = os.path.join(args.out_dir, "comparison_summary.csv")
    grouped.to_csv(summary_csv, index=False)
    print(f"Saved aggregated comparison summary to {summary_csv}")

    # --- Generar LaTeX ---
    # Generamos una tabla bonita para el split de TEST (In-distribution) y OOD
    print("\n" + "="*40 + " TABLA LATEX PARA MEMORIA (SPLIT: TEST) " + "="*40)
    test_df = grouped[grouped["split"] == "test"]
    if not test_df.empty:
        print("\\begin{table}[h!]")
        print("  \\centering")
        print("  \\caption{Comparativa de controladores en trayectoria de Test (In-Distribution). Entre paréntesis, la desviación representa la dispersión del RMSE entre escenarios del grupo, no incertidumbre temporal.}")
        print("  \\label{tab:comparativa_test}")
        print("  \\begin{tabular}{llcccccc}")
        print("    \\hline")
        print("    \\textbf{Controlador} & \\textbf{Trayectoria} & \\textbf{Éxito (\\%)} & \\textbf{RMSE medio [m] (disp. escenarios)} & \\textbf{Máx. Err. (m)} & \\textbf{Saturación (\\%)} & \\textbf{Norm Clip (\\%)} & \\textbf{Tilt Clip (\\%)} \\\\")
        print("    \\hline")
        for _, r in test_df.sort_values(by=["controller", "family"]).iterrows():
            rmse_cell = _format_rmse_dispersion(r["rmse_mean"], r["rmse_std"], r["count"])
            print(f"    {r['controller'].replace('_', '\\_')} & {r['family']} & {r['success_rate']:.1f}\\% & {rmse_cell} & {r['rmse_max']:.3f} & {r['saturation_mean']:.1f}\\% & {r['clip_norm_mean']:.1f}\\% & {r['clip_tilt_mean']:.1f}\\% \\\\")
        print("    \\hline")
        print("  \\end{tabular}")
        print("\\end{table}")
    else:
        print("No test split data collected. Run simulations first.")

    print("\n" + "="*40 + " TABLA LATEX PARA MEMORIA (SPLIT: OOD) " + "="*40)
    ood_df = grouped[grouped["split"] == "ood"]
    if not ood_df.empty:
        print("\\begin{table}[h!]")
        print("  \\centering")
        print("  \\caption{Comparativa de controladores bajo escenarios OOD (Out-of-Distribution). Entre paréntesis, la desviación representa la dispersión del RMSE entre escenarios del grupo, no incertidumbre temporal.}")
        print("  \\label{tab:comparativa_ood}")
        print("  \\begin{tabular}{llcccccc}")
        print("    \\hline")
        print("    \\textbf{Controlador} & \\textbf{Trayectoria} & \\textbf{Éxito (\\%)} & \\textbf{RMSE medio [m] (disp. escenarios)} & \\textbf{Máx. Err. (m)} & \\textbf{Saturación (\\%)} & \\textbf{Norm Clip (\\%)} & \\textbf{Tilt Clip (\\%)} \\\\")
        print("    \\hline")
        for _, r in ood_df.sort_values(by=["controller", "family"]).iterrows():
            rmse_cell = _format_rmse_dispersion(r["rmse_mean"], r["rmse_std"], r["count"])
            print(f"    {r['controller'].replace('_', '\\_')} & {r['family']} & {r['success_rate']:.1f}\\% & {rmse_cell} & {r['rmse_max']:.3f} & {r['saturation_mean']:.1f}\\% & {r['clip_norm_mean']:.1f}\\% & {r['clip_tilt_mean']:.1f}\\% \\\\")
        print("    \\hline")
        print("  \\end{tabular}")
        print("\\end{table}")
    else:
        print("No OOD split data collected. Run OOD battery simulations first.")
    print("="*120)


if __name__ == "__main__":
    main()
