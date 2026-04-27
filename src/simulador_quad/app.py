import argparse
import os
import sys
import numpy as np
from simulador_quad.scenarios.loader import load_scenario, instantiate_scenario
from simulador_quad.runner import SimulationRunner
from simulador_quad.metrics.report import compute_metrics
from simulador_quad.telemetry.export import export_telemetry_json, export_metrics_json

def run_simulation(scenario_path: str):
    print(f"Cargando escenario: {scenario_path}")
    config = load_scenario(scenario_path)
    
    # Instanciar componentes
    v_params, mixer, actuators, initial_state, trajectory, controller, wind, noise = instantiate_scenario(config)
    
    # Configurar runner
    t_cfg = config['timing']
    term_cfg = config['termination']
    
    runner = SimulationRunner(
        physics_dt_s=t_cfg['physics_dt_s'],
        control_dt_s=t_cfg['control_dt_s'],
        telemetry_dt_s=t_cfg['telemetry_dt_s'],
        vehicle_params=v_params,
        mixer=mixer,
        actuators=actuators,
        wind_model=wind,
        observation_noise=noise,
        max_duration_s=term_cfg['max_duration_s'],
        z_min_m=term_cfg['z_min_m'],
        max_attitude_angle_rad=term_cfg.get('max_attitude_angle_rad', 1.256),
        max_saturation_duration_s=term_cfg.get('max_saturation_duration_s', 1.0)
    )
    
    # Función control para el runner (adaptador)
    def controller_func(t, obs, ref):
        return controller.compute_control(t, obs, ref)
    
    # Ejecutar
    print("Iniciando simulación...")
    result_raw = runner.run(initial_state, controller_func, trajectory)
    telemetry = result_raw['telemetry']
    reason = result_raw['termination_reason']
    
    print(f"Simulación terminada. Razón: {reason}")
    
    # Métricas
    metadata = {
        "scenario_name": config['name'],
        "seed": config.get('seed', 42),
        "config": config  # Guardamos todo para máxima trazabilidad
    }
    metrics = compute_metrics(telemetry, reason, metadata)
    
    # Exportar
    out_cfg = config['output']
    os.makedirs(out_cfg['dir'], exist_ok=True)
    
    tel_path = os.path.join(out_cfg['dir'], out_cfg['telemetry_file'])
    met_path = os.path.join(out_cfg['dir'], out_cfg['metrics_file'])
    
    print(f"Exportando telemetría a {tel_path}...")
    export_telemetry_json(telemetry, tel_path)
    
    print(f"Exportando métricas a {met_path}...")
    export_metrics_json(metrics, met_path)
    
    print("Métricas clave:")
    print(f"  RMSE Posición: {metrics['position_rmse_m']:.4f} m")
    print(f"  Duración: {metrics['duration_s']:.2f} s")

def main():
    parser = argparse.ArgumentParser(description="Simulador Quadcopter 6DOF")
    subparsers = parser.add_subparsers(dest="command")
    
    run_parser = subparsers.add_parser("run", help="Ejecutar un escenario")
    run_parser.add_argument("scenario", help="Ruta al archivo YAML del escenario")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_simulation(args.scenario)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
