"""
Tests de integracion para el script de evaluacion neuronal.
"""
import pytest
import os
import json
import yaml
import torch
import pandas as pd
import numpy as np
import sys
import subprocess

@pytest.fixture
def trained_model(tmp_path):
    """Genera un modelo entrenado minimal para evaluacion."""
    ds_path = tmp_path / "mock_ds"
    ds_path.mkdir()
    
    # Manifest
    ep_dir = "ep_0"
    (ds_path / ep_dir).mkdir()
    manifest = pd.DataFrame([
        {"id": 0, "split": "train", "result_dir": ep_dir},
        {"id": 1, "split": "val", "result_dir": ep_dir},
        {"id": 2, "split": "test", "result_dir": ep_dir}
    ])
    manifest.to_csv(ds_path / "manifest.csv", index=False)
    
    # Telemetry
    telemetry = []
    for t in np.linspace(0, 1, 10):
        telemetry.append({
            "time_s": t,
            "state": {"position_W_m": [0,0,0], "velocity_W_m_s": [0,0,0], "orientation_WB": [1,0,0,0], "angular_velocity_B_rad_s": [0,0,0]},
            "reference": {"position_W_m": [0,0,1], "velocity_W_m_s": [0,0,0], "acceleration_W_m_s2": [0,0,0], "yaw_rad": 0.0},
            "control": {"collective_thrust_N": 9.81, "body_moments_Nm": [0,0,0]}
        })
    with open(ds_path / ep_dir / "telemetry.json", "w") as f:
        json.dump(telemetry, f)
        
    out_dir = tmp_path / "model_out"
    train_args = [sys.executable, "tools/train_neural_controller.py", "--dataset", str(ds_path), "--architecture", "mlp", "--out", str(out_dir), "--epochs", "1"]
    subprocess.run(train_args, check=True)
        
    return ds_path, out_dir

def test_eval_script_execution(trained_model):
    """Verifica que el script de evaluacion genera metricas."""
    ds_path, run_dir = trained_model
    
    eval_args = [
        sys.executable, "tools/evaluate_neural_controller.py",
        "--dataset", str(ds_path),
        "--run", str(run_dir)
    ]
    
    result = subprocess.run(eval_args, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with stdout: {result.stdout}\nstderr: {result.stderr}"
        
    # Verificar metricas
    assert (run_dir / "metrics" / "train_metrics.json").exists()
    assert (run_dir / "metrics" / "test_metrics.json").exists()
    
    with open(run_dir / "metrics" / "test_metrics.json", "r") as f:
        m = json.load(f)
        assert "mse_normalized" in m
        assert "mae_thrust_N" in m
