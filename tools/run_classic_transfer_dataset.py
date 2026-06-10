import argparse
import os
import sys
import yaml
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from simulador_quad.app import run_simulation


def _run_transfer_row(scenario_row, dataset_path, transfer_family, pid_data, no_visualization, rerun):
    scenario_id = scenario_row["scenario_id"]
    orig_scenario_path = os.path.join(dataset_path, scenario_row["scenario_path"])
    
    transfer_scenario_id = f"{scenario_id}_with_pid_{transfer_family}"
    
    # Directorio de salida
    result_dir = os.path.join(dataset_path, "results_transfer", transfer_scenario_id)
    metrics_file = os.path.join(result_dir, "metrics.json")
    
    # Comprobar si ya existe y no queremos re-ejecutar
    if os.path.exists(metrics_file) and not rerun:
        return {
            "scenario_id": scenario_id,
            "baseline_family": scenario_row["family"],
            "pid_family": transfer_family,
            "controller_label": f"classic_transfer_{transfer_family}",
            "status": "SKIPPED",
            "result_dir": os.path.relpath(result_dir, dataset_path),
        }
        
    try:
        # Cargar escenario original
        with open(orig_scenario_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        # Modificar controlador y salida
        config["name"] = transfer_scenario_id
        config["controller"] = {
            "type": "classic",
            "Kp_pos": pid_data.get("Kp_pos"),
            "Kd_pos": pid_data.get("Kd_pos"),
            "Kp_att": pid_data.get("Kp_att"),
            "Kd_att": pid_data.get("Kd_att"),
        }
        if "max_body_moments_Nm" in pid_data:
            config["controller"]["max_body_moments_Nm"] = pid_data["max_body_moments_Nm"]
            
        config["output"] = {
            "dir": result_dir,
            "telemetry_file": "telemetry.json",
            "metrics_file": "metrics.json"
        }
        
        # Guardar archivo de escenario de transferencia
        transfer_scenario_dir = os.path.join(dataset_path, "scenarios_transfer")
        os.makedirs(transfer_scenario_dir, exist_ok=True)
        transfer_scenario_path = os.path.join(transfer_scenario_dir, f"{transfer_scenario_id}.yaml")
        
        with open(transfer_scenario_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, sort_keys=False)
            
        # Ejecutar simulación
        run_simulation(transfer_scenario_path, visualization=not no_visualization)
        status = "SUCCESS"
    except Exception as exc:
        status = f"FAILED: {exc}"
        
    return {
        "scenario_id": scenario_id,
        "baseline_family": scenario_row["family"],
        "pid_family": transfer_family,
        "controller_label": f"classic_transfer_{transfer_family}",
        "status": status,
        "result_dir": os.path.relpath(result_dir, dataset_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Run classical PID transfer simulations.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory (e.g. data/classic_dataset/v1)")
    parser.add_argument("--family", type=str, help="Filter original scenarios by baseline family")
    parser.add_argument("--limit", type=int, help="Limit number of original scenarios to process")
    parser.add_argument("--no-visualization", action="store_true", default=True, help="Disable visualizations (default: True)")
    parser.add_argument("--visualization", action="store_false", dest="no_visualization", help="Enable visualizations")
    parser.add_argument("--rerun", action="store_true", help="Rerun already completed simulations")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel scenario processes.")
    
    args = parser.parse_args()
    
    manifest_path = os.path.join(args.dataset, "manifest.csv")
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        sys.exit(1)
        
    df = pd.read_csv(manifest_path)
    
    # Filtrar por familia original si se pide
    if args.family:
        df = df[df["family"] == args.family]
        
    if args.limit:
        df = df.head(args.limit)
        
    # Cargar todos los PIDs de familia disponibles en la carpeta pids/
    pids_dir = os.path.join(args.dataset, "pids")
    if not os.path.exists(pids_dir):
        print(f"Error: PIDs directory not found at {pids_dir}")
        sys.exit(1)
        
    families = ["hold", "circle", "lissajous", "waypoint"]
    pid_configs = {}
    for fam in families:
        # Intentamos encontrar el archivo pid_<fam>_*.yaml
        pid_file = None
        for f in os.listdir(pids_dir):
            if f.startswith(f"pid_{fam}_") and f.endswith(".yaml"):
                pid_file = os.path.join(pids_dir, f)
                break
        if pid_file is None:
            print(f"Warning: No PID file found for family '{fam}' in {pids_dir}. Skipping as transfer candidate.")
            continue
            
        with open(pid_file, "r", encoding="utf-8") as f:
            pid_configs[fam] = yaml.safe_load(f)
            
    if not pid_configs:
        print("Error: No PID configurations loaded.")
        sys.exit(1)
        
    tasks = []
    for _, row in df.iterrows():
        for transfer_fam, pid_data in pid_configs.items():
            if row["family"] == transfer_fam:
                continue
            # Agregamos la combinación original-escenario + PID de transferencia
            tasks.append((row.to_dict(), transfer_fam, pid_data))
            
    total = len(tasks)
    print(f"Total transfer simulations to run: {total}")
    
    report = []
    
    if args.workers == 1:
        for index, (row, transfer_fam, pid_data) in enumerate(tasks, start=1):
            print(f"[{index}/{total}] Running {row['scenario_id']} with PID of {transfer_fam}...")
            res = _run_transfer_row(row, args.dataset, transfer_fam, pid_data, args.no_visualization, args.rerun)
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
                    args.no_visualization, 
                    args.rerun
                )
                for row, transfer_fam, pid_data in tasks
            ]
            for index, future in enumerate(as_completed(futures), start=1):
                res = future.result()
                print(f"[{index}/{total}] {res['scenario_id']} with PID of {res['pid_family']}: {res['status']}")
                report.append(res)
                
    # Guardar reporte de transferencia
    report_path = os.path.join(args.dataset, "run_report_classic_transfer.csv")
    report_df = pd.DataFrame(report)
    if os.path.exists(report_path):
        old_report = pd.read_csv(report_path)
        # Combinar y quitar duplicados por escenario_id + pid_family
        report_df = pd.concat([old_report, report_df]).drop_duplicates(subset=["scenario_id", "pid_family"], keep="last")
        
    report_df.to_csv(report_path, index=False)
    print(f"Transfer run report saved to {report_path}")

    # Exit with error if any scenario failed in this run
    if any(r["status"].startswith("FAILED") for r in report):
        print("Error: One or more simulation runs failed.")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
