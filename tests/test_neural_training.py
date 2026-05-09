"""
Tests de integracion para el script de entrenamiento neuronal.
"""
import pytest
import os
import shutil
import json
import pandas as pd
import numpy as np
import torch
import sys
import subprocess

@pytest.fixture
def mock_dataset(tmp_path):
    """Crea un mini dataset sintetico para pruebas."""
    ds_path = tmp_path / "mock_ds"
    ds_path.mkdir()
    
    # Manifest
    ep_dir = "ep_0"
    (ds_path / ep_dir).mkdir()
    
    manifest = pd.DataFrame([
        {"id": 0, "split": "train", "result_dir": ep_dir},
        {"id": 1, "split": "val", "result_dir": ep_dir}
    ])
    manifest.to_csv(ds_path / "manifest.csv", index=False)
    
    # Telemetry
    telemetry = []
    for t in np.linspace(0, 1, 50):
        sample = {
            "time_s": t,
            "state": {
                "position_W_m": [0, 0, 0],
                "velocity_W_m_s": [0, 0, 0],
                "orientation_WB": [1, 0, 0, 0],
                "angular_velocity_B_rad_s": [0, 0, 0]
            },
            "reference": {
                "position_W_m": [0, 0, 1],
                "velocity_W_m_s": [0, 0, 0],
                "acceleration_W_m_s2": [0, 0, 0],
                "yaw_rad": 0.0
            },
            "control": {
                "collective_thrust_N": 9.81,
                "body_moments_Nm": [0, 0, 0]
            }
        }
        telemetry.append(sample)
        
    with open(ds_path / ep_dir / "telemetry.json", "w") as f:
        json.dump(telemetry, f)
        
    return ds_path

def test_train_script_execution(mock_dataset, tmp_path):
    """Verifica que el script de entrenamiento se ejecuta y genera artefactos."""
    out_dir = tmp_path / "out"
    
    test_args = [
        sys.executable, "tools/train_neural_controller.py",
        "--dataset", str(mock_dataset),
        "--architecture", "mlp",
        "--out", str(out_dir),
        "--epochs", "2",
        "--batch-size", "16",
        "--hidden-dim", "16"
    ]
    
    result = subprocess.run(test_args, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with stdout: {result.stdout}\nstderr: {result.stderr}"
        
    # Verificar artefactos
    assert (out_dir / "normalization.json").exists()
    assert (out_dir / "config.yaml").exists()
    assert (out_dir / "checkpoints" / "mlp_best.pt").exists()
    assert (out_dir / "metrics" / "train_metrics.json").exists()

def test_train_gru_script_execution(mock_dataset, tmp_path):
    """Verifica que el script de entrenamiento funciona para GRU (Normalizer fix)."""
    out_dir = tmp_path / "out_gru"
    
    test_args = [
        sys.executable, "tools/train_neural_controller.py",
        "--dataset", str(mock_dataset),
        "--architecture", "gru",
        "--out", str(out_dir),
        "--epochs", "2",
        "--batch-size", "16",
        "--hidden-dim", "16",
        "--sequence-length", "10"
    ]
    
    result = subprocess.run(test_args, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with stdout: {result.stdout}\nstderr: {result.stderr}"
    
    assert (out_dir / "checkpoints" / "gru_best.pt").exists()
    assert (out_dir / "normalization.json").exists()
    
    # Verificar que mean_x en normalization.json tiene dimension 31 (no 10)
    with open(out_dir / "normalization.json", "r") as f:
        norm_data = json.load(f)
        assert len(norm_data["mean_x"]) == 31
