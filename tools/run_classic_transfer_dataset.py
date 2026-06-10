import argparse
import json
import os
import sys
import yaml
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from simulador_quad.app import run_simulation
from simulador_quad.metrics.success import (
    evaluate_termination_outcome,
    is_preserved_transfer_execution_status,
    trajectory_type_from_config,
)
from simulador_quad.datasets.pids import (
    FROZEN_PID_FAMILIES,
    controller_gains_match,
    load_all_frozen_pids,
    load_frozen_pid_family,
    pid_gains_fingerprint,
)

REPRESENTATIVE_MAPPING = {
    "hold": "hold",
    "circle": "circle",
    "lissajous": "lissajous",
    "waypoint": "waypoint",
    "lemniscate": "lissajous",
    "composite": "lissajous"
}


def build_transfer_tasks(
    manifest_rows: list[dict],
    pid_configs: dict,
    pid_source_files: dict,
    *,
    pid_family: str = "all",
    include_native: bool = False,
    representative_only: bool = False,
) -> list[tuple[dict, str, dict, str]]:
    tasks: list[tuple[dict, str, dict, str]] = []
    representative_mode = representative_only or pid_family == "representative"

    for row_dict in manifest_rows:
        scenario_fam = row_dict["family"]

        if representative_mode:
            transfer_fam = REPRESENTATIVE_MAPPING.get(scenario_fam, "lissajous")
            if transfer_fam in pid_configs:
                tasks.append(
                    (row_dict, transfer_fam, pid_configs[transfer_fam], pid_source_files[transfer_fam])
                )
            continue

        if pid_family == "all":
            target_pids = list(pid_configs.keys())
        elif pid_family in pid_configs:
            target_pids = [pid_family]
        else:
            target_pids = []

        for transfer_fam in target_pids:
            if scenario_fam == transfer_fam and not include_native:
                continue
            tasks.append(
                (row_dict, transfer_fam, pid_configs[transfer_fam], pid_source_files[transfer_fam])
            )

    return tasks


def _load_previous_report_rows(report_path: str) -> dict[tuple[str, str], dict]:
    if not os.path.exists(report_path):
        return {}
    previous_df = pd.read_csv(report_path)
    rows: dict[tuple[str, str], dict] = {}
    for _, row in previous_df.iterrows():
        key = (str(row["scenario_id"]), str(row["pid_family"]))
        rows[key] = row.to_dict()
    return rows


def refresh_transfer_report(
    manifest_rows: list[dict],
    dataset_path: str,
    pid_configs: dict,
    pid_source_files: dict,
    *,
    pid_family: str = "all",
    include_native: bool = False,
    representative_only: bool = False,
    previous_report_path: str | None = None,
) -> list[dict]:
    tasks = build_transfer_tasks(
        manifest_rows,
        pid_configs,
        pid_source_files,
        pid_family=pid_family,
        include_native=include_native,
        representative_only=representative_only,
    )
    report_path = previous_report_path or os.path.join(dataset_path, "run_report_classic_transfer.csv")
    previous_rows = _load_previous_report_rows(report_path)

    report: list[dict] = []
    for scenario_row, transfer_family, pid_data, pid_source_file in tasks:
        scenario_id = scenario_row["scenario_id"]
        transfer_scenario_id = f"{scenario_id}_with_pid_{transfer_family}"
        result_dir = os.path.join(dataset_path, "results_transfer", transfer_scenario_id)
        metrics_file = os.path.join(result_dir, "metrics.json")
        transfer_scenario_path = os.path.join(
            dataset_path, "scenarios_transfer", f"{transfer_scenario_id}.yaml"
        )
        rel_result_dir = os.path.relpath(result_dir, dataset_path)

        if not os.path.exists(metrics_file):
            continue

        scenario_config = {}
        if os.path.exists(transfer_scenario_path):
            with open(transfer_scenario_path, "r", encoding="utf-8") as file:
                scenario_config = yaml.safe_load(file) or {}
        else:
            orig_scenario_path = os.path.join(dataset_path, scenario_row["scenario_path"])
            if os.path.exists(orig_scenario_path):
                with open(orig_scenario_path, "r", encoding="utf-8") as file:
                    scenario_config = yaml.safe_load(file) or {}

        report_key = (scenario_id, transfer_family)
        previous_row = previous_rows.get(report_key, {})
        previous_status = previous_row.get("execution_status") or previous_row.get("status")
        previous_provenance = previous_row.get("report_provenance")
        if isinstance(previous_provenance, float) and pd.isna(previous_provenance):
            previous_provenance = None
        if is_preserved_transfer_execution_status(
            previous_status if isinstance(previous_status, str) else None,
            report_provenance=previous_provenance if isinstance(previous_provenance, str) else None,
        ):
            execution_status = previous_status
            report_provenance = previous_provenance or "live"
        else:
            execution_status = "RECOVERED"
            report_provenance = "refreshed"
        termination_reason, mission_success, safety_success = _read_transfer_outcome(
            metrics_file, scenario_config
        )
        report.append(
            _build_report_row(
                scenario_row,
                transfer_family,
                rel_result_dir,
                execution_status=execution_status,
                termination_reason=termination_reason,
                mission_success=mission_success,
                safety_success=safety_success,
                report_provenance=report_provenance,
            )
        )
    return report


def _transfer_is_current(
    transfer_scenario_path: str,
    transfer_family: str,
    pid_data: dict,
    pid_source_file: str,
) -> bool:
    if not os.path.exists(transfer_scenario_path):
        return False

    with open(transfer_scenario_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    meta = config.get("transfer_meta", {})
    if meta.get("pid_family") != transfer_family:
        return False
    if meta.get("pid_source_file") != os.path.basename(pid_source_file):
        return False
    if meta.get("pid_fingerprint") != pid_gains_fingerprint(pid_data):
        return False

    return controller_gains_match(config.get("controller", {}), pid_data, transfer_family)


def _read_transfer_outcome(metrics_file: str, scenario_config: dict) -> tuple[str, bool, bool]:
    if not os.path.exists(metrics_file):
        return "", False, False
    with open(metrics_file, "r", encoding="utf-8") as file:
        metrics = json.load(file)
    termination_reason = metrics.get("termination_reason", "")
    trajectory_type = trajectory_type_from_config(scenario_config)
    outcome = evaluate_termination_outcome(
        termination_reason,
        trajectory_type=trajectory_type,
        family=scenario_config.get("family"),
    )
    return termination_reason, outcome["mission_success"], outcome["safety_success"]


def _build_report_row(
    scenario_row: dict,
    transfer_family: str,
    result_dir: str,
    *,
    execution_status: str,
    termination_reason: str = "",
    mission_success: bool = False,
    safety_success: bool = False,
    report_provenance: str = "live",
) -> dict:
    return {
        "scenario_id": scenario_row["scenario_id"],
        "baseline_family": scenario_row["family"],
        "pid_family": transfer_family,
        "controller_label": f"classic_pid_{transfer_family}",
        "status": execution_status,
        "execution_status": execution_status,
        "execution_success": execution_status in ("EXECUTED", "SKIPPED", "RECOVERED"),
        "termination_reason": termination_reason,
        "mission_success": mission_success,
        "safety_success": safety_success,
        "control_success": mission_success,
        "report_provenance": report_provenance,
        "result_dir": result_dir,
    }


def _run_transfer_row(
    scenario_row,
    dataset_path,
    transfer_family,
    pid_data,
    pid_source_file,
    no_visualization,
    rerun,
):
    scenario_id = scenario_row["scenario_id"]
    orig_scenario_path = os.path.join(dataset_path, scenario_row["scenario_path"])

    transfer_scenario_id = f"{scenario_id}_with_pid_{transfer_family}"

    # Directorio de salida
    result_dir = os.path.join(dataset_path, "results_transfer", transfer_scenario_id)
    metrics_file = os.path.join(result_dir, "metrics.json")

    transfer_scenario_dir = os.path.join(dataset_path, "scenarios_transfer")
    transfer_scenario_path = os.path.join(
        transfer_scenario_dir,
        f"{transfer_scenario_id}.yaml",
    )

    rel_result_dir = os.path.relpath(result_dir, dataset_path)

    if (
        os.path.exists(metrics_file)
        and not rerun
        and _transfer_is_current(transfer_scenario_path, transfer_family, pid_data, pid_source_file)
    ):
        skipped_config = {}
        if os.path.exists(transfer_scenario_path):
            with open(transfer_scenario_path, "r", encoding="utf-8") as file:
                skipped_config = yaml.safe_load(file) or {}
        elif os.path.exists(orig_scenario_path):
            with open(orig_scenario_path, "r", encoding="utf-8") as file:
                skipped_config = yaml.safe_load(f) or {}
        termination_reason, mission_success, safety_success = _read_transfer_outcome(
            metrics_file, skipped_config
        )
        return _build_report_row(
            scenario_row,
            transfer_family,
            rel_result_dir,
            execution_status="SKIPPED",
            termination_reason=termination_reason,
            mission_success=mission_success,
            safety_success=safety_success,
        )

    try:
        with open(orig_scenario_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Modificar controlador y salida
        config["name"] = transfer_scenario_id
        config["controller"] = {
            "type": "classic",
            "pid_family": transfer_family,
            "Kp_pos": pid_data.get("Kp_pos"),
            "Kd_pos": pid_data.get("Kd_pos"),
            "Kp_att": pid_data.get("Kp_att"),
            "Kd_att": pid_data.get("Kd_att"),
        }
        if "max_body_moments_Nm" in pid_data:
            config["controller"]["max_body_moments_Nm"] = pid_data["max_body_moments_Nm"]

        config["transfer_meta"] = {
            "pid_family": transfer_family,
            "pid_source_file": os.path.basename(pid_source_file),
            "pid_fingerprint": pid_gains_fingerprint(pid_data),
        }

        config["output"] = {
            "dir": result_dir,
            "telemetry_file": "telemetry.json",
            "metrics_file": "metrics.json"
        }

        os.makedirs(transfer_scenario_dir, exist_ok=True)

        with open(transfer_scenario_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, sort_keys=False)

        run_simulation(transfer_scenario_path, visualization=not no_visualization)
        termination_reason, mission_success, safety_success = _read_transfer_outcome(
            metrics_file, config
        )
        return _build_report_row(
            scenario_row,
            transfer_family,
            rel_result_dir,
            execution_status="EXECUTED",
            termination_reason=termination_reason,
            mission_success=mission_success,
            safety_success=safety_success,
        )
    except Exception as exc:
        return _build_report_row(
            scenario_row,
            transfer_family,
            rel_result_dir,
            execution_status=f"FAILED: {exc}",
        )


def main():
    parser = argparse.ArgumentParser(description="Run classical PID transfer simulations.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to target dataset directory (e.g. data/classic_dataset/v1)")
    parser.add_argument("--pid-source-dataset", type=str, default="data/classic_dataset/v1", help="Path to source dataset for frozen PIDs (default: data/classic_dataset/v1)")
    parser.add_argument("--pid-family", type=str, default="all", choices=["all", "representative", "hold", "circle", "lissajous", "waypoint"], help="Filter by PID family to transfer (default: all)")
    parser.add_argument("--split", type=str, help="Filter original scenarios by split (e.g. test, ood)")
    parser.add_argument("--include-native", action="store_true", help="Include diagonal (native baseline family run)")
    parser.add_argument("--representative-only", action="store_true", help="Run only the representative PID family mapping (same as --pid-family representative)")
    parser.add_argument("--family", type=str, help="Filter original scenarios by baseline family")
    parser.add_argument("--limit", type=int, help="Limit number of original scenarios to process")
    parser.add_argument("--no-visualization", action="store_true", default=True, help="Disable visualizations (default: True)")
    parser.add_argument("--visualization", action="store_false", dest="no_visualization", help="Enable visualizations")
    parser.add_argument("--rerun", action="store_true", help="Rerun already completed simulations")
    parser.add_argument(
        "--refresh-report-only",
        action="store_true",
        help="Rebuild run_report_classic_transfer.csv from existing metrics without simulating.",
    )
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel scenario processes.")

    args = parser.parse_args()

    manifest_path = os.path.join(args.dataset, "manifest.csv")
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)

    df = pd.read_csv(manifest_path)

    # Filtrar por split original si se pide
    if args.split and "split" in df.columns:
        df = df[df["split"] == args.split]

    # Filtrar por familia original si se pide
    if args.family:
        df = df[df["family"] == args.family]

    if args.limit:
        df = df.head(args.limit)

    # Cargar todos los PIDs de familia disponibles en la carpeta pids/ del dataset origen
    pids_dir = os.path.join(args.pid_source_dataset, "pids")
    if not os.path.exists(pids_dir):
        print(f"Error: PIDs directory not found at {pids_dir}")
        sys.exit(1)

    representative_mode = args.representative_only or (args.pid_family == "representative")
    if args.pid_family == "all":
        required_families = FROZEN_PID_FAMILIES
    elif representative_mode:
        required_families = FROZEN_PID_FAMILIES
    else:
        required_families = (args.pid_family,)

    try:
        pid_configs = load_all_frozen_pids(pids_dir, required_families=required_families)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    pid_source_files = {}
    for family in pid_configs:
        _, pid_path = load_frozen_pid_family(pids_dir, family)
        pid_source_files[family] = pid_path

    tasks = build_transfer_tasks(
        [row.to_dict() for _, row in df.iterrows()],
        pid_configs,
        pid_source_files,
        pid_family=args.pid_family,
        include_native=args.include_native,
        representative_only=args.representative_only,
    )

    if args.refresh_report_only:
        report = refresh_transfer_report(
            [row.to_dict() for _, row in df.iterrows()],
            args.dataset,
            pid_configs,
            pid_source_files,
            pid_family=args.pid_family,
            include_native=args.include_native,
            representative_only=args.representative_only,
        )
        report_path = os.path.join(args.dataset, "run_report_classic_transfer.csv")
        report_df = pd.DataFrame(report)
        if report_df.empty:
            print("No transfer metrics found to refresh report.")
            sys.exit(1)
        report_df.to_csv(report_path, index=False)
        print(f"Refreshed transfer run report at {report_path} ({len(report_df)} rows)")
        return

    total = len(tasks)
    print(f"Total transfer simulations to run: {total}")

    report = []

    if args.workers == 1:
        for index, (row, transfer_fam, pid_data, pid_source_file) in enumerate(tasks, start=1):
            print(f"[{index}/{total}] Running {row['scenario_id']} with PID of {transfer_fam}...")
            res = _run_transfer_row(
                row,
                args.dataset,
                transfer_fam,
                pid_data,
                pid_source_file,
                args.no_visualization,
                args.rerun,
            )
            print(f"[{index}/{total}] Result: {res['status']}")
            report.append(res)
    else:
        print(f"Running transfer simulations with {args.workers} worker processes.")
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(
                    _run_transfer_row,
                    row,
                    args.dataset,
                    transfer_fam,
                    pid_data,
                    pid_source_file,
                    args.no_visualization,
                    args.rerun,
                )
                for row, transfer_fam, pid_data, pid_source_file in tasks
            ]
            for index, future in enumerate(as_completed(futures), start=1):
                res = future.result()
                print(f"[{index}/{total}] {res['scenario_id']} with PID of {res['pid_family']}: {res['status']}")
                report.append(res)

    # Guardar reporte de transferencia
    report_path = os.path.join(args.dataset, "run_report_classic_transfer.csv")
    report_df = pd.DataFrame(report)
    if os.path.exists(report_path) and not report_df.empty:
        old_report = pd.read_csv(report_path)
        # Combinar y quitar duplicados por escenario_id + pid_family
        report_df = pd.concat([old_report, report_df]).drop_duplicates(subset=["scenario_id", "pid_family"], keep="last")

    if not report_df.empty:
        report_df.to_csv(report_path, index=False)
        print(f"Transfer run report saved to {report_path}")

    # Exit with error if any scenario failed in this run
    if any(r["execution_status"].startswith("FAILED") for r in report):
        print("Error: One or more simulation runs failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
