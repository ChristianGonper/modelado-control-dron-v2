"""Shared helpers for neural checkpoint trees in tests (not collected as tests)."""
import json
from pathlib import Path

import torch
import yaml

from simulador_quad.ml.models import MLPControllerNet


def make_dummy_outer_force_checkpoint(
    tmp_path: Path,
    output_dim: int = 3,
    controller_mode: str = "neural_outer_force",
    target_names=None,
    feature_version="outer_force_min_v1",
):
    """Create minimal valid (or invalid for rejection) checkpoint tree for tests."""
    model_dir = tmp_path / "outer_model"
    (model_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

    if target_names is None:
        target_names = (
            ["force_x_W_N", "force_y_W_N", "force_z_W_N"]
            if output_dim == 3
            else ["thrust", "mx", "my", "mz"]
        )

    in_dim = 9 if "min" in feature_version else 31
    norm_data = {
        "mean_x": [0.0] * in_dim,
        "std_x": [1.0] * in_dim,
        "mean_y": [0.0] * output_dim,
        "std_y": [1.0] * output_dim,
        "feature_names": ["f"] * in_dim,
        "target_names": target_names,
        "feature_version": feature_version,
        "target_version": "desired_force_W_v1" if output_dim == 3 else "legacy",
        "epsilon": 1e-8,
    }
    with open(model_dir / "normalization.json", "w", encoding="utf-8") as f:
        json.dump(norm_data, f)

    model = MLPControllerNet(in_dim, output_dim, hidden_dim=8)
    for p in model.parameters():
        torch.nn.init.constant_(p, 0.01)
    torch.save(model.state_dict(), model_dir / "checkpoints" / "mlp_best.pt")

    cfg = {
        "architecture": "mlp",
        "input_dim": in_dim,
        "output_dim": output_dim,
        "hidden_dim": 8,
        "controller_mode": controller_mode,
        "feature_version": feature_version,
        "target_version": "desired_force_W_v1" if output_dim == 3 else None,
    }
    with open(model_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    return model_dir