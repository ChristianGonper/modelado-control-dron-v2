"""OOD split contract for evaluate_neural_controller and OuterForceDataset."""
import json
from pathlib import Path

import pandas as pd
import pytest
import torch
import yaml

from simulador_quad.datasets.classic import INITIAL_PIDS
from simulador_quad.ml.dataset import OuterForceDataset
from simulador_quad.ml.models import MLPControllerNet
from simulador_quad.ml.normalization import Normalizer


def _write_frozen_pid_source(tmp_path: Path) -> Path:
    pid_root = tmp_path / "classic_source"
    pids_dir = pid_root / "pids"
    pids_dir.mkdir(parents=True, exist_ok=True)
    for family, gains in INITIAL_PIDS.items():
        payload = {"pid_id": f"pid_{family}_v1", "family": family, "version": "v1", **gains}
        with open(pids_dir / f"pid_{family}_v1.yaml", "w", encoding="utf-8") as file:
            yaml.dump(payload, file)
    return pid_root


def _write_minimal_outer_force_run(tmp_path: Path, in_dim: int = 9) -> Path:
    run_dir = tmp_path / "run"
    (run_dir / "checkpoints").mkdir(parents=True)
    (run_dir / "metrics").mkdir(parents=True)

    norm = {
        "mean_x": [0.0] * in_dim,
        "std_x": [1.0] * in_dim,
        "mean_y": [0.0, 0.0, 9.81],
        "std_y": [1.0, 1.0, 1.0],
        "feature_names": ["f"] * in_dim,
        "target_names": ["force_x_W_N", "force_y_W_N", "force_z_W_N"],
        "feature_version": "outer_force_min_v1",
        "target_version": "desired_force_W_v1",
        "epsilon": 1e-8,
    }
    with open(run_dir / "normalization.json", "w", encoding="utf-8") as f:
        json.dump(norm, f)

    model = MLPControllerNet(in_dim, 3, hidden_dim=8)
    torch.save(model.state_dict(), run_dir / "checkpoints" / "mlp_best.pt")

    cfg = {
        "architecture": "mlp",
        "input_dim": in_dim,
        "output_dim": 3,
        "hidden_dim": 8,
        "controller_mode": "neural_outer_force",
        "feature_version": "outer_force_min_v1",
        "batch_size": 8,
        "mass_kg": 1.0,
        "max_desired_tilt_rad": 0.52,
    }
    with open(run_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    return run_dir


def _write_ood_dataset(tmp_path: Path) -> Path:
    ds = tmp_path / "ood_ds"
    ep = ds / "results" / "ood_ep"
    ep.mkdir(parents=True)
    sc_dir = ds / "scenarios" / "lemniscate"
    sc_dir.mkdir(parents=True)

    scenario = {
        "controller": {"Kp_pos": [2, 2, 5], "Kd_pos": [1, 1, 2]},
        "vehicle": {"mass_kg": 1.0, "gravity_m_s2": 9.81},
    }
    with open(sc_dir / "ood_ep.yaml", "w", encoding="utf-8") as f:
        yaml.dump(scenario, f)

    telemetry = []
    for t in [0.0, 0.1]:
        telemetry.append(
            {
                "time_s": t,
                "observation": {
                    "position_W_m": [0, 0, 1],
                    "velocity_W_m_s": [0, 0, 0],
                    "orientation_WB": [1, 0, 0, 0],
                    "angular_velocity_B_rad_s": [0, 0, 0],
                },
                "reference": {
                    "position_W_m": [0, 0, 1],
                    "velocity_W_m_s": [0, 0, 0],
                    "acceleration_W_m_s2": [0, 0, 0],
                    "yaw_rad": 0.0,
                },
            }
        )
    with open(ep / "telemetry.json", "w", encoding="utf-8") as f:
        json.dump(telemetry, f)

    pd.DataFrame(
        [
            {
                "scenario_id": "ood_ep",
                "family": "lemniscate",
                "split": "ood",
                "scenario_path": "scenarios/lemniscate/ood_ep.yaml",
                "result_dir": "results/ood_ep",
            }
        ]
    ).to_csv(ds / "manifest.csv", index=False)
    return ds


def test_outer_force_dataset_filters_ood_split(tmp_path):
    ds = _write_ood_dataset(tmp_path)
    ood_ds = OuterForceDataset(str(ds), split="ood")
    train_ds = OuterForceDataset(str(ds), split="train")
    assert len(ood_ds) > 0
    assert len(train_ds) == 0


def test_evaluate_neural_controller_uses_ood_split_not_train(tmp_path):
    import subprocess
    import sys

    run_dir = _write_minimal_outer_force_run(tmp_path)
    ood_ds = _write_ood_dataset(tmp_path)
    id_ds = tmp_path / "id_ds"
    id_ds.mkdir()
    pd.DataFrame(
        [{"scenario_id": "x", "split": "train", "result_dir": "results/x"}]
    ).to_csv(id_ds / "manifest.csv", index=False)

    result = subprocess.run(
        [
            sys.executable,
            "tools/evaluate_neural_controller.py",
            "--dataset",
            str(id_ds),
            "--run",
            str(run_dir),
            "--ood-dataset",
            str(ood_ds),
            "--splits",
            "ood",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (run_dir / "metrics" / "ood_force_metrics.json").exists()
    assert not (run_dir / "metrics" / "train_force_metrics.json").exists()


def test_evaluate_empty_ood_battery_raises(tmp_path):
    """Scenario-only OOD battery must not pass supervised eval silently."""
    import subprocess
    import sys

    run_dir = _write_minimal_outer_force_run(tmp_path)
    pid_root = _write_frozen_pid_source(tmp_path)
    battery = tmp_path / "battery_only"
    subprocess.run(
        [
            sys.executable,
            "tools/generate_ood_battery.py",
            "--out",
            str(battery),
            "--pid-source-dataset",
            str(pid_root),
            "--scenario-id",
            "lemniscate_3d_heavy_wind",
            "--overwrite",
        ],
        check=True,
    )
    id_ds = tmp_path / "id_ds"
    id_ds.mkdir()
    pd.DataFrame([{"scenario_id": "x", "split": "train", "result_dir": "r"}]).to_csv(
        id_ds / "manifest.csv", index=False
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/evaluate_neural_controller.py",
            "--dataset",
            str(id_ds),
            "--run",
            str(run_dir),
            "--ood-dataset",
            str(battery),
            "--splits",
            "ood",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "no loadable samples" in (result.stderr + result.stdout).lower()


def test_evaluate_rejects_ambiguous_outer_force_config(tmp_path):
    """output_dim=3 without controller_mode must fail before dataset load."""
    import subprocess
    import sys

    run_dir = tmp_path / "ambiguous_run"
    (run_dir / "checkpoints").mkdir(parents=True)
    torch.save(
        MLPControllerNet(9, 3, hidden_dim=8).state_dict(),
        run_dir / "checkpoints" / "mlp_best.pt",
    )
    with open(run_dir / "normalization.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "mean_x": [0.0] * 9,
                "std_x": [1.0] * 9,
                "mean_y": [0.0, 0.0, 9.81],
                "std_y": [1.0, 1.0, 1.0],
                "feature_names": ["f"] * 9,
                "target_names": ["force_x_W_N", "force_y_W_N", "force_z_W_N"],
                "epsilon": 1e-8,
            },
            f,
        )
    with open(run_dir / "config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "architecture": "mlp",
                "input_dim": 9,
                "output_dim": 3,
                "hidden_dim": 8,
                "target_version": "desired_force_W_v1",
            },
            f,
        )

    id_ds = tmp_path / "id_ds"
    id_ds.mkdir()
    pd.DataFrame([{"scenario_id": "x", "split": "train", "result_dir": "r"}]).to_csv(
        id_ds / "manifest.csv", index=False
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/evaluate_neural_controller.py",
            "--dataset",
            str(id_ds),
            "--run",
            str(run_dir),
            "--splits",
            "train",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ambiguous evaluation mode" in (result.stderr + result.stdout).lower()


def test_evaluate_requires_ood_dataset_when_ood_split_requested(tmp_path):
    import subprocess
    import sys

    run_dir = _write_minimal_outer_force_run(tmp_path)
    id_ds = tmp_path / "id_ds"
    id_ds.mkdir()
    pd.DataFrame([{"scenario_id": "x", "split": "train", "result_dir": "r"}]).to_csv(
        id_ds / "manifest.csv", index=False
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/evaluate_neural_controller.py",
            "--dataset",
            str(id_ds),
            "--run",
            str(run_dir),
            "--splits",
            "ood",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ood-dataset" in (result.stderr + result.stdout).lower()