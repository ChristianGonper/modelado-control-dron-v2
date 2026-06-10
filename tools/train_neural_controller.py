"""
Script para entrenar controladores neuronales por imitacion.
"""
import argparse
import os
import yaml
import torch
from torch.utils.data import DataLoader
from simulador_quad.ml.dataset import (
    ImitationDataset, SequentialImitationDataset,
    OuterForceDataset, SequentialOuterForceDataset,
    FEATURE_NAMES, TARGET_NAMES, FEATURE_VERSION,
    OUTER_FORCE_MIN_V1_NAMES, OUTER_FORCE_FULL_V1_NAMES,
    TARGET_FORCE_NAMES, TARGET_FORCE_VERSION,
)
from simulador_quad.ml.normalization import Normalizer
from simulador_quad.ml.models import build_model
from simulador_quad.ml.train import train_model

def main():
    parser = argparse.ArgumentParser(description="Train a neural controller by imitation.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to classic dataset root.")
    parser.add_argument("--architecture", type=str, choices=["mlp", "gru", "lstm"], default="mlp", help="Model architecture.")
    parser.add_argument("--out", type=str, required=True, help="Output directory for artifacts.")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs.")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument("--patience", type=int, default=10, help="Patience for early stopping.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--sequence-length", type=int, default=20, help="Sequence length for recurrent models.")
    parser.add_argument("--hidden-dim", type=int, default=64, help="Hidden dimension size.")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda"], default="auto", help="Training device.")
    parser.add_argument("--feature-version", type=str, default="v1",
                        help="Feature version: 'v1' (legacy 4-out), 'outer_force_min_v1' (9) or 'outer_force_full_v1' (31).")

    args = parser.parse_args()

    # Reproducibilidad
    import random
    import numpy as np
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    # Comentario: El determinismo completo puede depender del dispositivo de hardware y de operaciones CUDA específicas.

    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested, but torch.cuda.is_available() is False")

    os.makedirs(args.out, exist_ok=True)

    is_outer = args.feature_version.startswith("outer_force_")

    # 1. Cargar datasets (train y val) - outer usa observation + target fuerza
    if is_outer:
        ds_cls = OuterForceDataset if args.architecture == "mlp" else SequentialOuterForceDataset
        seq_kw = {"sequence_length": args.sequence_length} if args.architecture != "mlp" else {}
        train_ds = ds_cls(args.dataset, split="train", feature_version=args.feature_version, **seq_kw)
        val_ds = ds_cls(args.dataset, split="val", feature_version=args.feature_version, **seq_kw)
        feat_names = train_ds.feature_names
        targ_names = TARGET_FORCE_NAMES
        out_dim = 3
        ctrl_mode = "neural_outer_force"
        target_ver = TARGET_FORCE_VERSION
    else:
        if args.architecture == "mlp":
            train_ds = ImitationDataset(args.dataset, split="train")
            val_ds = ImitationDataset(args.dataset, split="val")
        else:
            train_ds = SequentialImitationDataset(args.dataset, split="train", sequence_length=args.sequence_length)
            val_ds = SequentialImitationDataset(args.dataset, split="val", sequence_length=args.sequence_length)
        feat_names = FEATURE_NAMES
        targ_names = TARGET_NAMES
        out_dim = 4
        ctrl_mode = "neural_legacy"
        target_ver = FEATURE_VERSION

    if len(train_ds) == 0:
        raise ValueError("No training samples found in dataset.")

    # 2. Normalizacion (solo con train)
    norm = Normalizer()
    norm.fit(train_ds, feature_names=feat_names, target_names=targ_names, feature_version=args.feature_version)
    norm.save(os.path.join(args.out, "normalization.json"))

    # Aplicar normalizacion a los datasets
    train_ds.transform = norm.normalize_x
    train_ds.target_transform = norm.normalize_y
    val_ds.transform = norm.normalize_x
    val_ds.target_transform = norm.normalize_y

    # 3. Loaders
    def seed_worker(worker_id):
        worker_seed = torch.initial_seed() % 2**32
        import numpy as np
        import random
        np.random.seed(worker_seed)
        random.seed(worker_seed)

    g = torch.Generator()
    g.manual_seed(args.seed)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        generator=g,
        worker_init_fn=seed_worker
    )
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)

    # 4. Construir modelo
    input_dim = len(norm.mean_x)
    model = build_model(args.architecture, input_dim, output_dim=out_dim, config={"hidden_dim": args.hidden_dim})

    # 5. Config (incluye campos para outer-force contract)
    config = {
        "architecture": args.architecture,
        "input_dim": input_dim,
        "output_dim": out_dim,
        "hidden_dim": args.hidden_dim,
        "sequence_length": args.sequence_length if args.architecture != "mlp" else None,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "patience": args.patience,
        "seed": args.seed,
        "device": device,
        "out_dir": args.out,
        "feature_version": args.feature_version,
        "target_version": target_ver,
        "controller_mode": ctrl_mode,
    }

    with open(os.path.join(args.out, "config.yaml"), "w") as f:
        yaml.dump(config, f)

    # 6. Entrenar
    train_model(model, train_loader, val_loader, config)

    print(f"Training complete. Artifacts saved in {args.out}")

if __name__ == "__main__":
    main()
