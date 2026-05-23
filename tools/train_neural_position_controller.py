"""
Entrena un controlador neuronal de lazo externo de posicion.

La red predice log-multiplicadores para Kp_pos y Kd_pos. El lazo interno de
actitud queda en el controlador clasico.
"""
import argparse
import os
import yaml
import torch
from torch.utils.data import DataLoader

from simulador_quad.ml.dataset import (
    FEATURE_NAMES,
    FEATURE_VERSION,
    POSITION_GAIN_TARGET_NAMES,
    PositionGainDataset,
    SequentialPositionGainDataset,
)
from simulador_quad.ml.normalization import Normalizer
from simulador_quad.ml.models import build_model
from simulador_quad.ml.train import train_model


def _parse_vector(value: str) -> list[float]:
    return [float(part) for part in value.split(",")]


def main():
    parser = argparse.ArgumentParser(description="Train a neural position-loop gain scheduler.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to classic/PID-bank dataset root.")
    parser.add_argument("--architecture", type=str, choices=["mlp", "gru", "lstm"], default="mlp")
    parser.add_argument("--out", type=str, required=True, help="Output directory for artifacts.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--sequence-length", type=int, default=20)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--base-kp-pos", type=_parse_vector, default=[2.0, 2.0, 5.0])
    parser.add_argument("--base-kd-pos", type=_parse_vector, default=[1.0, 1.0, 2.0])
    parser.add_argument("--multiplier-clip", type=_parse_vector, default=[0.25, 4.0])
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested, but torch.cuda.is_available() is False")

    dataset_cls = PositionGainDataset if args.architecture == "mlp" else SequentialPositionGainDataset
    kwargs = {
        "base_Kp_pos": args.base_kp_pos,
        "base_Kd_pos": args.base_kd_pos,
    }
    if args.architecture != "mlp":
        kwargs["sequence_length"] = args.sequence_length

    train_ds = dataset_cls(args.dataset, split="train", **kwargs)
    val_ds = dataset_cls(args.dataset, split="val", **kwargs)
    if len(train_ds) == 0:
        raise ValueError("No training samples found in dataset.")
    if len(val_ds) == 0:
        raise ValueError("No validation samples found in dataset.")

    norm = Normalizer()
    norm.fit(
        train_ds,
        feature_names=FEATURE_NAMES,
        target_names=POSITION_GAIN_TARGET_NAMES,
        feature_version=f"{FEATURE_VERSION}_position_gain",
    )
    norm.save(os.path.join(args.out, "normalization.json"))

    train_ds.transform = norm.normalize_x
    train_ds.target_transform = norm.normalize_y
    val_ds.transform = norm.normalize_x
    val_ds.target_transform = norm.normalize_y

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)

    input_dim = len(norm.mean_x)
    output_dim = 6
    model = build_model(args.architecture, input_dim, output_dim=output_dim, config={"hidden_dim": args.hidden_dim})

    config = {
        "controller_mode": "neural_position",
        "architecture": args.architecture,
        "input_dim": input_dim,
        "output_dim": output_dim,
        "hidden_dim": args.hidden_dim,
        "sequence_length": args.sequence_length if args.architecture != "mlp" else None,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "patience": args.patience,
        "seed": args.seed,
        "device": device,
        "out_dir": args.out,
        "feature_version": f"{FEATURE_VERSION}_position_gain",
        "base_Kp_pos": args.base_kp_pos,
        "base_Kd_pos": args.base_kd_pos,
        "multiplier_clip": args.multiplier_clip,
    }

    with open(os.path.join(args.out, "config.yaml"), "w") as f:
        yaml.dump(config, f)

    train_model(model, train_loader, val_loader, config)
    print(f"Training complete. Artifacts saved in {args.out}")


if __name__ == "__main__":
    main()
