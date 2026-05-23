"""
Script para evaluar controladores neuronales entrenados (modo supervisado).
"""
import argparse
import os
import json
import yaml
import torch
from torch.utils.data import DataLoader
from simulador_quad.ml.dataset import ImitationDataset, SequentialImitationDataset
from simulador_quad.ml.normalization import Normalizer
from simulador_quad.ml.models import build_model
from simulador_quad.ml.evaluate import evaluate_model

def main():
    parser = argparse.ArgumentParser(description="Evaluate a trained neural controller.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to classic dataset root.")
    parser.add_argument("--run", type=str, required=True, help="Path to the training run directory.")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda"], default="auto", help="Device to use.")
    parser.add_argument("--ood-dataset", type=str, help="Optional path to OOD dataset root.")
    
    args = parser.parse_args()
    device = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested, but torch.cuda.is_available() is False")
    
    # 1. Cargar config
    config_path = os.path.join(args.run, "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # 2. Cargar normalizador
    norm_path = os.path.join(args.run, "normalization.json")
    norm = Normalizer.load(norm_path)
    
    # 3. Cargar modelo
    input_dim = config["input_dim"]
    output_dim = config["output_dim"]
    model = build_model(config["architecture"], input_dim, output_dim, config)
    
    checkpoint_path = os.path.join(args.run, "checkpoints", f"{config['architecture']}_best.pt")
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    
    # 4. Evaluar cada split (train, val, test)
    splits = ["train", "val", "test"]
    if args.ood_dataset:
        splits.append("ood")
    
    results = {}
    
    for split in splits:
        print(f"Evaluating split: {split}...")
        
        ds_root = args.dataset if split != "ood" else args.ood_dataset
        # Para OOD, cargamos todo el dataset como un unico split si no hay division explicita
        actual_split = split if split != "ood" else "train"
        
        if config["architecture"] == "mlp":
            ds = ImitationDataset(ds_root, split=actual_split)
        else:
            ds = SequentialImitationDataset(ds_root, split=actual_split, sequence_length=config["sequence_length"])
        
        if len(ds) == 0:
            print(f"Warning: split {split} has no samples. Skipping.")
            continue
        
        # Aplicar normalizacion
        ds.transform = norm.normalize_x
        ds.target_transform = norm.normalize_y
        
        loader = DataLoader(ds, batch_size=config.get("batch_size", 64), shuffle=False)
        
        metrics = evaluate_model(model, loader, norm, device=device)
        results[split] = metrics
        
        # Guardar metricas del split
        filename = f"{split}_metrics.json"
        metrics_path = os.path.join(args.run, "metrics", filename)
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=4)
        
        print(f"Split {split} MSE: {metrics['mse_normalized']:.6f}")

    print(f"Evaluation complete. Results saved in {os.path.join(args.run, 'metrics')}")

if __name__ == "__main__":
    main()
