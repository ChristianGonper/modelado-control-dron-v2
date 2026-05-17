"""
Ejecuta un escenario con el controlador neuronal de lazo externo.
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
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}


def resolve_architecture(checkpoint_path: str, architecture_override: str | None = None) -> str:
    model_config = load_model_config(checkpoint_path)
    return architecture_override or model_config.get("architecture", "mlp")


def build_neural_position_config(
    scenario_path: str,
    checkpoint_path: str,
    normalization_path: str,
    architecture_override: str | None = None,
    device: str = "auto",
    out_dir: str | None = None,
) -> tuple[dict, str]:
    with open(scenario_path, "r") as f:
        config = yaml.safe_load(f)

    model_config = load_model_config(checkpoint_path)
    architecture = architecture_override or model_config.get("architecture", "mlp")

    config["controller"] = {
        "type": "neural_position",
        "architecture": architecture,
        "checkpoint_path": checkpoint_path,
        "normalization_path": normalization_path,
        "sequence_length": model_config.get("sequence_length", 20) or 20,
        "base_Kp_pos": model_config.get("base_Kp_pos", [2.0, 2.0, 5.0]),
        "base_Kd_pos": model_config.get("base_Kd_pos", [1.0, 1.0, 2.0]),
        "multiplier_clip": model_config.get("multiplier_clip", [0.25, 4.0]),
        "device": device,
    }

    if out_dir:
        config["output"]["dir"] = out_dir
    else:
        config["output"]["dir"] = config["output"].get("dir", "results/temp") + f"_neural_position_{architecture}"

    return config, architecture


def run_neural_position_scenario(
    scenario_path: str,
    checkpoint_path: str,
    normalization_path: str,
    architecture_override: str | None = None,
    device: str = "auto",
    out_dir: str | None = None,
    visualization: bool = True,
):
    config, architecture = build_neural_position_config(
        scenario_path=scenario_path,
        checkpoint_path=checkpoint_path,
        normalization_path=normalization_path,
        architecture_override=architecture_override,
        device=device,
        out_dir=out_dir,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(config, tmp)
        temp_scenario_path = tmp.name

    try:
        command = (
            f"uv run python tools/run_neural_position_scenario.py --scenario {scenario_path} "
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
    parser = argparse.ArgumentParser(description="Run a scenario with a neural position-loop controller.")
    parser.add_argument("--scenario", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--normalization", type=str, required=True)
    parser.add_argument("--architecture", type=str, choices=["mlp", "gru", "lstm"], help="Override architecture from config.yaml.")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out", type=str)
    parser.add_argument("--no-visualization", action="store_false", dest="visualization", default=True)
    args = parser.parse_args()

    run_neural_position_scenario(
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
