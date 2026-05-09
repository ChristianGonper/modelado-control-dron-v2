"""
Script para entrenar controladores neuronales por imitacion.
"""
import argparse
import os
import yaml
import torch
from torch.utils.data import DataLoader
from simulador_quad.ml.dataset import ImitationDataset, SequentialImitationDataset, FEATURE_NAMES, TARGET_NAMES, FEATURE_VERSION
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
    
    args = parser.parse_args()
    
    # Reproducibilidad
    torch.manual_seed(args.seed)
    
    os.makedirs(args.out, exist_ok=True)
    
    # 1. Cargar datasets (train y val)
    if args.architecture == "mlp":
        train_ds = ImitationDataset(args.dataset, split="train")
        val_ds = ImitationDataset(args.dataset, split="val")
    else:
        train_ds = SequentialImitationDataset(args.dataset, split="train", sequence_length=args.sequence_length)
        val_ds = SequentialImitationDataset(args.dataset, split="val", sequence_length=args.sequence_length)
    
    if len(train_ds) == 0:
        raise ValueError("No training samples found in dataset.")
    
    # 2. Normalizacion (solo con train)
    norm = Normalizer()
    norm.fit(train_ds, feature_names=FEATURE_NAMES, target_names=TARGET_NAMES, feature_version=FEATURE_VERSION)
    norm.save(os.path.join(args.out, "normalization.json"))
    
    # Aplicar normalizacion a los datasets
    train_ds.transform = norm.normalize_x
    train_ds.target_transform = norm.normalize_y
    val_ds.transform = norm.normalize_x
    val_ds.target_transform = norm.normalize_y
    
    # 3. Loaders
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)
    
    # 4. Construir modelo
    input_dim = len(norm.mean_x)
    model = build_model(args.architecture, input_dim, output_dim=4, config={"hidden_dim": args.hidden_dim})
    
    # 5. Config
    config = {
        "architecture": args.architecture,
        "input_dim": input_dim,
        "output_dim": 4,
        "hidden_dim": args.hidden_dim,
        "sequence_length": args.sequence_length if args.architecture != "mlp" else None,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "patience": args.patience,
        "seed": args.seed,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "out_dir": args.out,
        "feature_version": FEATURE_VERSION
    }
    
    with open(os.path.join(args.out, "config.yaml"), "w") as f:
        yaml.dump(config, f)
    
    # 6. Entrenar
    train_model(model, train_loader, val_loader, config)
    
    print(f"Training complete. Artifacts saved in {args.out}")

if __name__ == "__main__":
    main()
