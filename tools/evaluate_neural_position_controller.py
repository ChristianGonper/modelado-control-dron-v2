"""
Evaluacion supervisada del controlador neuronal de lazo externo.
"""
import argparse
import json
import os
import yaml
import torch
from torch.utils.data import DataLoader

from simulador_quad.ml.dataset import PositionGainDataset, SequentialPositionGainDataset
from simulador_quad.ml.normalization import Normalizer
from simulador_quad.ml.models import build_model


def evaluate_position_model(model, loader, normalizer, device="cpu"):
    model.eval()
    model.to(device)

    total_mse = 0.0
    preds = []
    targets = []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            y_pred = model(x)
            loss = torch.nn.functional.mse_loss(y_pred, y)
            total_mse += loss.item() * x.size(0)
            preds.append(y_pred.cpu())
            targets.append(y.cpu())

    total_mse /= len(loader.dataset)
    pred_log = normalizer.denormalize_y(torch.cat(preds))
    target_log = normalizer.denormalize_y(torch.cat(targets))
    log_errors = pred_log - target_log
    multiplier_errors = torch.exp(pred_log) - torch.exp(target_log)

    return {
        "mse_normalized": float(total_mse),
        "mae_log_multipliers": torch.abs(log_errors).mean(dim=0).tolist(),
        "rmse_log_multipliers": torch.sqrt((log_errors ** 2).mean(dim=0)).tolist(),
        "mae_multipliers": torch.abs(multiplier_errors).mean(dim=0).tolist(),
        "rmse_multipliers": torch.sqrt((multiplier_errors ** 2).mean(dim=0)).tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate a neural position-loop gain scheduler.")
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--run", type=str, required=True)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    with open(os.path.join(args.run, "config.yaml"), "r") as f:
        config = yaml.safe_load(f)

    norm = Normalizer.load(os.path.join(args.run, "normalization.json"))
    model = build_model(config["architecture"], config["input_dim"], config["output_dim"], config)
    checkpoint = os.path.join(args.run, "checkpoints", f"{config['architecture']}_best.pt")
    model.load_state_dict(torch.load(checkpoint, map_location=args.device))

    dataset_cls = PositionGainDataset if config["architecture"] == "mlp" else SequentialPositionGainDataset
    kwargs = {
        "base_Kp_pos": config.get("base_Kp_pos", [2.0, 2.0, 5.0]),
        "base_Kd_pos": config.get("base_Kd_pos", [1.0, 1.0, 2.0]),
    }
    if config["architecture"] != "mlp":
        kwargs["sequence_length"] = config["sequence_length"]

    os.makedirs(os.path.join(args.run, "metrics"), exist_ok=True)
    for split in ["train", "val", "test"]:
        ds = dataset_cls(args.dataset, split=split, **kwargs)
        if len(ds) == 0:
            print(f"Warning: split {split} has no samples. Skipping.")
            continue
        ds.transform = norm.normalize_x
        ds.target_transform = norm.normalize_y
        loader = DataLoader(ds, batch_size=config.get("batch_size", 64), shuffle=False)
        metrics = evaluate_position_model(model, loader, norm, device=args.device)
        with open(os.path.join(args.run, "metrics", f"{split}_position_metrics.json"), "w") as f:
            json.dump(metrics, f, indent=4)
        print(f"Split {split} MSE: {metrics['mse_normalized']:.6f}")


if __name__ == "__main__":
    main()
