import argparse
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any
from simulador_quad.datasets.classic import passes_hard_filters

def load_metrics(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Summarize classical control dataset results.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory")
    
    args = parser.parse_args()
    
    manifest_path = os.path.join(args.dataset, "manifest.csv")
    if not os.path.exists(manifest_path):
        print(f"Error: Manifest not found at {manifest_path}")
        return
        
    df_manifest = pd.read_csv(manifest_path)
    
    rows = []
    
    for _, row in df_manifest.iterrows():
        metrics_file = os.path.join(args.dataset, row["result_dir"], "metrics.json")
        
        data = row.to_dict()
        if os.path.exists(metrics_file):
            try:
                metrics = load_metrics(metrics_file)
                # Apply hard filters from spec
                is_valid, reason = passes_hard_filters(metrics, row["family"])
                
                data.update({
                    "rmse_m": metrics.get("position_rmse_m"),
                    "max_err_m": metrics.get("position_max_err_m"),
                    "sat_pct": metrics.get("saturation_percentage"),
                    "deg_pct": metrics.get("degradation_percentage"),
                    "duration_s": metrics.get("duration_s"),
                    "termination": metrics.get("termination_reason"),
                    "status": "VALID" if is_valid else "INVALID",
                    "invalid_reason": reason if not is_valid else ""
                })
                data["is_valid"] = is_valid
            except Exception as e:
                data["status"] = "ERROR"
                data["invalid_reason"] = str(e)
                data["is_valid"] = False
        else:
            data["status"] = "MISSING"
            data["invalid_reason"] = "Metrics file not found"
            data["is_valid"] = False
            
        rows.append(data)
        
    df_summary = pd.DataFrame(rows)
    summary_path = os.path.join(args.dataset, "summary.csv")
    df_summary.to_csv(summary_path, index=False)
    print(f"Summary saved to {summary_path}")
    
    # Print aggregates
    if not df_summary.empty:
        total = len(df_summary)
        valid_count = df_summary["is_valid"].sum()
        missing_count = (df_summary["status"] == "MISSING").sum()
        invalid_count = (df_summary["status"] == "INVALID").sum()
        error_count = (df_summary["status"] == "ERROR").sum()
        
        print(f"\nResults Overview:")
        print(f"  Total:    {total}")
        print(f"  Valid:    {valid_count} ({valid_count/total*100:.1f}%)")
        print(f"  Invalid:  {invalid_count}")
        print(f"  Missing:  {missing_count}")
        print(f"  Errors:   {error_count}")
        
        if valid_count > 0:
            agg = df_summary[df_summary["is_valid"]].groupby("family")[["rmse_m", "max_err_m", "sat_pct"]].mean()
            print("\nMean metrics for VALID episodes by family:")
            print(agg)
        
        if invalid_count > 0:
            print("\nTop reasons for invalid episodes:")
            print(df_summary[df_summary["status"] == "INVALID"]["invalid_reason"].value_counts().head())

if __name__ == "__main__":
    main()
