import argparse
import hashlib
import os
import platform
import subprocess
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Dict

from simulador_quad.scenarios.loader import load_scenario, instantiate_scenario
from simulador_quad.runner import SimulationRunner
from simulador_quad.metrics.report import compute_metrics
from simulador_quad.telemetry.export import export_telemetry_json, export_metrics_json
from simulador_quad.visualization.plots import plot_telemetry
from simulador_quad.visualization.three_d import export_trajectory_viewer_html


def _package_version() -> str:
    try:
        return importlib_metadata.version("simulador-quad")
    except importlib_metadata.PackageNotFoundError:
        return "unknown"


def _run_git_command(args: list[str], empty_value: str = "unknown") -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=Path.cwd(),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"

    value = result.stdout.strip()
    return value if value else empty_value


def _git_metadata() -> Dict[str, Any]:
    commit = _run_git_command(["rev-parse", "HEAD"])
    dirty_raw = _run_git_command(["status", "--porcelain"], empty_value="")

    if dirty_raw == "unknown":
        dirty: bool | str = "unknown"
    else:
        dirty = dirty_raw != ""

    return {
        "git_commit": commit,
        "git_dirty": dirty,
    }


def _file_sha256(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return "unknown"

    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _controller_metadata(controller: Any, config: Dict[str, Any]) -> Dict[str, Any]:
    controller_cfg = config.get("controller", {})
    parameters: Dict[str, Any] = {
        "config": controller_cfg,
    }

    for attr in ("Kp_pos", "Kd_pos", "Kp_att", "Kd_att", "max_thrust", "min_thrust", "max_moments_Nm"):
        if hasattr(controller, attr):
            parameters[attr] = getattr(controller, attr)

    return {
        "type": controller_cfg.get("type", controller.__class__.__name__),
        "class": controller.__class__.__name__,
        "parameters": parameters,
    }


def _resolved_config(config: Dict[str, Any], runner: SimulationRunner) -> Dict[str, Any]:
    resolved = dict(config)
    resolved["timing_effective"] = {
        "physics_dt_s": runner.physics_dt_s,
        "control_dt_s": runner.control_dt_s,
        "telemetry_dt_s": runner.telemetry_dt_s,
    }
    resolved["termination_effective"] = {
        "max_duration_s": runner.max_duration_s,
        "z_min_m": runner.z_min_m,
        "max_position_m": runner.max_position_m,
        "max_velocity_m_s": runner.max_velocity_m_s,
        "max_attitude_angle_rad": runner.max_attitude_angle_rad,
        "max_saturation_duration_s": runner.max_saturation_duration_s,
    }
    return resolved


def _default_run_command(scenario_path: str, visualization: bool) -> str:
    command = f"uv run simulador-quad run {scenario_path}"
    if not visualization:
        command += " --no-visualization"
    return command


def build_execution_metadata(
    config: Dict[str, Any],
    scenario_path: str,
    controller: Any,
    runner: SimulationRunner,
    visualization: bool,
    command: str | None = None,
) -> Dict[str, Any]:
    metadata = {
        "scenario_name": config["name"],
        "scenario_path": scenario_path,
        "scenario_file_hash": _file_sha256(scenario_path),
        "seed": config.get("seed", 42),
        "controller": _controller_metadata(controller, config),
        "command": command or _default_run_command(scenario_path, visualization),
        "visualization_requested": visualization,
        "package_version": _package_version(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "uv_lock_hash": _file_sha256("uv.lock"),
        "config": config,
        "config_resolved": _resolved_config(config, runner),
    }
    metadata.update(_git_metadata())
    return metadata


def run_simulation(scenario_path: str, visualization: bool = True, command: str | None = None):
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
    
    # Ejecutar
    print("Iniciando simulación...")
    result_raw = runner.run(initial_state, controller, trajectory)
    telemetry = result_raw['telemetry']
    reason = result_raw['termination_reason']
    
    print(f"Simulación terminada. Razón: {reason}")
    
    # Métricas
    metadata = build_execution_metadata(
        config=config,
        scenario_path=scenario_path,
        controller=controller,
        runner=runner,
        visualization=visualization,
        command=command,
    )
    metrics = compute_metrics(telemetry, reason, metadata)

    # Surface runtime outer-force clip stats (spec-required for closed-loop evaluation / Success Criteria)
    # This makes force_*_clip_percentage available in metrics.json for NeuralOuterForceController runs
    # (tool-specific path per original plan preference; does not alter classic metrics/report.py)
    if hasattr(controller, "get_clip_stats"):
        try:
            clip_stats = controller.get_clip_stats()
            for k in ("force_norm_clip_percentage", "force_tilt_clip_percentage", "force_norm_clip_count", "force_tilt_clip_count"):
                if k in clip_stats:
                    metrics[k] = clip_stats[k]
        except Exception:
            pass  # non-fatal; stats are best-effort for observability
    
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
    
    if visualization:
        print("Generando visualizaciones...")
        figures_dir = os.path.join(out_cfg['dir'], "figures")
        plot_telemetry(tel_path, figures_dir, met_path)
        
        viz_3d_path = os.path.join(out_cfg['dir'], "visualization_3d.html")
        export_trajectory_viewer_html(tel_path, viz_3d_path, met_path)
        print(f"  Visualización 3D: {viz_3d_path}")
        print(f"  Figuras PNG: {figures_dir}")

def main():
    parser = argparse.ArgumentParser(description="Simulador Quadcopter 6DOF")
    subparsers = parser.add_subparsers(dest="command")
    
    run_parser = subparsers.add_parser("run", help="Ejecutar un escenario")
    run_parser.add_argument("scenario", help="Ruta al archivo YAML del escenario")
    run_parser.add_argument("--no-visualization", action="store_false", dest="visualization", default=True,
                            help="No generar figuras ni visualización 3D")

    plot_parser = subparsers.add_parser("plot", help="Generar figuras desde telemetría JSON")
    plot_parser.add_argument("telemetry", help="Ruta al telemetry.json exportado por el simulador")
    plot_parser.add_argument("--metrics", help="Ruta opcional al metrics.json asociado")
    plot_parser.add_argument("--out", required=True, help="Directorio donde se escribirán las figuras PNG")
    
    args = parser.parse_args()
    
    if args.command == "run":
        run_simulation(
            args.scenario,
            visualization=args.visualization,
            command=_default_run_command(args.scenario, args.visualization),
        )
    elif args.command == "plot":
        paths = plot_telemetry(args.telemetry, args.out, args.metrics)
        print("Figuras generadas:")
        for path in paths:
            print(f"  {path}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
