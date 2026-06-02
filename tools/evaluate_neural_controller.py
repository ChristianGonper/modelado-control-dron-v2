"""
Script para evaluar controladores neuronales entrenados (modo supervisado).

Splits in-distribution: train, val, test desde --dataset (manifest.csv).
Split OOD: requiere --ood-dataset con filas manifest.split == 'ood' (no se mapea a train).
"""
import argparse
import os
import json
import yaml
import torch
from torch.utils.data import DataLoader
from simulador_quad.ml.dataset import (
    ImitationDataset,
    SequentialImitationDataset,
    OuterForceDataset,
    SequentialOuterForceDataset,
)
from simulador_quad.ml.normalization import Normalizer
from simulador_quad.ml.models import build_model
from simulador_quad.ml.evaluate import evaluate_model, evaluate_outer_force_model


def _resolve_splits(args) -> list[str]:
    if args.splits:
        return [s.strip() for s in args.splits.split(",") if s.strip()]
    splits = ["train", "val", "test"]
    if args.ood_dataset:
        splits.append("ood")
    return splits


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a trained neural controller (supervised imitation metrics)."
    )
    parser.add_argument("--dataset", type=str, required=True, help="Path to in-distribution dataset root (manifest.csv).")
    parser.add_argument("--run", type=str, required=True, help="Path to the training run directory.")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda"], default="auto", help="Device to use.")
    parser.add_argument(
        "--ood-dataset",
        type=str,
        help="OOD dataset root with manifest rows split=ood and compatible telemetry (outer-force targets).",
    )
    parser.add_argument(
        "--splits",
        type=str,
        help="Comma-separated splits to evaluate (default: train,val,test plus ood if --ood-dataset).",
    )

    args = parser.parse_args()

    splits = _resolve_splits(args)
    if "ood" in splits and not args.ood_dataset:
        raise ValueError(
            "Split 'ood' requested but --ood-dataset was not provided. "
            "Pass a separate OOD dataset directory; OOD must not be evaluated as train."
        )

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested, but torch.cuda.is_available() is False")

    config_path = os.path.join(args.run, "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    is_outer = config.get("controller_mode") == "neural_outer_force"
    if not is_outer and (
        config.get("output_dim") == 3 or config.get("target_version") == "desired_force_W_v1"
    ):
        raise ValueError(
            "Ambiguous evaluation mode: config suggests outer-force (output_dim=3 or "
            "target_version=desired_force_W_v1) but controller_mode is not 'neural_outer_force'. "
            "Retrain with tools/train_neural_controller.py or fix config.yaml."
        )

    norm_path = os.path.join(args.run, "normalization.json")
    norm = Normalizer.load(norm_path)

    input_dim = config["input_dim"]
    output_dim = config["output_dim"]
    model = build_model(config["architecture"], input_dim, output_dim, config)

    checkpoint_path = os.path.join(args.run, "checkpoints", f"{config['architecture']}_best.pt")
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))

    results = {}

    for split in splits:
        print(f"Evaluating split: {split}...")

        if split == "ood":
            ds_root = args.ood_dataset
            actual_split = "ood"
        else:
            ds_root = args.dataset
            actual_split = split

        if is_outer:
            ds_cls = OuterForceDataset if config["architecture"] == "mlp" else SequentialOuterForceDataset
            ds = ds_cls(
                ds_root,
                split=actual_split,
                feature_version=config.get("feature_version", "outer_force_min_v1"),
            )
        elif config["architecture"] == "mlp":
            ds = ImitationDataset(ds_root, split=actual_split)
        else:
            ds = SequentialImitationDataset(
                ds_root, split=actual_split, sequence_length=config["sequence_length"]
            )

        if len(ds) == 0:
            if split == "ood":
                raise ValueError(
                    f"Split 'ood' has no loadable samples in {ds_root}. "
                    "Supervised OOD evaluation requires telemetry under manifest result_dir "
                    "(e.g. from generate_outer_force_dataset on OOD scenarios). "
                    "Scenario-only batteries (generate_ood_battery.py) support closed-loop via "
                    "run_neural_outer_force_dataset.py, not evaluate_neural_controller.py."
                )
            print(f"Warning: split {split} has no samples. Skipping.")
            continue

        ds.transform = norm.normalize_x
        ds.target_transform = norm.normalize_y

        loader = DataLoader(ds, batch_size=config.get("batch_size", 64), shuffle=False)

        if is_outer:
            max_t = float(config.get("mass_kg", 1.0)) * 9.81 * 2.5
            max_tilt = float(config.get("max_desired_tilt_rad", 0.52))
            metrics = evaluate_outer_force_model(
                model, loader, norm, device=device, max_thrust=max_t, max_tilt_rad=max_tilt
            )
            filename = f"{split}_force_metrics.json"
        else:
            metrics = evaluate_model(model, loader, norm, device=device)
            filename = f"{split}_metrics.json"
        results[split] = metrics

        metrics_path = os.path.join(args.run, "metrics", filename)
        os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=4)

        print(f"Split {split} MSE: {metrics.get('mse_normalized', 0):.6f}")

    print(f"Evaluation complete. Results saved in {os.path.join(args.run, 'metrics')}")


if __name__ == "__main__":
    main()