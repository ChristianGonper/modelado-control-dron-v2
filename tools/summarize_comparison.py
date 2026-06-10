import argparse
import os
import json
import re

import numpy as np
import pandas as pd
import yaml

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


def get_success(termination_reason, family):
    valid = ["Time limit reached"]
    if family == "waypoint":
        valid.append("Trajectory completed")
    return 1.0 if termination_reason in valid else 0.0


def _is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and np.isnan(value))


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
    """Resolve the frozen PID family used in a run from manifest, report or scenario metadata."""
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
        full_path = os.path.join(dataset_root, scenario_path)
        if os.path.exists(full_path):
            with open(full_path, encoding="utf-8") as handle:
                scenario = yaml.safe_load(handle) or {}
            matched = _match_pid_family(scenario.get("controller", {}), frozen_signatures)
            if matched:
                return matched

    return None


def build_run_record(
    *,
    scenario_id,
    family,
    split,
    controller,
    metrics,
    force_norm_clip_percentage=0.0,
    force_tilt_clip_percentage=0.0,
):
    return {
        "scenario_id": scenario_id,
        "family": family,
        "split": split,
        "controller": controller,
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
        "force_norm_clip_percentage": force_norm_clip_percentage,
        "force_tilt_clip_percentage": force_tilt_clip_percentage,
        "success": get_success(metrics.get("termination_reason"), family),
    }


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
    
    # --- A. Classic Family PID ---
    if not manifest_df.empty:
        for _, row in manifest_df.iterrows():
            scenario_id = row["scenario_id"]
            family = row["family"]
            split = row["split"]
            res_dir = os.path.join(args.dataset_classic, row["result_dir"])
            metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
            if metrics:
                records.append(
                    build_run_record(
                        scenario_id=scenario_id,
                        family=family,
                        split=split,
                        controller=f"classic_pid_{family}",
                        metrics=metrics,
                    )
                )
                
    # --- B. Classic Cross PID (Transfer) ---
    if not manifest_df.empty:
        transfer_dir = os.path.join(args.dataset_classic, "results_transfer")
        if os.path.exists(transfer_dir):
            for _, row in manifest_df.iterrows():
                scenario_id = row["scenario_id"]
                family = row["family"]
                split = row["split"]
                for t_fam in ["hold", "circle", "lissajous", "waypoint"]:
                    if t_fam == family:
                        continue
                    t_scenario_id = f"{scenario_id}_with_pid_{t_fam}"
                    res_dir = os.path.join(transfer_dir, t_scenario_id)
                    metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                    if metrics:
                        records.append(
                            build_run_record(
                                scenario_id=scenario_id,
                                family=family,
                                split=split,
                                controller=f"classic_pid_{t_fam}",
                                metrics=metrics,
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
                records.append(
                    build_run_record(
                        scenario_id=scenario_id,
                        family=family,
                        split=split,
                        controller="outer_force_oracle",
                        metrics=metrics,
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

                    if orig_row.empty:
                        family = "unknown"
                        split = "unknown"
                    else:
                        family = orig_row.iloc[0]["family"]
                        split = orig_row.iloc[0]["split"]
                        
                    res_dir = r["result_dir"]
                    # El reporte neural almacena la ruta relativa al dataset o absoluta
                    if not os.path.isabs(res_dir):
                        if os.path.exists(res_dir):
                            pass
                        else:
                            opt_dir = os.path.join(args.dataset_neural, res_dir)
                            if os.path.exists(opt_dir):
                                res_dir = opt_dir
                    metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                    if metrics:
                        records.append(
                            build_run_record(
                                scenario_id=scenario_id,
                                family=family,
                                split=split,
                                controller=f"neural_outer_force_{arch}",
                                metrics=metrics,
                                force_norm_clip_percentage=metrics.get("force_norm_clip_percentage", 0.0),
                                force_tilt_clip_percentage=metrics.get("force_tilt_clip_percentage", 0.0),
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

                    if orig_row.empty:
                        family = "unknown"
                        split = "unknown"
                    else:
                        family = orig_row.iloc[0]["family"]
                        split = orig_row.iloc[0]["split"]
                        
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
                        records.append(
                            build_run_record(
                                scenario_id=scenario_id,
                                family=family,
                                split=split,
                                controller=f"neural_position_{arch}",
                                metrics=metrics,
                            )
                        )
                        
    # --- F. OOD Battery Closed-Loop Runs ---
    # Si existe el dataset OOD y hay reportes ejecutados sobre él
    if os.path.exists(args.dataset_ood):
        ood_manifest = os.path.join(args.dataset_ood, "manifest.csv")
        if os.path.exists(ood_manifest):
            ood_df = pd.read_csv(ood_manifest)
            # Clásico sobre OOD
            for _, row in ood_df.iterrows():
                scenario_id = row["scenario_id"]
                family = row["family"]
                # En OOD, el resultado se ubica bajo result_dir del OOD dataset
                res_dir = os.path.join(args.dataset_ood, row["result_dir"])
                metrics = load_metrics(os.path.join(res_dir, "metrics.json"))
                if metrics:
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
                    records.append(
                        build_run_record(
                            scenario_id=scenario_id,
                            family=family,
                            split="ood",
                            controller=f"classic_pid_{pid_family}",
                            metrics=metrics,
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
                        family = orig_row.iloc[0]["family"] if not orig_row.empty else "unknown"
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
                            records.append(
                                build_run_record(
                                    scenario_id=scenario_id,
                                    family=family,
                                    split="ood",
                                    controller=f"neural_outer_force_{arch}",
                                    metrics=metrics,
                                    force_norm_clip_percentage=metrics.get("force_norm_clip_percentage", 0.0),
                                    force_tilt_clip_percentage=metrics.get("force_tilt_clip_percentage", 0.0),
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
                        family = orig_row.iloc[0]["family"] if not orig_row.empty else "unknown"
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
                            records.append(
                                build_run_record(
                                    scenario_id=scenario_id,
                                    family=family,
                                    split="ood",
                                    controller=f"neural_position_{arch}",
                                    metrics=metrics,
                                )
                            )
                            
    if not records:
        print("No simulation metrics collected. Summary cannot be constructed.")
        return
        
    df_all = pd.DataFrame(records)
    
    # Guardar tabla plana de todas las corridas
    all_runs_csv = os.path.join(args.out_dir, "comparison_all_runs.csv")
    df_all.to_csv(all_runs_csv, index=False)
    print(f"Saved all raw runs to {all_runs_csv}")
    
    # Calcular promedios agrupados
    grouped = df_all.groupby(["controller", "split", "family"]).agg(
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
    grouped["success_rate"] = grouped["success_rate"] * 100.0
    
    # Redondear para legibilidad
    for col in ["success_rate", "rmse_mean", "rmse_std", "rmse_max", "saturation_mean", "degradation_mean", "clip_norm_mean", "clip_tilt_mean"]:
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
        print(
            "  \\caption{Comparativa de controladores en trayectoria de Test (In-Distribution). "
            "Entre paréntesis, la desviación resume la dispersión del RMSE entre escenarios del mismo grupo.}"
        )
        print("  \\label{tab:comparativa_test}")
        print("  \\begin{tabular}{llcccccc}")
        print("    \\hline")
        print(
            "    \\textbf{Controlador} & \\textbf{Trayectoria} & \\textbf{Éxito (\\%)} "
            "& \\textbf{RMSE medio [m] (disp. escenarios)} & \\textbf{Máx. Err. (m)} "
            "& \\textbf{Saturación (\\%)} & \\textbf{Norm Clip (\\%)} & \\textbf{Tilt Clip (\\%)} \\\\"
        )
        print("    \\hline")
        for _, r in test_df.sort_values(by=["controller", "family"]).iterrows():
            rmse_cell = _format_rmse_dispersion(r["rmse_mean"], r["rmse_std"], r["count"])
            print(
                f"    {r['controller'].replace('_', '\\_')} & {r['family']} & {r['success_rate']:.1f}\\% "
                f"& {rmse_cell} & {r['rmse_max']:.3f} & {r['saturation_mean']:.1f}\\% "
                f"& {r['clip_norm_mean']:.1f}\\% & {r['clip_tilt_mean']:.1f}\\% \\\\"
            )
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
        print(
            "  \\caption{Comparativa de controladores bajo escenarios OOD (Out-of-Distribution). "
            "Entre paréntesis, la desviación resume la dispersión del RMSE entre escenarios del mismo grupo.}"
        )
        print("  \\label{tab:comparativa_ood}")
        print("  \\begin{tabular}{llcccccc}")
        print("    \\hline")
        print(
            "    \\textbf{Controlador} & \\textbf{Trayectoria} & \\textbf{Éxito (\\%)} "
            "& \\textbf{RMSE medio [m] (disp. escenarios)} & \\textbf{Máx. Err. (m)} "
            "& \\textbf{Saturación (\\%)} & \\textbf{Norm Clip (\\%)} & \\textbf{Tilt Clip (\\%)} \\\\"
        )
        print("    \\hline")
        for _, r in ood_df.sort_values(by=["controller", "family"]).iterrows():
            rmse_cell = _format_rmse_dispersion(r["rmse_mean"], r["rmse_std"], r["count"])
            print(
                f"    {r['controller'].replace('_', '\\_')} & {r['family']} & {r['success_rate']:.1f}\\% "
                f"& {rmse_cell} & {r['rmse_max']:.3f} & {r['saturation_mean']:.1f}\\% "
                f"& {r['clip_norm_mean']:.1f}\\% & {r['clip_tilt_mean']:.1f}\\% \\\\"
            )
        print("    \\hline")
        print("  \\end{tabular}")
        print("\\end{table}")
    else:
        print("No OOD split data collected. Run OOD battery simulations first.")
    print("="*120)


if __name__ == "__main__":
    main()
