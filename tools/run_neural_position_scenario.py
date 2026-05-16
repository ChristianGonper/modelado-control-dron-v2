"""
Ejecuta un escenario con el controlador neuronal de lazo externo.
"""
import argparse
import os
import tempfile
import yaml

from simulador_quad.app import run_simulation


def main():
    parser = argparse.ArgumentParser(description="Run a scenario with a neural position-loop controller.")
    parser.add_argument("--scenario", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--normalization", type=str, required=True)
    parser.add_argument("--architecture", type=str, choices=["mlp", "gru", "lstm"], default="mlp")
    parser.add_argument("--out", type=str)
    parser.add_argument("--no-visualization", action="store_false", dest="visualization", default=True)
    args = parser.parse_args()

    with open(args.scenario, "r") as f:
        config = yaml.safe_load(f)

    config_path = os.path.join(os.path.dirname(os.path.dirname(args.checkpoint)), "config.yaml")
    model_config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            model_config = yaml.safe_load(f)

    config["controller"] = {
        "type": "neural_position",
        "architecture": args.architecture,
        "checkpoint_path": args.checkpoint,
        "normalization_path": args.normalization,
        "sequence_length": model_config.get("sequence_length", 20) or 20,
        "base_Kp_pos": model_config.get("base_Kp_pos", [2.0, 2.0, 5.0]),
        "base_Kd_pos": model_config.get("base_Kd_pos", [1.0, 1.0, 2.0]),
        "multiplier_clip": model_config.get("multiplier_clip", [0.25, 4.0]),
    }

    if args.out:
        config["output"]["dir"] = args.out
    else:
        config["output"]["dir"] = config["output"].get("dir", "results/temp") + f"_neural_position_{args.architecture}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(config, tmp)
        temp_scenario_path = tmp.name

    try:
        command = (
            f"uv run python tools/run_neural_position_scenario.py --scenario {args.scenario} "
            f"--checkpoint {args.checkpoint} --normalization {args.normalization} --architecture {args.architecture}"
        )
        if not args.visualization:
            command += " --no-visualization"
        run_simulation(temp_scenario_path, visualization=args.visualization, command=command)
    finally:
        if os.path.exists(temp_scenario_path):
            os.remove(temp_scenario_path)


if __name__ == "__main__":
    main()
