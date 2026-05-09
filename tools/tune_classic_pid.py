import argparse
import os
import yaml
import numpy as np
import datetime
from typing import Dict, Any, List
from simulador_quad.datasets.classic import (
    PROFILES, BASE_VEHICLE, build_scenario_config, get_geometry_variants,
    pid_candidate_score, passes_hard_filters
)
from simulador_quad.scenarios.loader import instantiate_scenario
from simulador_quad.runner import SimulationRunner
from simulador_quad.metrics.report import compute_metrics

def run_candidate(family: str, pid_config: Dict[str, Any], trajectory_cfg: Dict[str, Any]) -> Dict[str, Any]:
    # Build nominal scenario
    scenario_id = f"tune_{family}_nominal"
    config = build_scenario_config(
        scenario_id, family, trajectory_cfg, "P0_nominal", pid_config, 1042, "tmp_tuning"
    )
    
    v_params, mixer, actuators, initial_state, trajectory, controller, wind, noise = instantiate_scenario(config)
    
    runner = SimulationRunner(
        physics_dt_s=config["timing"]["physics_dt_s"],
        control_dt_s=config["timing"]["control_dt_s"],
        telemetry_dt_s=config["timing"]["telemetry_dt_s"],
        vehicle_params=v_params,
        mixer=mixer,
        actuators=actuators,
        wind_model=wind,
        observation_noise=noise,
        max_duration_s=config["termination"]["max_duration_s"]
    )
    
    result = runner.run(initial_state, controller.compute_control, trajectory)
    metrics = compute_metrics(result["telemetry"], result["termination_reason"])
    
    return {
        "metrics": metrics,
        "telemetry": result["telemetry"],
        "pid_config": pid_config
    }

def main():
    parser = argparse.ArgumentParser(description="Tune classical PID gains for a family.")
    parser.add_argument("--family", type=str, required=True, choices=["hold", "circle", "lissajous", "waypoint"])
    parser.add_argument("--out", type=str, required=True, help="Output directory for PID YAML")
    parser.add_argument("--version", type=str, default="v1")
    
    args = parser.parse_args()
    
    # Defaults
    base_gains = {
        "Kp_pos": np.array([2.0, 2.0, 5.0]),
        "Kd_pos": np.array([1.0, 1.0, 2.0]),
        "Kp_att": np.array([4.0, 4.0, 1.0]),
        "Kd_att": np.array([1.5, 1.5, 0.5])
    }
    
    # Sweep multipliers
    multipliers = [0.8, 1.0, 1.2]
    
    # Use the first geometry variant for tuning
    trajectory_cfg = get_geometry_variants(args.family)[0][1]
    
    candidates = []
    
    print(f"Tuning PID for family: {args.family}...")
    
    # Simple grid search (3^4 = 81 runs)
    for m_kp_pos in multipliers:
        for m_kd_pos in multipliers:
            for m_kp_att in multipliers:
                for m_kd_att in multipliers:
                    pid_config = {
                        "Kp_pos": (base_gains["Kp_pos"] * m_kp_pos).tolist(),
                        "Kd_pos": (base_gains["Kd_pos"] * m_kd_pos).tolist(),
                        "Kp_att": (base_gains["Kp_att"] * m_kp_att).tolist(),
                        "Kd_att": (base_gains["Kd_att"] * m_kd_att).tolist()
                    }
                    
                    res = run_candidate(args.family, pid_config, trajectory_cfg)
                    ok, msg = passes_hard_filters(res["metrics"], args.family)
                    
                    if ok:
                        score = pid_candidate_score(res["metrics"], res["telemetry"], args.family)
                        candidates.append({
                            "pid_config": pid_config,
                            "score": score,
                            "metrics": res["metrics"],
                            "sum_gains": m_kp_pos + m_kd_pos + m_kp_att + m_kd_att # For conservative tie-break
                        })
    
    if not candidates:
        print("Error: No candidates passed hard filters.")
        return
    
    # Select best score
    # Sort by score ascending, then by sum of gains ascending (conservative)
    candidates.sort(key=lambda x: x["score"])
    best = candidates[0]
    
    # Apply 5% rule
    best_score = best["score"]
    threshold = best_score * 1.05
    competitive = [c for c in candidates if c["score"] <= threshold]
    # Among competitive, pick the one with lowest gains sum
    best = min(competitive, key=lambda x: x["sum_gains"])
    
    print(f"Best score: {best['score']:.4f}")
    
    # Save PID YAML
    os.makedirs(args.out, exist_ok=True)
    out_file = os.path.join(args.out, f"pid_{args.family}_{args.version}.yaml")
    
    output_data = {
        "pid_id": f"pid_{args.family}_{args.version}",
        "family": args.family,
        "version": args.version,
        "Kp_pos": best["pid_config"]["Kp_pos"],
        "Kd_pos": best["pid_config"]["Kd_pos"],
        "Kp_att": best["pid_config"]["Kp_att"],
        "Kd_att": best["pid_config"]["Kd_att"],
        "tuning_info": {
            "score": best["score"],
            "date": datetime.datetime.now().isoformat(),
            "metrics": {
                "rmse": best["metrics"]["position_rmse_m"],
                "max_err": best["metrics"]["position_max_err_m"],
                "sat_pct": best["metrics"]["saturation_percentage"]
            }
        }
    }
    
    with open(out_file, 'w') as f:
        yaml.dump(output_data, f, sort_keys=False)
        
    print(f"Saved best PID to {out_file}")

if __name__ == "__main__":
    main()
