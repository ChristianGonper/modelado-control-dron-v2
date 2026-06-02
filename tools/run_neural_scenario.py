"""
Script para ejecutar un escenario existente con un controlador neuronal outer-force.
"""
import argparse
import os
import tempfile
import yaml

from simulador_quad.app import run_simulation


def load_model_config(checkpoint_path: str) -> dict:
    config_path = os.path.join(os.path.dirname(os.path.dirname(checkpoint_path)), "config.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_architecture(checkpoint_path: str, architecture_override: str | None = None) -> str:
    model_config = load_model_config(checkpoint_path)
    return architecture_override or model_config.get("architecture", "mlp")


def build_neural_outer_force_config(
    scenario_path: str,
    checkpoint_path: str,
    normalization_path: str,
    architecture_override: str | None = None,
    device: str = "auto",
    out_dir: str | None = None,
) -> tuple[dict, str]:
    with open(scenario_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    model_config = load_model_config(checkpoint_path)
    architecture = architecture_override or model_config.get("architecture", "mlp")

    ctrl_override = {
        "type": "neural",
        "architecture": architecture,
        "checkpoint_path": checkpoint_path,
        "normalization_path": normalization_path,
        "sequence_length": model_config.get("sequence_length", 20) or 20,
        "clip_to_classic_limits": True,
        "device": device,
    }
    if model_config.get("controller_mode") == "neural_outer_force" or model_config.get("output_dim") == 3:
        ctrl_override["feature_version"] = model_config.get("feature_version", "outer_force_min_v1")
        ctrl_override["max_desired_tilt_rad"] = model_config.get("max_desired_tilt_rad", 0.52)
        ctrl_override["Kp_att"] = model_config.get("Kp_att", [4.0, 4.0, 1.0])
        ctrl_override["Kd_att"] = model_config.get("Kd_att", [1.5, 1.5, 0.5])

    config["controller"] = ctrl_override

    if out_dir:
        config["output"]["dir"] = out_dir
    else:
        config["output"]["dir"] = config["output"].get("dir", "results/temp") + f"_neural_{architecture}"

    return config, architecture


def run_neural_outer_force_scenario(
    scenario_path: str,
    checkpoint_path: str,
    normalization_path: str,
    architecture_override: str | None = None,
    device: str = "auto",
    out_dir: str | None = None,
    visualization: bool = True,
):
    config, architecture = build_neural_outer_force_config(
        scenario_path=scenario_path,
        checkpoint_path=checkpoint_path,
        normalization_path=normalization_path,
        architecture_override=architecture_override,
        device=device,
        out_dir=out_dir,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as tmp:
        yaml.dump(config, tmp)
        temp_scenario_path = tmp.name

    try:
        command = (
            f"uv run python tools/run_neural_scenario.py --scenario {scenario_path} "
            f"--checkpoint {checkpoint_path} --normalization {normalization_path} "
            f"--architecture {architecture} --device {device}"
        )
        if not visualization:
            command += " --no-visualization"
        run_simulation(temp_scenario_path, visualization=visualization, command=command)
    finally:
        if os.path.exists(temp_scenario_path):
            os.remove(temp_scenario_path)


def main():
    parser = argparse.ArgumentParser(description="Run a scenario with a neural outer-force controller.")
    parser.add_argument("--scenario", type=str, required=True, help="Base scenario YAML path.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to the neural checkpoint (.pt).")
    parser.add_argument("--normalization", type=str, required=True, help="Path to normalization.json.")
    parser.add_argument("--architecture", type=str, choices=["mlp", "gru", "lstm"], help="Override architecture from config.yaml.")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out", type=str, help="Override output directory.")
    parser.add_argument("--no-visualization", action="store_false", dest="visualization", default=True, help="Disable visualization.")

    args = parser.parse_args()

    run_neural_outer_force_scenario(
        scenario_path=args.scenario,
        checkpoint_path=args.checkpoint,
        normalization_path=args.normalization,
        architecture_override=args.architecture,
        device=args.device,
        out_dir=args.out,
        visualization=args.visualization,
    )


if __name__ == "__main__":
    main()